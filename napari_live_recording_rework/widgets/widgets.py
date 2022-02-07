from gc import isenabled
from typing import Callable
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QLineEdit, QPushButton
from PyQt5.QtWidgets import QFormLayout, QGridLayout
from abc import ABC, abstractmethod

class LocalWidget(ABC, QWidget):
    def __init__(self, name: str, unit: str = "") -> None:
        """Common widget constructor.

        Args:
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
        """
        super(LocalWidget, self).__init__()
        self.__name = name
        self.__unit = unit
        labelStr = (self.__name + " (" + self.__unit + ")" if self.__unit != "" else self.__name)
        self.__label = QLabel(labelStr)
        self.__label.setAlignment(QtCore.Qt.AlignRight)
        self.__layout = QFormLayout(self)
    
    @property
    def layout(self) -> QFormLayout:
        """ QFormLayout structured as |<Text label>|<Specific widget>| (this must be built in the specific class constructor).
        """
        return self.__layout

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

    @property
    @abstractmethod
    def isEnabled(self) -> bool:
        """Widget is enabled for editing (True) or not (False).
        """
        pass
    
    @isEnabled.setter
    @abstractmethod
    def isEnabled(self, enable : bool) -> None:
        """Sets widget enabled for editing (True) or not (False).
        """
        pass
    
    @property
    @abstractmethod
    def signals(self) -> dict[str, Callable]:
        """Common widget method to expose signals to the device.
        """
        pass

class ComboBox(LocalWidget):
    def __init__(self, param : list[str], name : str, unit : str = "") -> None:
        """ComboBox widget.

        Args:
            param (list[str]): list of parameters added to the ComboBox.
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
        """
        super().__init__(name, unit)
        self.__combobox = QComboBox(self)
        self.__combobox.addItems(param)
        self.__layout.addRow(self.__label, self.__combobox)
    
    def changeWidgetSettings(self, newParam: list[str]) -> None:
        """ComboBox update widget parameter method. Old list of items is deleted.

        Args:
            newParam (list[str]): new list of parameters to add to the ComboBox.
        """
        self.__combobox.clear()
        self.__combobox.addItems(newParam)
    
    @property
    def value(self) -> tuple[str, int]:
        """Returns a tuple containing the ComboBox current text and index.
        """
        return (self.__combobox.currentText(), self.__combobox.currentIndex())
    
    @property
    def isEnabled(self) -> bool:
        return self.__combobox.isEnabled()
    
    @isEnabled.setter
    def isEnabled(self, enable : bool) -> None:
        self.__combobox.setEnabled(enable)
    
    @property
    def signals(self) -> dict[str, Callable]:
        """Returns a list of signals available for the ComboBox widget.
        Exposed signals are:
        
        - currentIndexChanged,
        - currentTextChanged

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "currentIndexChanged" : self.__combobox.currentIndexChanged,
            "currentTextChanged" : self.__combobox.currentTextChanged
        }
        

class SpinBox(LocalWidget):
    def __init__(self, param: tuple[int, int, int], name: str, unit: str = "") -> None:
        """SpinBox widget.

        Args:
            param (tuple[int, int, int]): parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
        """
        super().__init__(name, unit)
        self.__spinbox = QSpinBox(self)
        self.__spinbox.setRange(param[0], param[1])
        self.__spinbox.setValue(param[2])
        self.__layout.addRow(self.__label, self.__spinbox)
    
    def changeWidgetSettings(self, newParam : tuple(int, int, int)) -> None:
        """SpinBox update widget parameter method.

        Args:
            newParam (tuple(int, int, int)): new parameters for SpinBox settings: (<minimum_value>, <maximum_value>, <starting_value>)
        """
        self.__spinbox.setRange(newParam[0], newParam[1])
        self.__spinbox.setValue(newParam[2])
    
    @property
    def value(self) -> int:
        """Returns the SpinBox current value.
        """
        return self.__spinbox.value()
    
    @property
    def isEnabled(self) -> bool:
        return self.__spinbox.isEnabled()
    
    @isEnabled.setter
    def isEnabled(self, enable : bool) -> None:
        self.__spinbox.setEnabled(enable)
    
    @property
    def signals(self) -> dict[str, Callable]:
        """Returns a list of signals available for the SpinBox widget.
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

class DoubleSpinBox(LocalWidget):
    def __init__(self, param: tuple[float, float, float], name: str, unit: str = "") -> None:
        """DoubleSpinBox widget.

        Args:
            param (tuple[float, float, float]): parameters for spinbox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
        """
        super().__init__(name, unit)
        self.__spinbox = QDoubleSpinBox(self)
        self.__spinbox.setRange(param[0], param[1])
        self.__spinbox.setValue(param[2])
        self.__layout.addRow(self.__label, self.__spinbox)

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
    
    @property
    def isEnabled(self) -> bool:
        return self.__spinbox.isEnabled()
    
    @isEnabled.setter
    def isEnabled(self, enable : bool) -> None:
        self.__spinbox.setEnabled(enable)

    @property
    def signals(self) -> dict[str, Callable]:
        """Returns a list of signals available for the SpinBox widget.
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

class Slider(LocalWidget):
    def __init__(self, param: tuple[int, int, int], name: str, unit: str = "") -> None:
        """Slider widget.

        Args:
            param (tuple[int, int, int])): parameters for spinbox settings: (<minimum_value>, <maximum_value>, <starting_value>)
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
        """
        super().__init__(name, unit)
        self.__slider = QSlider(self, QtCore.Qt.Horizontal)
        self.__slider.setRange(param[0], param[1])
        self.__slider.setValue(param[2])
        self.__layout.addRow(self.__label, self.__slider)

        # adding an extra text to the widget label (the current slider value)
        self._updateLabelValue(param[2])

        # we connect the valueChanged signal to _updateLabelValue
        # this signal can still be connected to other slots if necessary
        self.__slider.valueChanged.connect(self._updateLabelValue)
    
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
    
    def _updateLabelValue(self, value : int) -> None:
        labelStr = (self.__name + " (" + self.__unit + ")" if self.__unit != "" else self.__name)
        self.__label.setText(labelStr + " - " + str(value))

    @property
    def isEnabled(self) -> bool:
        return self.__slider.isEnabled()
    
    @isEnabled.setter
    def isEnabled(self, enable : bool) -> None:
        self.__slider.setEnabled(enable)

    @property
    def signals(self) -> dict[str, Callable]:
        """Returns a list of signals available for the SpinBox widget.
        Exposed signals are:
        
        - valueChanged

        Returns:
            dict: dict of signals (key: function name, value: function objects).
        """
        return {
            "valueChanged" : self.__slider.valueChanged
        }

class LineEdit(LocalWidget):
    
    def __init__(self, param: str, name: str, unit: str = "", editable = False) -> None:
        """LineEdit widget. Editing disabled by default.

        Args:
            param (str): line edit contents
            name (str): parameter label description.
            unit (str, optional): parameter unit measure. Defaults to "".
        """
        super().__init__(name, unit)
        self.__lineEdit = QLineEdit(self, param)
        self.__lineEdit.setEnabled(editable)
        self.__layout.addRow(self.__label, self.__lineEdit)
    
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
    
    @property
    def isEnabled(self) -> bool:
        return self.__lineEdit.isEnabled()
    
    @property
    @isEnabled.setter
    def isEnabled(self, enable: bool) -> None:
        self.__lineEdit.setEnabled(enable)
    
    @property
    def signals(self) -> dict[str, Callable]:
        """Returns a list of signals available for the LineEdit widget.
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

class CameraSelection(QWidget):
    def __init__(self) -> None:
        """Camera selection widget. It includes the following widgets:

        - a ComboBox for camera selection based on strings to identify each camera type;
        - a LineEdit for camera ID or serial number input
        - a QPushButton to add the camera

        Widget layout:
        |(0,0) ComboBox|(0,1) QPushButton|
        |(1,0) LineEdit|(1,1)            |

        The QPushButton remains disabled as long as no camera is selected (first index is highlited). 
        """
        super(CameraSelection, self).__init__()
        self.camerasComboBox = ComboBox([], "Camera")
        self.idLineEdit = LineEdit(param="", name="Camera ID/SN", editable=True)
        self.addButton = QPushButton("Add camera", self)
        self.addButton.setEnabled(False)

        # create widget layout
        self.widgetLayout = QGridLayout(self)
        self.widgetLayout.addLayout(self.camerasComboBox.layout, 0, 0, 1, 1)
        self.widgetLayout.addWidget(self.addButton, 0, 1, 1, 1)
        self.widgetLayout.addLayout(self.idLineEdit.layout, 1, 0, 1, 1)
    
    def setAvailableCameras(self, cameras: list[str]) -> None:
        """Sets the ComboBox with the list of available camera devices.

        Args:
            cameras (list[str]): list of available camera devices.
        """
        # we need to extend the list of available cameras with a selection text
        cameras.insert(0, "Select device")
        self.camerasComboBox.changeWidgetSettings(cameras)