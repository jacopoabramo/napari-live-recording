from typing import Union
from qtpy.QtCore import Qt, QObject, pyqtSignal, QTimer
from qtpy.QtWidgets import (
    QWidget, 
    QLabel, 
    QComboBox, 
    QSpinBox, 
    QDoubleSpinBox, 
    QLineEdit, 
    QPushButton
)
from superqt import QLabeledSlider
from qtpy.QtWidgets import QFormLayout, QGridLayout, QGroupBox
from abc import ABC, abstractmethod
from dataclasses import replace
from napari_live_recording.common import ROI
from enum import Enum

class Timer(QTimer):
    pass

class WidgetEnum(Enum):
    ComboBox = 0,
    SpinBox = 1,
    DoubleSpinBox = 2,
    LabeledSlider = 3,
    LineEdit = 4

class LocalWidget(ABC):
    def __init__(self, internalWidget : QWidget, name: str, unit: str = "", orientation: str = "left") -> None:
        """Common widget constructor.

        Args:
            internalWidget (QWidget): widget to construct the form layout.
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        self.__name = name
        self.__unit = unit
        labelStr = (self.__name + " (" + self.__unit + ")" if self.__unit != "" else self.__name)
        self.label = QLabel(labelStr)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.widget = internalWidget
    
    @property
    def isEnabled(self) -> bool:
        """Widget is enabled for editing (True) or not (False).
        """
        return self.widget.isEnabled()
    
    @isEnabled.setter
    def isEnabled(self, enable : bool) -> None:
        """Sets widget enabled for editing (True) or not (False).
        """
        self.widget.setEnabled(enable)

    @abstractmethod
    def changeWidgetSettings(self, newParam) -> None:
        """Common widget update parameter abstract method.
        """
        pass

    @property
    @abstractmethod
    def value(self) -> None:
        """Widget current value.
        """
        pass

    @value.setter
    @abstractmethod
    def value(self, value: Union[str, int, float]) -> None:
        """Widget value setter.
        """
        pass
    
    @property
    @abstractmethod
    def signals(self) -> dict[str, pyqtSignal]:
        """Common widget method to expose signals to the device.
        """
        pass

class ComboBox(LocalWidget):
    def __init__(self, param : list[str], name : str, unit : str = "", orientation: str = "left") -> None:
        """ComboBox widget.

        Args:
            param (list[str]): list of parameters added to the ComboBox.
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        self.combobox = QComboBox()
        self.combobox.addItems(param)
        super().__init__(self.combobox, name, unit, orientation)
    
    def changeWidgetSettings(self, newParam: list[str]) -> None:
        """ComboBox update widget parameter method. Old list of items is deleted.

        Args:
            newParam (list[str]): new list of parameters to add to the ComboBox.
        """
        self.combobox.clear()
        self.combobox.addItems(newParam)
    
    @property
    def value(self) -> tuple[str, int]:
        """Returns a tuple containing the ComboBox current text and index.
        """
        return (self.combobox.currentText(), self.combobox.currentIndex())
    
    @value.setter
    def value(self, value: int) -> None:
        """Sets the ComboBox current showed value (based on elements indeces).

        Args:
            value (int): index of value to show on the ComboBox.
        """
        self.combobox.setCurrentIndex(value)
    
    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the ComboBox widget.
        Exposed signals are:
        
        - currentIndexChanged,
        - currentTextChanged

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "currentIndexChanged" : self.combobox.currentIndexChanged,
            "currentTextChanged" : self.combobox.currentTextChanged
        }
        

class SpinBox(LocalWidget):
    def __init__(self, param: tuple[int, int, int], name: str, unit: str = "", orientation: str = "left") -> None:
        """SpinBox widget.

        Args:
            param (tuple[int, int, int]): parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        self.spinbox = QSpinBox()
        self.spinbox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinbox.setRange(param[0], param[1])
        self.spinbox.setValue(param[2])
        super().__init__(self.spinbox, name, unit, orientation)
    
    def changeWidgetSettings(self, newParam : tuple[int, int, int]) -> None:
        """SpinBox update widget parameter method.

        Args:
            newParam (tuple(int, int, int)): new parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
        """
        self.spinbox.setRange(newParam[0], newParam[1])
        self.spinbox.setValue(newParam[2])
    
    @property
    def value(self) -> int:
        """Returns the SpinBox current value.
        """
        return self.spinbox.value()
    
    @value.setter
    def value(self, value: int) -> None:
        """Sets the SpinBox current value to show on the widget.

        Args:
            value (int): value to set.
        """
        self.spinbox.setValue(value)
    
    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the SpinBox widget.
        Exposed signals are:
        
        - valueChanged,
        - textChanged

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "valueChanged" : self.spinbox.valueChanged,
            "textChanged" : self.spinbox.textChanged
        }

class DoubleSpinBox(LocalWidget):
    def __init__(self, param: tuple[float, float, float], name: str, unit: str = "", orientation: str = "left") -> None:
        """DoubleSpinBox widget.

        Args:
            param (tuple[float, float, float]): parameters for spinbox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        self.__spinbox = QDoubleSpinBox()
        self.__spinbox.setRange(param[0], param[1])
        self.__spinbox.setValue(param[2])
        super().__init__(self.__spinbox, name, unit, orientation)

    def changeWidgetSettings(self, newParam : tuple[float, float, float]) -> None:
        """DoubleSpinBox update widget parameter method.

        Args:
            newParam (tuple[float, float, float]): new parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
        """
        self.__spinbox.setRange(newParam[0], newParam[1])
        self.__spinbox.setValue(newParam[2])
    
    @property
    def value(self) -> float:
        """Returns the DoubleSpinBox current value.
        """
        return self.__spinbox.value()
    
    @value.setter
    def value(self, value: float) -> None:
        """Sets the DoubleSpinBox current value to show on the widget.

        Args:
            value (float): value to set.
        """
        self.__spinbox.setValue(value)

    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the SpinBox widget.
        Exposed signals are:
        
        - valueChanged,
        - textChanged

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "valueChanged" : self.__spinbox.valueChanged,
            "textChanged" : self.__spinbox.textChanged
        }

class LabeledSlider(LocalWidget):
    def __init__(self, param: tuple[int, int, int], name: str, unit: str = "", orientation: str = "left") -> None:
        """Slider widget.

        Args:
            param (tuple[int, int, int])): parameters for spinbox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
            orientation (str, optional): label orientation on the layout. Defaults to "left".
        """
        self.__slider = QLabeledSlider(Qt.Horizontal)
        self.__slider.setRange(param[0], param[1])
        self.__slider.setValue(param[2])
        super().__init__(self.__slider, name, unit, orientation)
    
    def changeWidgetSettings(self, newParam : tuple[int, int, int]) -> None:
        """Slider update widget parameter method.

        Args:
            newParam (tuple[int, int, int]): new parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
        """
        self.__slider.setRange(newParam[0], newParam[1])
        self.__slider.setValue(newParam[2])
    
    @property
    def value(self) -> int:
        """Returns the Slider current value.
        """
        return self.__slider.value()
    
    @value.setter
    def value(self, value: int) -> None:
        """Sets the DoubleSpinBox current value to show on the widget.

        Args:
            value (float): value to set.
        """
        self.__slider.setValue(value)

    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the SpinBox widget.
        Exposed signals are:
        
        - valueChanged

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "valueChanged" : self.__slider.valueChanged
        }

class LineEdit(LocalWidget):
    
    def __init__(self, param: str, name: str, unit: str = "", orientation: str = "left") -> None:
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
    
    def changeWidgetSettings(self, newParam : str) -> None:
        """Updates LineEdit text contents.

        Args:
            newParam (str): new string for LineEdit.
        """
        self.__lineEdit.setText(newParam)

    @property
    def value(self) -> str:
        """Returns the LineEdit current text.
        """
        return self.__lineEdit.text()
    
    @value.setter
    def value(self, value: str) -> None:
        """Sets the LineEdit current text to show on the widget.

        Args:
            value (str): string to set.
        """
        self.__lineEdit.setText(value)
    
    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the LineEdit widget.
        Exposed signals are:
        
        - textChanged,
        - textEdited

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "textChanged" : self.__lineEdit.textChanged,
            "textEdited" : self.__lineEdit.textEdited
        }

class CameraSelection(QObject):
    newCameraRequested = pyqtSignal(str, str, str)

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
        self.camerasComboBox = ComboBox([], "Interface")
        self.nameLineEdit = LineEdit(param="MyCamera", name="Camera name")
        self.idLineEdit = LineEdit(param="0", name="Camera ID/SN", orientation="right")
        self.addButton = QPushButton("Add camera")
        self.addButton.setEnabled(False)

        # create widget layout
        self.camerasComboBox.signals["currentIndexChanged"].connect(self._setAddEnabled)
        self.addButton.clicked.connect(lambda: self.newCameraRequested.emit(self.camerasComboBox.value[0], self.nameLineEdit.value, self.idLineEdit.value))

        self.formLayout = QFormLayout()
        self.formLayout.addRow(self.camerasComboBox.label, self.camerasComboBox.widget)
        self.formLayout.addRow(self.nameLineEdit.label, self.nameLineEdit.widget)
        self.formLayout.addRow(self.idLineEdit.label, self.idLineEdit.widget)
        self.formLayout.addRow(self.addButton)
        self.group.setLayout(self.formLayout)
        self.group.setFlat(True)

    def setAvailableCameras(self, cameras: list[str]) -> None:
        """Sets the ComboBox with the list of available camera devices.

        Args:
            cameras (list[str]): list of available camera devices.
        """
        # we need to extend the list of available cameras with a selection text
        cameras.insert(0, "Select device")
        self.camerasComboBox.changeWidgetSettings(cameras)
        self.camerasComboBox.isEnabled = True
    
    def _setAddEnabled(self, idx: int):
        """Private method serving as an enable/disable mechanism for the Add button widget.
        This is done to avoid the first index, the "Select device" string, to be considered
        as a valid camera device (which is not).
        """
        if idx > 0:
            self.addButton.setEnabled(True)
        else:
            self.addButton.setEnabled(False)


class RecordHandling(QObject):
    recordRequested = pyqtSignal(int)
    def __init__(self) -> None:
        """Recording Handling widget. Includes QPushButtons which allow to handle the following operations:

        - live viewing;
        - recording to output file;
        - single frame snap;
        - album stacking snap.

        Widget layout:
        |(0,0) QPushButton (Snap)|(0,1) QPushButton (Album)|(0,2) QPushButton  (Live) |
        |(1,0-1)          QSpinBox (Record size)           |(0,2) QPushButton (Record)| 

        """
        QObject.__init__(self)

        self.group = QGroupBox()
        self.layout = QGridLayout()

        self.snap = QPushButton("Snap")
        self.album = QPushButton("Album")
        self.live = QPushButton("Live")

        # the live button is implemented as a toggle button
        self.live.setCheckable(True)

        self.recordSpinBox = QSpinBox()
        self.recordSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)

        # todo: this is currently hardcoded
        # maybe should find a way to initialize
        # from outside the instance?
        self.recordSpinBox.setRange(1, 5000)
        self.recordSpinBox.setValue(100)

        self.record = QPushButton("Record")
        
        self.layout.addWidget(self.snap, 0, 0)
        self.layout.addWidget(self.album, 0, 1)
        self.layout.addWidget(self.live, 0, 2)
        self.layout.addWidget(self.recordSpinBox, 1, 0, 1, 2)
        self.layout.addWidget(self.record, 1, 2)
        self.group.setLayout(self.layout)

        # whenever the live button is toggled,
        # the other pushbutton must be enabled/disabled
        # in order to avoid undefined behaviors
        # when grabbing frames from the device
        self.live.toggled.connect(self._handleLiveToggled)

        # whenever the record button is clicked,
        # the widgets send a signal
        # with the current SpinBox value
        self.record.clicked.connect(lambda: self.recordRequested.emit(self.recordSpinBox.value()))

    def _handleLiveToggled(self, status: bool) -> None:
        """Enables/Disables pushbuttons when the live button is toggled.

        Args:
            status (bool): new live button status.
        """
        self.snap.setEnabled(not status)
        self.album.setEnabled(not status)
        self.record.setEnabled(not status)
    
    @property
    def recordSize(self) -> int:
        """Returns the record size currently indicated in the QSpinBox widget.
        """
        return self.recordSpinBox.value()

    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the RecordHandling widget.
        Exposed signals are:
        
        - snapRequested,
        - albumRequested,
        - liveRequested,
        - recordRequested

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "snapRequested" : self.snap.clicked,
            "albumRequested" : self.album.clicked,
            "liveRequested" : self.live.toggled,
            "recordRequested" : self.recordRequested,
        }

class ROIHandling(QObject):
    changeROIRequested = pyqtSignal(ROI)
    fullROIRequested = pyqtSignal(ROI)
    def __init__(self, sensorShape : ROI) -> None:
        """ROI Handling widget. Defines a set of non-custom widgets to set the Region Of Interest of the device.
        This widget is common for all devices.

        Args:
            cameraROI (ROI): data describing the device sensor shape and step value to increment/decrement each parameter.
        """
        QObject.__init__(self)
        # todo: maybe this is inefficient...
        # in previous implementation
        # copying the reference would cause
        # issues when changing the ROI
        # so we'll create a local copy
        # and discard the input
        self.sensorFullROI = replace(sensorShape)

        # todo: these widgets are not
        # our custom LocalWidgets
        # but since they are common
        # for all types of cameras
        # it is not worth to customize them...
        # ... right?
        self.offsetXLabel = QLabel("Offset X (px)")
        self.offsetXLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.offsetXSpinBox = QSpinBox()
        self.offsetXSpinBox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.offsetXSpinBox.setRange(0, self.sensorFullROI.width)
        self.offsetXSpinBox.setSingleStep(self.sensorFullROI.ofs_x_step)
        self.offsetXSpinBox.setValue(0)

        self.offsetYLabel = QLabel("Offset Y (px)", )
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

        self.layout = QGridLayout()
        self.layout.addWidget(self.offsetXLabel, 0, 0)
        self.layout.addWidget(self.offsetXSpinBox, 0, 1)
        self.layout.addWidget(self.offsetYSpinBox, 0, 2)
        self.layout.addWidget(self.offsetYLabel, 0, 3)
        
        self.layout.addWidget(self.widthLabel, 1, 0)
        self.layout.addWidget(self.widthSpinBox, 1, 1)
        self.layout.addWidget(self.heightSpinBox, 1, 2)
        self.layout.addWidget(self.heightLabel, 1, 3)
        self.layout.addWidget(self.changeROIButton, 2, 0, 1, 2)
        self.layout.addWidget(self.fullROIButton, 2, 2, 1, 2)

        # "clicked" signals are connected to private slots.
        # These slots expose the signals available to the user
        # to process the new ROI information if necessary.
        self.changeROIButton.clicked.connect(self._onROIChanged)
        self.fullROIButton.clicked.connect(self._onFullROI)

        self.group = QGroupBox()
        self.group.setLayout(self.layout)
    
    def changeWidgetSettings(self, settings : ROI):
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
        """Private slot for ROI changed button pressed. Exposes a signal with the updated ROI settings.
        """
        # read the current SpinBoxes status
        newRoi = ROI(
            offset_x=self.offsetXSpinBox.value(),
            ofs_x_step=self.offsetXSpinBox.singleStep(),
            offset_y=self.offsetYSpinBox.value(),
            ofs_y_step=self.offsetXSpinBox.singleStep(),            
            width=self.widthSpinBox.value(),
            width_step=self.widthSpinBox.singleStep(),
            height=self.heightSpinBox.value(),
            height_step=self.heightSpinBox.singleStep()
        )
        self.changeROIRequested.emit(newRoi)

    def _onFullROI(self) -> None:
        """Private slot for full ROI button pressed. Exposes a signal with the full ROI settings.
        It also returns the widget settings to their original value.
        """
        self.changeWidgetSettings(self.sensorFullROI)
        self.fullROIRequested.emit(replace(self.sensorFullROI))
    
    @property
    def signals(self) -> dict[str, pyqtSignal]:
        """Returns a dictionary of signals available for the ROIHandling widget.
        Exposed signals are:
        
        - changeROIRequested,
        - fullROIRequested,

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "changeROIRequested" : self.changeROIRequested,
            "fullROIRequested" : self.fullROIRequested,
        }