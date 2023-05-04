import numpy as np
from abc import abstractmethod
from typing import Union, Tuple
from qtpy.QtCore import QObject
from napari_live_recording.common import ROI, ColorType
from typing import Dict, List, Any
from dataclasses import dataclass, replace
from abc import ABC

# the camera interface and setting management is heavily inspired by the work of Xavier Casas Moreno in ImSwitch
# reference work: https://github.com/kasasxav/ImSwitch/blob/master/imswitch/imcontrol/model/managers/detectors/DetectorManager.py
# Xavier Casas Moreno GitHub profile: https://github.com/kasasxav
@dataclass
class Parameter(ABC):
    editable: bool
    """Wether the parameter is readonly or not.
    """

@dataclass
class NumberParameter(Parameter):
    value: Union[int, float]
    """Value of the parameter.
    """

    unit: str
    """Unit measure of the specific parameter.
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
        QObject.__init__(self)
        self.name = name
        self.deviceID = deviceID
        self.cameraKey = f"{self.name}:{self.__class__.__name__}:{str(self.deviceID)}"
        self.parameters = parameters
        self._roiShape = sensorShape
        self._fullShape = sensorShape
        self._colorType = ColorType.GRAYLEVEL

    @property
    def colorType(self) -> ColorType:
        return self._colorType
    
    @property
    def fullShape(self) -> ROI:
        return self._fullShape
    
    @property
    def roiShape(self) -> ROI:
        return self._roiShape
    
    @roiShape.setter
    def roiShape(self, newROI: ROI) -> None:
        self._roiShape = replace(newROI)
    
    @abstractmethod
    def setAcquisitionStatus(self, started: bool) -> None:
        """Sets the current acquisition status of the camera device. 
            - True: acquisition started;
            - False: acquisition stopped.
        """
        raise NotImplementedError()

    @abstractmethod
    def grabFrame(self) -> np.ndarray:
        """Returns the latest captured frame as a numpy array.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def changeROI(self, newROI: ROI) -> None:
        """Changes the Region Of Interest of the sensor's device.
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

    def __enter__(self):
        self.setAcquisitionStatus(True)
    
    def __exit__(self, exc_type, exc_value, tb):
        self.setAcquisitionStatus(False)