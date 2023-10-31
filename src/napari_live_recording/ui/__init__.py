from napari.viewer import Viewer
from qtpy.QtCore import QTimer, Qt, QSize
from qtpy.QtWidgets import (
    QTabWidget,
    QWidget,
    QScrollArea,
    QFrame,
    QVBoxLayout,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from superqt import QCollapsible
from napari_live_recording.common import (
    THIRTY_FPS,
    WriterInfo,
    RecordType,
    FileFormat,
    settings,
    filtersDict,
    createPipelineFilter,
)
from napari_live_recording.control.devices import devicesDict, ICamera
from napari_live_recording.control.devices.interface import NumberParameter
from napari_live_recording.control import MainController
from napari_live_recording.ui.widgets import (
    QFormLayout,
    QGroupBox,
    QPushButton,
    LabeledSlider,
    ComboBox,
    RecordHandling,
    CameraSelection,
    ROIHandling,
)
import numpy as np
import functools
import pims


class ViewerAnchor:
    """Class which handles the UI elements of the plugin."""

    def __init__(self, napari_viewer: Viewer, mainController: MainController) -> None:
        self.viewer = napari_viewer
        self.mainController = mainController
        self.settings = settings
        self.filtersDict = filtersDict
        self.mainLayout = QVBoxLayout()
        self.selectionWidget = CameraSelection()
        self.selectionWidget.setDeviceSelectionWidget(list(devicesDict.keys()))
        self.selectionWidget.setAvailableCameras(list(devicesDict.keys()))
        self.recordingWidget = RecordHandling()
        verticalSpacer = QSpacerItem(0, 1, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.mainLayout.addWidget(self.selectionWidget.group)
        self.mainLayout.addWidget(self.recordingWidget.group)
        self.mainLayout.setAlignment(
            self.selectionWidget.group, Qt.AlignmentFlag.AlignTop
        )
        # if self.settings.value("availableFilters") is not None:
        #     self.filtersDict = self.settings.value("availableFilters")
        # else:
        #     self.filtersDict = {"No Filter": None}
        self.cameraTabsDict = {}
        self.selectionWidget.newCameraRequested.connect(self.addCameraUI)
        self.recordingWidget.signals["snapRequested"].connect(self.snap)
        self.recordingWidget.signals["liveRequested"].connect(self.live)
        self.recordingWidget.signals["recordRequested"].connect(self.record)
        self.recordingWidget.filterCreated.connect(self.refreshAvailableFilters)
        self.recordingWidget.resetFilters.clicked.connect(self.resetFilters)
        self.mainController.recordFinished.connect(
            lambda: self.recordingWidget.record.setChecked(False)
        )
        self.mainController.cameraDeleted.connect(self.recordingWidget.live.setChecked)
        self.liveTimer = QTimer()
        self.liveTimer.timeout.connect(self._updateLiveLayers)
        self.liveTimer.setInterval(THIRTY_FPS)
        self.isFirstTab = True
        self.mainLayout.addItem(verticalSpacer)

    def addTabWidget(self, isFirstTab: bool):
        if isFirstTab:
            self.tabs = QTabWidget()
            self.mainLayout.insertWidget(self.mainLayout.count() - 1, self.tabs)
            self.isFirstTab = False
        else:
            pass

    def addCameraUI(self, interface: str, name: str, idx: int):
        self.addTabWidget(self.isFirstTab)
        camera: ICamera = devicesDict[interface](name, idx)
        cameraKey = f"{camera.name}:{camera.__class__.__name__}:{str(idx)}"

        cameraTab = QWidget()
        cameraTabLayout = QGridLayout()

        settingsLayout = QFormLayout()
        settingsGroup = QGroupBox()

        self.mainController.addCamera(cameraKey, camera)

        roiWidget = ROIHandling(camera.fullShape)
        roiWidget.signals["changeROIRequested"].connect(
            lambda roi: camera.changeROI(roi)
        )
        roiWidget.signals["fullROIRequested"].connect(lambda roi: camera.changeROI(roi))

        # here also change buffer ROI
        filtersCombo = ComboBox(self.filtersDict.keys(), "Filters")
        selectFilter_btn = QPushButton("Select Filter")

        cameraTabLayout.addWidget(filtersCombo.widget, 0, 0)
        cameraTabLayout.addWidget(selectFilter_btn, 0, 1)

        if interface == "MicroManager":
            cameraTabLayout.addWidget(camera.settingsWidget, 1, 0, 1, 2)

        else:
            scrollArea = QScrollArea()
            specificSettingsGroup = QWidget()
            specificSettingsLayout = QFormLayout()
            for name, parameter in camera.parameters.items():
                if len(name) > 15:
                    name = name[:15]
                if type(parameter) == NumberParameter:
                    widget = LabeledSlider(
                        (*parameter.valueLimits, parameter.value), name, parameter.unit
                    )
                    widget.signals["valueChanged"].connect(
                        lambda value, name=name: camera.changeParameter(name, value)
                    )
                else:  # ListParameter
                    widget = ComboBox(parameter.options, name)
                    widget.signals["currentTextChanged"].connect(
                        lambda text, name=name: camera.changeParameter(name, text)
                    )
                specificSettingsLayout.addRow(widget.label, widget.widget)

            specificSettingsGroup.setLayout(specificSettingsLayout)
            scrollArea.setWidget(specificSettingsGroup)
            scrollArea.setWidgetResizable(True)
            scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            cameraTabLayout.addWidget(scrollArea, 1, 0, 1, 2)

        deleteButton = QPushButton("Delete camera")
        deleteButton.clicked.connect(lambda: self.deleteCameraUI(cameraKey))
        settingsLayout.addRow(deleteButton)
        settingsLayout.addRow(roiWidget)
        settingsGroup.setLayout(settingsLayout)
        cameraTabLayout.addWidget(settingsGroup)
        cameraTab.setLayout(cameraTabLayout)

        self.cameraTabsDict[cameraKey] = cameraTabLayout
        self.tabs.addTab(cameraTab, cameraKey)

    def deleteCameraUI(self, cameraKey: str) -> None:
        self.mainController.deleteCamera(cameraKey)
        self.tabs.removeTab(self.tabs.currentIndex())
        if self.tabs.count() == 0:
            self.mainLayout.removeWidget(self.tabs)
            self.tabs.setParent(None)
            self.isFirstTab = True

    def refreshAvailableFilters(self):
        # print(newFilter)
        # self.filtersDict[newFilter[0]] = newFilter[1]
        print(self.filtersDict)
        for key in self.cameraTabsDict.keys():
            widget = self.cameraTabsDict[key].itemAt(0).widget()
            previousIndex = widget.currentIndex()
            widget.clear()
            widget.addItems(self.filtersDict.keys())
            filterDescription = ""
            for key in list(self.filtersDict.values())[-1].keys():
                filterDescription += str(key)
                filterDescription += " "
            indexOfLast = widget.count() - 1
            widget.setItemData(indexOfLast, filterDescription, Qt.ToolTipRole)
            widget.setCurrentIndex(previousIndex)
            self.settings.setValue("availableFilters", self.filtersDict)

    def resetFilters(self):
        for key in self.cameraTabsDict.keys():
            widget = self.cameraTabsDict[key].itemAt(0).widget()
            self.filtersDict = {"No Filter": None}
            self.settings.setValue("availableFilters", self.filtersDict)
            widget.clear()
            widget.addItems(self.filtersDict.keys())

    def record(self, status: bool) -> None:
        if status:
            # todo: add dynamic control
            filtersList = {}
            cameraKeys = list(self.cameraTabsDict.keys())
            for key in cameraKeys:
                widget = self.cameraTabsDict[key].itemAt(0).widget()
                selectedFilter = widget.currentText()
                filtersList[key] = self.filtersDict[selectedFilter]
            print(filtersList, "FiltersList Created before calling process")
            writerInfo = WriterInfo(
                folder=self.recordingWidget.folderTextEdit.text(),
                filename=self.recordingWidget.filenameTextEdit.text(),
                fileFormat=self.recordingWidget.formatComboBox.currentEnum(),
                recordType=self.recordingWidget.recordComboBox.currentEnum(),
                stackSize=self.recordingWidget.recordSize,
                acquisitionTime=self.recordingWidget.recordSize,
            )
            writerInfoProcessed = WriterInfo(
                folder=self.recordingWidget.folderTextEdit.text(),
                filename=self.recordingWidget.filenameTextEdit.text() + "processed",
                fileFormat=self.recordingWidget.formatComboBox.currentEnum(),
                recordType=self.recordingWidget.recordComboBox.currentEnum(),
                stackSize=self.recordingWidget.recordSize,
                acquisitionTime=self.recordingWidget.recordSize,
            )
            self.mainController.process(filtersList, writerInfoProcessed)
            self.mainController.record(cameraKeys, writerInfo)
        else:
            self.mainController.stopRecord()

    def snap(self) -> None:
        for key in self.mainController.deviceControllers.keys():
            self._updateLayer(f"Snap {key}", self.mainController.returnNewestFrame(key))

    def live(self, status: bool) -> None:
        # self.mainController.live(status)
        if status:
            self.liveTimer.start()
        else:
            self.liveTimer.stop()

    def _updateLiveLayers(self):
        # for key, buffer in self.mainController.deviceLiveBuffer.items():
        for key in self.mainController.deviceControllers.keys():
            # this copy may not be truly necessary
            # but it does not impact performance too much
            # so we keep it to avoid possible data corruption
            self._updateLayer(
                f"Live {key}", np.copy(self.mainController.returnNewestFrame(key))
            )

    def _updateLayer(self, layerKey: str, data: np.ndarray) -> None:
        try:
            # layer is recreated in case the image changes type (i.e. grayscale -> RGB and viceversa)
            if data.ndim != self.viewer.layers[layerKey].data.ndim:
                self.viewer.layers.remove(layerKey)
                self.viewer.add_image(data, name=layerKey)
            else:
                self.viewer.layers[layerKey].data = data
        except KeyError:
            # needed in case the layer of that live recording does not exist
            self.viewer.add_image(data, name=layerKey)
