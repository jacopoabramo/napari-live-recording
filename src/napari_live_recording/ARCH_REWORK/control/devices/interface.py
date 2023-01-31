import numpy as np
from abc import abstractmethod
from typing import Union, Tuple
from qtpy.QtCore import QObject
from napari_live_recording.ARCH_REWORK.common import ROI, WidgetEnum
from typing import Dict, List, Any
from dataclasses import dataclass
from abc import ABC

# the camera interface and setting management is heavily inspired by the work of Xavier Casas Moreno in ImSwitch
# reference work: https://github.com/kasasxav/ImSwitch/blob/master/imswitch/imcontrol/model/managers/detectors/DetectorManager.py
# Xavier Casas Moreno GitHub profile: https://github.com/kasasxav
@dataclass
class Parameter(ABC):
    widget: WidgetEnum
    """Widget type associated with the parameter.
    """

    unit: str
    """Unit measure of the specific parameter.
    """

    editable: bool
    """Wether the parameter is readonly or not.
    """

@dataclass
class NumberParameter(Parameter):
    value: Union[int, float]
    """Value of the parameter.
    """

    valueLimits: Tuple[Union[int, float], Union[int, float]]
    """Upper and lower boundaries of the possible parameter's value.
    """

@dataclass
class ListParameter(Parameter):
    value: str
    """Value of the parameter.
    """

    options: List[str]
    """List of possible options for the parameter.
    """
    

class ICamera(QObject):
    def __init__(self, name: str, deviceID: Union[str, int], parameters: Dict[str, Any], sensorShape: ROI) -> None:
        """Generic camera device interface. Each device is initialized with a series of parameters.
        Live and recording are handled using child thread workers.
        
        Args:
            name (str): name of the camera device.
            deviceID (`Union[str, int]`): device ID.
            parameters (`Dict[str, Any]`): dictionary of parameters of the specific device.
            sensorShape (`ROI`): camera physical shape and information related to the widget steps.
        """
        super().__init__(self)
        self.name = name
        self.deviceID = deviceID
        self.cameraKey = f"{self.name}:{self.__class__.__name__}:{str(self.deviceID)}"
        self.parameters = parameters
        self._roiShape = sensorShape
        self._fullShape = sensorShape
        self.frameBuffer = None
    
    @property
    def fullShape(self) -> ROI:
        return self._fullShape
    
    @property
    def roi(self) -> ROI:
        return self._roiShape
    
    @abstractmethod
    def setAcquisitionStatus(self, started: bool) -> bool:
        """Sets the current acquisition status of the camera device.
        If `started` is True, camera will start acquiring, otherwise the camera will stop acquiring.

        Args:
            started (bool): _description_

        Raises:
            NotImplementedError: _description_
            NotImplementedError: _description_
            NotImplementedError: _description_
        """

    @abstractmethod
    def grabFrame(self) -> np.ndarray:
        """Returns the latest captured frame as a numpy array.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def changeROI(self, newROI: ROI) -> bool:
        """Changes the Region Of Interest of the sensor's device.
        """
        raise NotImplementedError()

    @abstractmethod
    def cameraInfo(self) -> List[str]:
        """Returns a List of strings containing relevant device informations.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def changeParameter(name: str, value: Any) -> None:
        """Changes one of the settings of the device.

        Args:
            name (str): name of the setting.
            value (Any): new value for the specified setting.
        """
        pass

    def close(self) -> None:
        """Optional method to close the device.
        """
        pass