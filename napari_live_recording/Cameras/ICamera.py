"""Generic Camera interface
"""

from abc import ABC, abstractmethod
import numpy as np

class ICamera(ABC):
    """Abstract class representing the camera device interface.
    Gives access to a series of functionality differently supported by each device.

    :param ABC: abstract metaclass
    :type ABC: ABC
    """

    @abstractmethod
    def __init__(self) -> None:
        """Abstract constructor method
        """
        super().__init__()
        self.camera_name = "ICamera"

    @abstractmethod
    def __del__(self) -> None:
        """Abstract destructor method"""
        pass

    @abstractmethod
    def open_device(self) -> bool:
        """Opens the device, enabling acquisition.

        :return: True if device has been started, otherwise False.
        :rtype: bool
        """
        pass
    
    @abstractmethod
    def close_device(self) -> None:
        """Closes device, disabling acquisition
        """
        pass

    @abstractmethod
    def capture_image(self) -> np.array:
        """Captures a single image.

        :return: a 2D numpy array (grayscale 8 bits by default)
        :rtype: numpy.array
        """
        pass

    @abstractmethod
    def set_exposure(self, exposure) -> None:
        """Sets the exposure time for the current device.

        :param exposure: the new exposure time (for OpenCV time scale is fixed, for other devices is microseconds)
        :type exposure: int, string
        """
        pass

    @abstractmethod
    def set_roi(self, roi : list) -> None:
        """Sets a ROI for the current device.

        :param roi: list of integers indicating the new ROI (this is still not supported)
        :type roi: list
        """
        pass

    @abstractmethod
    def get_roi(self) -> list:
        """Returns the current set ROI.

        :return: list of current ROI.
        :rtype: list
        """
        pass
    
    def get_name(self) -> str:
        """Returns the camera name specified by camera_name

        :return: the camera name
        :rtype: str
        """
        return self.camera_name