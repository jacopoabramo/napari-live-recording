import os
import numpy as np
import microscope.cameras
from pkgutil import iter_modules
from typing import Union
from qtpy.QtCore import Qt, QObject, Signal, QTimer
from qtpy.QtWidgets import (
    QWidget,
    QLabel,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QStackedWidget,
    QProgressBar,
)
from superqt import QLabeledSlider, QLabeledDoubleSlider, QEnumComboBox
from qtpy.QtWidgets import QFormLayout, QGridLayout, QGroupBox
from abc import ABC, abstractmethod
from dataclasses import replace
from napari_live_recording.common import (
    ROI,
    FileFormat,
    RecordType,
    MMC_DEVICE_MAP,
    settings,
    Settings,
)
from enum import Enum
from napari_live_recording.common import (
    ROI,
    FileFormat,
    RecordType,
    MMC_DEVICE_MAP,
    microscopeDeviceDict,
    baseRecordingFolder,
)
from typing import Dict, List, Tuple
from napari_live_recording.processing_engine_.processing_gui import (
    FilterSelectionWidget,
)


class Timer(QTimer):
    pass


class LocalWidget(ABC):
    def __init__(
        self,
        internalWidget: QWidget,
        name: str,
        unit: str = "",
        orientation: str = "left",
    ) -> None:
        """Common widget constructor.

        Args:
            internalWidget (QWidget): widget to construct the form layout.
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        super().__init__()
        self.__name = name
        self.__unit = unit
        labelStr = (
            self.__name + " (" + self.__unit + ")" if self.__unit != "" else self.__name
        )
        self.label = QLabel(labelStr)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.widget = internalWidget

    @property
    def isEnabled(self) -> bool:
        """Widget is enabled for editing (True) or not (False)."""
        return self.widget.isEnabled()

    @isEnabled.setter
    def isEnabled(self, enable: bool) -> None:
        """Sets widget enabled for editing (True) or not (False)."""
        self.widget.setEnabled(enable)

    @abstractmethod
    def changeWidgetSettings(self, newParam) -> None:
        """Common widget update parameter abstract method."""
        pass

    @property
    @abstractmethod
    def value(self) -> None:
        """Widget current value."""
        pass

    @value.setter
    @abstractmethod
    def value(self, value: Union[str, int, float]) -> None:
        """Widget value setter."""
        pass

    @property
    @abstractmethod
    def signals(self) -> Dict[str, Signal]:
        """Common widget method to expose signals to the device."""
        pass


class ComboBox(LocalWidget):
    def __init__(
        self, param: List[str], name: str, unit: str = "", orientation: str = "left"
    ) -> None:
        """ComboBox widget.

        Args:
            param (List[str]): List of parameters added to the ComboBox.
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        self.combobox = QComboBox()
        self.combobox.addItems([str(item) for item in param])
        super().__init__(self.combobox, name, unit, orientation)

    def changeWidgetSettings(self, newParam: List[str]) -> None:
        """ComboBox update widget parameter method. Old List of items is deleted.

        Args:
            newParam (List[str]): new List of parameters to add to the ComboBox.
        """
        self.combobox.clear()
        self.combobox.addItems(newParam)

    @property
    def value(self) -> Tuple[str, int]:
        """Returns a Tuple containing the ComboBox current text and index."""
        return (self.combobox.currentText(), self.combobox.currentIndex())

    @value.setter
    def value(self, value: int) -> None:
        """Sets the ComboBox current showed value (based on elements indeces).

        Args:
            value (int): index of value to show on the ComboBox.
        """
        self.combobox.setCurrentIndex(value)

    @property
    def signals(self) -> Dict[str, Signal]:
        """Returns a dictionary of signals available for the ComboBox widget.
        Exposed signals are:

        - currentIndexChanged,
        - currentTextChanged

        Returns:
            Dict: Dict of signals (key: function name, value: function objects).
        """
        return {
            "currentIndexChanged": self.combobox.currentIndexChanged,
            "currentTextChanged": self.combobox.currentTextChanged,
        }


class LabeledSlider(LocalWidget):
    def __init__(
        self,
        param: Union[Tuple[int, int, int], Tuple[float, float, float]],
        name: str,
        unit: str = "",
        orientation: str = "left",
    ) -> None:
        """Slider widget.

        Args:
            param (Tuple[int, int, int])): parameters for spinbox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        if any(isinstance(parameter, float) for parameter in param):
            self.__slider = QLabeledDoubleSlider(Qt.Horizontal)
        else:
            self.__slider = QLabeledSlider(Qt.Horizontal)
        self.__slider.setRange(param[0], param[1])
        self.__slider.setValue(param[2])
        super().__init__(self.__slider, name, unit, orientation)

    def changeWidgetSettings(self, newParam: Tuple[int, int, int]) -> None:
        """Slider update widget parameter method.

        Args:
            newParam (Tuple[int, int, int]): new parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
        """
        self.__slider.setRange(newParam[0], newParam[1])
        self.__slider.setValue(newParam[2])

    @property
    def value(self) -> int:
        """Returns the Slider current value."""
        return self.__slider.value()

    @value.setter
    def value(self, value: int) -> None:
        """Sets the DoubleSpinBox current value to show on the widget.

        Args:
            value (float): value to set.
        """
        self.__slider.setValue(value)

    @property
    def signals(self) -> Dict[str, Signal]:
        """Returns a dictionary of signals available for the SpinBox widget.
        Exposed signals are:

        - valueChanged

        Returns:
            Dict: Dict of signals (key: function name, value: function objects).
        """
        return {"valueChanged": self.__slider.valueChanged}


class LineEdit(LocalWidget):
    def __init__(
        self, param: str, name: str, unit: str = "", orientation: str = "left"
    ) -> None:
        """LineEdit widget.

        Args:
            param (str): line edit contents
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
            editable (bool, optional): sets the LineEdit to be editable. Defaults to False.
        """
        self.__lineEdit = QLineEdit(param)
        super().__init__(self.__lineEdit, name, unit, orientation)

    def changeWidgetSettings(self, newParam: str) -> None:
        """Updates LineEdit text contents.

        Args:
            newParam (str): new string for LineEdit.
        """
        self.__lineEdit.setText(newParam)

    @property
    def value(self) -> str:
        """Returns the LineEdit current text."""
        return self.__lineEdit.text()

    @value.setter
    def value(self, value: str) -> None:
        """Sets the LineEdit current text to show on the widget.

        Args:
            value (str): string to set.
        """
        self.__lineEdit.setText(value)

    @property
    def signals(self) -> Dict[str, Signal]:
        """Returns a dictionary of signals available for the LineEdit widget.
        Exposed signals are:

        - textChanged,
        - textEdited

        Returns:
            Dict: Dict of signals (key: function name, value: function objects).
        """
        return {
            "textChanged": self.__lineEdit.textChanged,
            "textEdited": self.__lineEdit.textEdited,
        }


class CameraSelection(QObject):
    newCameraRequested = Signal(str, str, str)

    def __init__(self) -> None:
        """Camera selection widget. It includes the following widgets:

        - a ComboBox for camera selection based on strings to identify each camera type;
        - a LineEdit for camera ID or serial number input
        - a QPushButton to add the camera

        Widget grid layout:
        |(0,0-1) ComboBox                |(0,2) QPushButton|
        |(1,0) LineEdit|Line Edit(1,1)   |(1,2)            |

        The QPushButton remains disabled as long as no camera is selected (first index is highlited).
        """
        super(CameraSelection, self).__init__()
        self.group = QGroupBox()
        self.layout = QFormLayout()
        self.stackedWidget = QStackedWidget()
        self.camerasComboBox = ComboBox([], "Interface")
        self.nameLineEdit = LineEdit(param="MyCamera", name="Camera name")
        self.idLineEdit = LineEdit(param="0", name="Camera ID/SN", orientation="right")
        self.adapterComboBox = ComboBox(
            list(MMC_DEVICE_MAP.keys()), name="Adapter", orientation="right"
        )
        self.deviceComboBox = ComboBox([], name="Device", orientation="right")

        modules = [
            module
            for _, module, _ in iter_modules(microscope.cameras.__path__)
            if "_" not in module
        ]
        modules.append("simulators")

        self.microscopeModuleComboBox = ComboBox(
            modules, name="Module", orientation="right"
        )
        self.microscopeDeviceComboBox = ComboBox([], name="Device", orientation="right")
        self.addButton = QPushButton("Add camera")

        self.camerasComboBox.signals["currentIndexChanged"].connect(self.changeWidget)
        self.adapterComboBox.signals["currentIndexChanged"].connect(
            self.updateDeviceSelectionUI
        )

        self.microscopeModuleComboBox.signals["currentTextChanged"].connect(
            self.updateMicroscopeDeviceSelectionUI
        )

        self.camerasComboBox.signals["currentIndexChanged"].connect(self._setAddEnabled)
        self.addButton.clicked.connect(self.requestNewCamera)

    def requestNewCamera(self):
        interface = self.camerasComboBox.value[0]
        label = self.nameLineEdit.value
        module = ""
        device = ""
        if interface in ["MicroManager", "Microscope"]:
            if interface == "MicroManager":
                module = self.adapterComboBox.value[0]
                device = self.deviceComboBox.value[0]
            elif interface == "Microscope":
                module = self.microscopeModuleComboBox.value[0]
                device = self.microscopeDeviceComboBox.value[0]
            else:
                raise TypeError()
            self.newCameraRequested.emit(interface, label, module + " " + device)
        else:
            self.newCameraRequested.emit(interface, label, self.idLineEdit.value)
        self.camerasComboBox.signals["currentIndexChanged"].connect(self._setAddEnabled)

    def setAvailableCameras(self, cameras: List[str]) -> None:
        """Sets the ComboBox with the List of available camera devices.

        Args:
            cameras (List[str]): List of available camera devices.
        """
        # we need to extend the List of available cameras with a selection text
        cameras.insert(0, "Select device")
        self.camerasComboBox.changeWidgetSettings(cameras)
        self.camerasComboBox.isEnabled = True

    def setDeviceSelectionWidget(self, cameras: List[str]) -> None:
        cameras.insert(0, "Select device")
        self.stackWidgets = {}
        self.stackLayouts = {}
        for camera in cameras:
            self.stackWidgets[camera] = QWidget()
            self.stackLayouts[camera] = QFormLayout()
            if camera == "MicroManager":
                self.stackLayouts[camera].addRow(
                    self.adapterComboBox.label, self.adapterComboBox.widget
                )
                self.stackLayouts[camera].addRow(
                    self.deviceComboBox.label, self.deviceComboBox.widget
                )

            elif camera == "Microscope":
                self.stackLayouts[camera].addRow(
                    self.microscopeModuleComboBox.label,
                    self.microscopeModuleComboBox.widget,
                )
                self.stackLayouts[camera].addRow(
                    self.microscopeDeviceComboBox.label,
                    self.microscopeDeviceComboBox.widget,
                )
            else:
                self.stackLayouts[camera].addRow(
                    self.idLineEdit.label, self.idLineEdit.widget
                )

            self.stackWidgets[camera].setLayout(self.stackLayouts[camera])
            self.stackedWidget.addWidget(self.stackWidgets[camera])

        self.layout.addRow(self.camerasComboBox.label, self.camerasComboBox.widget)
        self.layout.addRow(self.nameLineEdit.label, self.nameLineEdit.widget)
        self.layout.addRow(self.stackedWidget)
        self.layout.addRow(self.addButton)

        self.group.setLayout(self.layout)
        self.group.setFlat(True)

    def changeWidget(self, idx):
        self.stackedWidget.setCurrentIndex(idx)

    def updateDeviceSelectionUI(self, idx):
        self.deviceComboBox.changeWidgetSettings(
            MMC_DEVICE_MAP[list(MMC_DEVICE_MAP.keys())[idx]]
        )

    def updateMicroscopeDeviceSelectionUI(self, key):
        self.microscopeDeviceComboBox.changeWidgetSettings([microscopeDeviceDict[key]])

    def _setAddEnabled(self, idx: int):
        """Private method serving as an enable/disable mechanism for the Add button widget.
        This is done to avoid the first index, the "Select device" string, to be considered
        as a valid camera device (which is not).
        """
        self.addButton.setEnabled(idx > 0)


class RecordHandling(QObject):
    recordRequested = Signal(int)
    filterCreated = Signal()

    def __init__(self) -> None:
        """Recording Handling widget. Includes QPushButtons which allow to handle the following operations:

        - live viewing;
        - recording to output file;
        - single frame snap;

        Widget layout:
        |(0,1-2)   QComboBox (File Format)               |(0,2)   QLabel   |
        |(1,0-1)   QLineEdit (Folder selection)          |(1,2) QPushButton|
        |(2,0-2)   QLineEdit (Record filename)           |(2,2)   QLabel   |
        |(3,0-2)   QSpinBox (Record size)                |(3,2)   QLabel   |
        |(4,0-2)                  QPushButton (Snap)                       |
        |(5,0-2)                  QPushButton (Live)                       |
        |(6,0-2)                  QPushButton (Record)                     |

        """
        QObject.__init__(self)
        self.settings = Settings()
        self.group = QGroupBox()
        self.layout = QGridLayout()

        self.formatLabel = QLabel("File format")
        self.formatComboBox = QEnumComboBox(enum_class=FileFormat)
        self.formatLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.folderTextEdit = QLineEdit(baseRecordingFolder)
        self.folderTextEdit.setReadOnly(True)
        self.folderButton = QPushButton("Select record folder")

        self.filenameTextEdit = QLineEdit("Filename")
        self.filenameLabel = QLabel("Record filename")
        self.filenameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.recordComboBox = QEnumComboBox(enum_class=RecordType)

        self.recordSpinBox = QSpinBox()
        self.recordSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recordSpinBox.setRange(1, np.iinfo(np.uint16).max)
        self.recordSpinBox.setValue(100)

        self.snap = QPushButton("Snap")
        self.live = QPushButton("Live")
        self.record = QPushButton("Record")
        self.createFilter = QPushButton("Create Filter")

        self.live.setCheckable(True)
        self.record.setCheckable(True)

        self.recordSpinBox = QSpinBox()
        self.recordSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.recordProgress = QProgressBar()

        # TODO: this is currently hardcoded
        # maybe should find a way to initialize
        # from outside the instance?
        self.recordSpinBox.setRange(1, 5000)
        self.recordSpinBox.setValue(100)
        self.record.setCheckable(True)

        self.layout.addWidget(self.formatComboBox, 0, 0, 1, 2)
        self.layout.addWidget(self.formatLabel, 0, 2)
        self.layout.addWidget(self.folderTextEdit, 1, 0, 1, 2)
        self.layout.addWidget(self.folderButton, 1, 2)
        self.layout.addWidget(self.filenameTextEdit, 2, 0, 1, 2)
        self.layout.addWidget(self.filenameLabel, 2, 2)
        self.layout.addWidget(self.recordSpinBox, 3, 0, 1, 2)
        self.layout.addWidget(self.recordComboBox, 3, 2)
        self.layout.addWidget(self.snap, 4, 0, 1, 3)
        self.layout.addWidget(self.live, 5, 0, 1, 3)
        self.layout.addWidget(self.record, 6, 0, 1, 3)
        self.layout.addWidget(self.recordProgress, 8, 0, 1, 3)
        self.layout.addWidget(self.createFilter, 7, 0, 1, 3)
        self.group.setLayout(self.layout)
        self.group.setFlat(True)

        # progress bar is hidden until recording is started
        self.recordProgress.hide()

        self.live.toggled.connect(self.handleLiveToggled)
        self.record.toggled.connect(self.handleRecordToggled)
        self.createFilter.clicked.connect(self.openFilterCreationWindow)

        self.folderButton.clicked.connect(self.handleFolderSelection)
        self.recordComboBox.currentEnumChanged.connect(self.handleRecordTypeChanged)

    def openFilterCreationWindow(self) -> None:
        global getFilter

        def getFilter():
            self.filterCreated.emit()

        self.selectionWindow = FilterSelectionWidget()
        self.selectionWindow.show()
        self.selectionWindow.filterAdded.connect(getFilter)

    def handleFolderSelection(self) -> None:
        """Handles the selection of the output folder for the recording."""
        folder = QFileDialog.getExistingDirectory(
            self.group, "Select output folder", self.folderTextEdit.text()
        )
        if folder:
            self.folderTextEdit.setText(folder)
            self.settings.setSetting("recordFolder", folder)

    def handleRecordTypeChanged(self, recordType: RecordType) -> None:
        """Handles the change of the record type.

        Args:
            recordType (RecordType): new record type.
        """
        if recordType == RecordType["Toggled"]:
            self.recordSpinBox.setEnabled(False)
            self.recordSpinBox.hide()
        else:
            self.recordSpinBox.show()
            self.recordSpinBox.setEnabled(True)
            if recordType == RecordType["Number of frames"]:
                newVal = 100
            elif recordType == RecordType["Time (seconds)"]:
                newVal = 1
            self.recordSpinBox.setValue(newVal)

    def setWidgetsEnabling(self, isEnabled: bool) -> None:
        """Enables/Disables all record handling widgets."""
        self.snap.setEnabled(isEnabled)
        self.live.setEnabled(isEnabled)
        self.record.setEnabled(isEnabled)
        self.recordSpinBox.setEnabled(isEnabled)

    def handleLiveToggled(self, status: bool) -> None:
        """Enables/Disables pushbuttons when the live button is toggled.

        Args:
            status (bool): new live button status.
        """
        self.snap.setEnabled(not status)
        self.record.setEnabled(not status)

    def handleRecordToggled(self, status: bool) -> None:
        """Enables/Disables pushbuttons when the record button is toggled.

        Args:
            status (bool): new live button status.
        """
        self.snap.setEnabled(not status)
        self.live.setEnabled(not status)
        self.recordSpinBox.setEnabled(not status)
        if status:
            self.recordProgress.show()
        else:
            self.recordProgress.hide()

    @property
    def recordSize(self) -> int:
        """Returns the record size currently indicated in the QSpinBox widget."""
        return self.recordSpinBox.value()

    @property
    def signals(self) -> Dict[str, Signal]:
        """Returns a dictionary of signals available for the RecordHandling widget.
        Exposed signals are:

        - snapRequested,
        - albumRequested,
        - liveRequested,
        - recordRequested

        Returns:
            Dict: Dict of signals (key: function name, value: function objects).
        """
        return {
            "snapRequested": self.snap.clicked,
            "liveRequested": self.live.toggled,
            "recordRequested": self.record.toggled,
        }


class ROIHandling(QWidget):
    changeROIRequested = Signal(ROI)
    fullROIRequested = Signal(ROI)

    def __init__(self, sensorShape: ROI) -> None:
        """ROI Handling widget. Defines a set of non-custom widgets to set the Region Of Interest of the device.
        This widget is common for all devices.
        """
        QWidget.__init__(self)

        self.sensorFullROI = replace(sensorShape)

        self.offsetXLabel = QLabel("Offset X (px)")
        self.offsetXLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.offsetXSpinBox = QSpinBox()
        self.offsetXSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.offsetXSpinBox.setRange(0, self.sensorFullROI.width)
        self.offsetXSpinBox.setSingleStep(self.sensorFullROI.ofs_x_step)
        self.offsetXSpinBox.setValue(0)

        self.offsetYLabel = QLabel(
            "Offset Y (px)",
        )
        self.offsetYLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.offsetYSpinBox = QSpinBox()
        self.offsetYSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.offsetYSpinBox.setRange(0, self.sensorFullROI.height)
        self.offsetYSpinBox.setSingleStep(self.sensorFullROI.ofs_y_step)
        self.offsetYSpinBox.setValue(0)

        self.widthLabel = QLabel("Width (px)")
        self.widthLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.widthSpinBox = QSpinBox()
        self.widthSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.widthSpinBox.setRange(0, self.sensorFullROI.width)
        self.widthSpinBox.setSingleStep(self.sensorFullROI.width_step)
        self.widthSpinBox.setValue(self.sensorFullROI.width)

        self.heightLabel = QLabel("Height (px)")
        self.heightLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.heightSpinBox = QSpinBox()
        self.heightSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.heightSpinBox.setRange(0, self.sensorFullROI.height)
        self.heightSpinBox.setSingleStep(self.sensorFullROI.height_step)
        self.heightSpinBox.setValue(self.sensorFullROI.height)

        self.changeROIButton = QPushButton("Set ROI")
        self.fullROIButton = QPushButton("Full frame")

        layout = QGridLayout()
        layout.addWidget(self.offsetXLabel, 0, 0)
        layout.addWidget(self.offsetXSpinBox, 0, 1)
        layout.addWidget(self.offsetYSpinBox, 0, 2)
        layout.addWidget(self.offsetYLabel, 0, 3)

        layout.addWidget(self.widthLabel, 1, 0)
        layout.addWidget(self.widthSpinBox, 1, 1)
        layout.addWidget(self.heightSpinBox, 1, 2)
        layout.addWidget(self.heightLabel, 1, 3)
        layout.addWidget(self.changeROIButton, 2, 0, 1, 2)
        layout.addWidget(self.fullROIButton, 2, 2, 1, 2)

        # "clicked" signals are connected to private slots.
        # These slots expose the signals available to the user
        # to process the new ROI information if necessary.
        self.changeROIButton.clicked.connect(self._onROIChanged)
        self.fullROIButton.clicked.connect(self._onFullROI)

        self.setLayout(layout)

    def changeWidgetSettings(self, settings: ROI):
        """ROI handling update widget settings method.
        This method is useful whenever the ROI values are changed based
        on some device requirements and adapted.

        Args:
            settings (ROI): new ROI settings to change the widget values and steps.
        """
        self.offsetXSpinBox.setSingleStep(settings.ofs_x_step)
        self.offsetXSpinBox.setValue(settings.offset_x)

        self.offsetYSpinBox.setSingleStep(settings.ofs_y_step)
        self.offsetYSpinBox.setValue(settings.offset_y)

        self.widthSpinBox.setSingleStep(settings.width_step)
        self.widthSpinBox.setValue(settings.width)

        self.heightSpinBox.setSingleStep(settings.height_step)
        self.heightSpinBox.setValue(settings.height)

    def _onROIChanged(self) -> None:
        """Private slot for ROI changed button pressed. Exposes a signal with the updated ROI settings."""
        # read the current SpinBoxes status
        newRoi = ROI(
            offset_x=self.offsetXSpinBox.value(),
            ofs_x_step=self.offsetXSpinBox.singleStep(),
            offset_y=self.offsetYSpinBox.value(),
            ofs_y_step=self.offsetXSpinBox.singleStep(),
            width=self.widthSpinBox.value(),
            width_step=self.widthSpinBox.singleStep(),
            height=self.heightSpinBox.value(),
            height_step=self.heightSpinBox.singleStep(),
        )
        self.changeROIRequested.emit(newRoi)

    def _onFullROI(self) -> None:
        """Private slot for full ROI button pressed. Exposes a signal with the full ROI settings.
        It also returns the widget settings to their original value.
        """
        self.changeWidgetSettings(self.sensorFullROI)
        self.fullROIRequested.emit(replace(self.sensorFullROI))

    @property
    def signals(self) -> Dict[str, Signal]:
        """Returns a dictionary of signals available for the ROIHandling widget.
        Exposed signals are:

        - changeROIRequested,
        - fullROIRequested,

        Returns:
            Dict: Dict of signals (key: function name, value: function objects).
        """
        return {
            "changeROIRequested": self.changeROIRequested,
            "fullROIRequested": self.fullROIRequested,
        }
