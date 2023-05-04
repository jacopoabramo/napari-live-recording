from napari.viewer import Viewer
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QFileDialog 
from superqt import QCollapsible
from napari_live_recording.common import (
    THIRTY_FPS,
    WriterInfo,
    RecordType,
    FileFormat
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
    ROIHandling
)

import numpy as np
import os

class ViewerAnchor:
    """Class which handles the UI elements of the plugin.
    """

    def __init__(self, napari_viewer : Viewer, mainController: MainController) -> None:
        self.viewer = napari_viewer
        
        self.mainController = mainController
        self.mainLayout = QFormLayout()
        self.selectionWidget = CameraSelection()
        self.selectionWidget.setAvailableCameras(list(devicesDict.keys()))
        self.recordingWidget = RecordHandling()
        
        self.mainLayout.addRow(self.selectionWidget.group)
        self.mainLayout.addRow(self.recordingWidget.group)

        self.cameraWidgetGroups = {}
        self.selectionWidget.newCameraRequested.connect(self.addCameraUI)
        self.recordingWidget.signals["snapRequested"].connect(self.snap)
        self.recordingWidget.signals["liveRequested"].connect(self.live)
        self.recordingWidget.signals["recordRequested"].connect(self.record)
        self.mainController.recordFinished.connect(lambda: self.recordingWidget.record.setChecked(False))

        self.liveTimer = QTimer()
        self.liveTimer.timeout.connect(self._updateLiveLayers)
        self.liveTimer.setInterval(THIRTY_FPS)
    
    def addCameraUI(self, interface: str, name: str, idx: int):

        camera : ICamera = devicesDict[interface](name, idx)
        cameraKey = f"{camera.name}:{camera.__class__.__name__}:{str(idx)}"

        cameraCollapsible = QCollapsible(cameraKey)
        cameraCollapsible.setDuration(100)

        settingsLayout = QFormLayout()
        settingsGroup = QGroupBox("Settings")

        self.mainController.addCamera(cameraKey, camera)
        
        roiWidget = ROIHandling(camera.fullShape)
        roiWidget.signals["changeROIRequested"].connect(lambda roi: camera.changeROI(roi))
        roiWidget.signals["fullROIRequested"].connect(lambda roi: camera.changeROI(roi))
        for name, parameter in camera.parameters.items():
            if type(parameter) == NumberParameter:
                widget = LabeledSlider((*parameter.valueLimits, parameter.value), name, parameter.unit)
                widget.signals["valueChanged"].connect(lambda value, name=name: camera.changeParameter(name, value))
            else: # ListParameter
                widget = ComboBox(parameter.options, name)
                widget.signals["currentTextChanged"].connect(lambda text, name=name: camera.changeParameter(name, text))
            settingsLayout.addRow(widget.label, widget.widget)
        deleteButton = QPushButton("Delete camera")
        deleteButton.clicked.connect(lambda: self.deleteCameraUI(cameraKey))
        settingsLayout.addRow(deleteButton)
        settingsLayout.addRow(roiWidget)
        settingsGroup.setLayout(settingsLayout)

        cameraCollapsible.addWidget(settingsGroup)
        cameraCollapsible.expand(True)

        self.cameraWidgetGroups[cameraKey] = cameraCollapsible
        self.mainLayout.addRow(cameraCollapsible)

    def deleteCameraUI(self, cameraKey: str) -> None:
        self.mainController.deleteCamera(cameraKey)
        self.mainLayout.removeRow(self.cameraWidgetGroups[cameraKey])
    
    def record(self, status: bool) -> None:
        if status:
            # todo: add dynamic control
            cameraKeys = list(self.cameraWidgetGroups.keys())            
            writerInfo = WriterInfo(
                folder=self.recordingWidget.folderTextEdit.text(),
                filename=self.recordingWidget.filenameTextEdit.text(),
                fileFormat=self.recordingWidget.formatComboBox.currentEnum(),
                recordType=self.recordingWidget.recordComboBox.currentEnum(),
                stackSize=self.recordingWidget.recordSize,
                acquisitionTime=self.recordingWidget.recordSize
            )
            self.mainController.record(cameraKeys, writerInfo)
        else:
            self.mainController.stopRecord()
    
    def snap(self) -> None:
        for key in self.mainController.deviceControllers.keys():
            self._updateLayer(f"Snap {key}", self.mainController.snap(key))
    
    def live(self, status: bool) -> None:
        self.mainController.live(status)
        if status:
            self.liveTimer.start()
        else:
            self.liveTimer.stop()
    
    def _updateLiveLayers(self):
        for key, buffer in self.mainController.deviceLiveBuffer.items():
            # this copy may not be truly necessary
            # but it does not impact performance too much
            # so we keep it to avoid possible data corruption
            self._updateLayer(f"Live {key}", np.copy(buffer))
    

    def _updateLayer(self, layerKey: str, data: np.ndarray) -> None:
        try:
            # layer is recreated in case the image changes type (i.e. grayscale -> RGB and viceversa)
            if data.ndim != self.viewer.layers[layerKey].data.ndim:
                self.viewer.layers.remove(layerKey)
                self.viewer.add_image(data, name = layerKey)
            else:
                self.viewer.layers[layerKey].data = data
        except KeyError:
            # needed in case the layer of that live recording does not exist
            self.viewer.add_image(data, name = layerKey)