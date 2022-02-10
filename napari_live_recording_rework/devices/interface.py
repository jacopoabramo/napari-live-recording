from abc import ABC, abstractmethod
from typing import Union
from widgets.widgets import (
    ComboBox,
    ROIHandling, 
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
    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """Generic camera device. Each device lives in its own thread, and has a set of common widgets:

        - ROI handling widget;
        - Delete device button.

        Constructor must be called AFTER calling the child class constructor to ensure that parameter widgets
        can be accessed.

        Args:
            name (str): name of the camera device.
            deviceID (Union[str, int]): device ID.
        """
        self.parameters = {}

    @abstractmethod
    def addLocalWidgets(self) -> None:
        """Adds the user-defined widgets to the final device widget.
        """
        pass

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

    def addParameter(self, widgetType: str, name: str, unit: str, param: ParameterType, orientation="left") -> None:
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
            - orientation (str, optional): orientation of the label for the parameter (can either be "left" or "right"). Default is "left".
        """
        if not name in self.parameters:
            paramWidget = self.__availableWidgets[widgetType.lower()](param, name, unit, orientation)
            self.parameters[name] = paramWidget

