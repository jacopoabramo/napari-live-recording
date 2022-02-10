from abc import ABC, abstractmethod
from typing import Union
from PyQt5.QtWidgets import QVBoxLayout
import numpy as np
from common import ROI
from widgets.widgets import (
    LocalWidget,
    ROIHandling,
    ComboBox,
    SpinBox, 
    DoubleSpinBox, 
    LabeledSlider, 
    LineEdit
)

ParameterType = Union[str, list[str], tuple[int, int, int], tuple[float, float, float]]

class Camera(ABC):
    __availableWidgets = {
        "combobox" : ComboBox,
        "spinbox" : SpinBox,
        "doublespinbox" : DoubleSpinBox,
        "slider" : LabeledSlider,
        "lineedit" : LineEdit
    }
    def __init__(self, name: str, deviceID: Union[str, int], paramDict: dict[str, LocalWidget], sensorShape: ROI) -> None:
        """Generic camera device. Each device lives in its own thread, and has a set of common widgets:

        - ROI handling widget;
        - Delete device button.

        Constructor must be called AFTER calling the child class constructor to ensure that parameter widgets
        can be accessed.

        Args:
            name (str): name of the camera device.
            deviceID (Union[str, int]): device ID.
            paramDict (dict[str, LocalWidget]): dictionary of parameters' widgets initialized for the specific device.
            sensorShape (ROI): camera physical shape and information related to the widget steps.
        """
        self.name = name
        self.deviceID = deviceID
        self.layout = QVBoxLayout()
        self.ROIHandling = ROIHandling(sensorShape)
        self.widgets = paramDict
        for widget in self.widgets.values():
            self.layout.addLayout(widget.layout)
        self.layout.addLayout(self.ROIHandling.layout)

    @abstractmethod
    def initDevice(self, name: str, deviceID: Union[str, int]) -> None:
        """Initializes the device.
        """
        pass

    @abstractmethod
    def closeDevice(self) -> None:
        """Closes the device if necessary.
        """
        pass

    @abstractmethod
    def grabFrame(self) -> np.array:
        """Returns the latest captured frame as a numpy array
        """
        pass

    @abstractmethod
    def cameraInfo(self) -> list[str]:
        """Returns a list of strings containing relevant device informations.
        """
        pass

    def addParameter(self, widgetType: str, name: str, unit: str, param: ParameterType, paramDict: dict[str, ParameterType], orientation="left") -> None:
        """Adds a parameter in the form of a widget, exposing the respective signals to enable connections to user-defined slots.
        If the parameter already exists, it will not be added to the parameter list.

        Args:
            - widgetType (str): type of widget created (case-independent), can be either:
                - \"ComboBox\"
                - \"SpinBox\"
                - \"DoubleSpinBox\"
                - \"LabeledSlider\"
                - \"LineEdit\"
            - name (str): name of the added parameter (i.e. \"Exposure time\")
                - this will be the name shown in the GUI
            - unit (str): unit measure of the added parameter (i.e. \"ms\")
            - param (ParameterType): actual parameter items
            - paramDict (dict[str, ParameterType]): dictionary to store all parameters.
            - orientation (str, optional): orientation of the label for the parameter (can either be "left" or "right"). Default is "left".
        """
        if not name in self.parameters:
            paramWidget = self.__availableWidgets[widgetType.lower()](param, name, unit, orientation)
            paramDict[name] = paramWidget

