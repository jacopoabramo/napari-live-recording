from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union
from widgets.widgets import (
    ComboBox, 
    SpinBox, 
    DoubleSpinBox, 
    Slider, 
    LineEdit
) 

@dataclass
class ROI:
    """Dataclass for ROI settings.
    """
    offset_x: int = 0
    offset_y: int = 0
    height: int = 0
    width: int = 0
    ofs_x_step: int = 1
    ofs_y_step: int = 1
    width_step: int = 1
    height_step: int = 1

class Camera(ABC):
    def __init__(self, name, device_id: Union[str, int]) -> None:
        """Constructor method for generic camera device.

        Args:
            name (str): name of the camera device.
            device_id (Union[str, int]): device ID.
        """
        self.__availableWidgets = {
            "combobox" : ComboBox,
            "spinbox" : SpinBox,
            "doublespinbox" : DoubleSpinBox,
            "slider" : Slider,
            "lineedit" : LineEdit
        }
        self.name = name
        self.device_id = device_id
        self.parameters = {}

    @abstractmethod
    def initDevice(self) -> None:
        pass

    @abstractmethod
    def closeDevice(self) -> None:
        pass

    def addParameter(self, widgetType: str, name: str, unit: str, param: Union[str, list[str], tuple[int, int, int], tuple[float, float, float]]) -> None:
        """Adds a parameter in the form of a widget, exposing the respective signals to enable connections to user-defined slots.
        If the parameter already exists, it will not be added to the parameter list.

        Args:
            - widgetType (str): type of widget created (case-independent), can be either:
                - \"ComboBox\"
                - \"SpinBox\"
                - \"DoubleSpinBox\"
                - \"Slider\"
                - \"LineEdit\"
            - name (str): name of the added parameter (i.e. \"Exposure time\")
                - this will be the name shown in the GUI
            - unit (str): unit measure of the added parameter (i.e. \"ms\")
            - param (Union[str, list[str], tuple[int, int, int], tuple[float, float, float]]): actual parameter items
        """
        paramWidget = self.__availableWidgets[widgetType.lower()](param=param, name=name, unit=unit)
        self.parameters[name] = paramWidget

