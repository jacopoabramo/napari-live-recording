"""Generic Camera interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np


@dataclass
class CameraROI():
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
    def get_available_pixel_formats(self) -> list:
        """Returns a list with associated pixel byte type.

        i.e.
        ["8-bit gray", "16-bit gray"]

        The first item of the list should be the default pixel format at camera startup.

        :return: list of strings with the supported pixel formats.
        :rtype: list[str]
        """
        pass

    @abstractmethod
    def set_pixel_format(self, format) -> None:
        """Sets a new pixel data format for the camera.

        :param format: the new data format (for OpenCV time scale is fixed, for other devices is microseconds)
        :type exposure: str
        """
        pass 

    @abstractmethod
    def set_exposure(self, exposure) -> None:
        """Sets the exposure time for the current device.

        :param exposure: the new exposure time (for OpenCV time scale is fixed, for other devices is microseconds)
        :type exposure: int, str
        """
        pass

    @abstractmethod
    def set_roi(self, roi: CameraROI) -> None:
        """Sets a ROI for the current device.

        :param roi: tuple indicating the new ROI
        :type roi: CameraROI
        """
        pass

    @abstractmethod
    def get_roi(self) -> CameraROI:
        """Returns the current set ROI.

        :return: tuple of current ROI.
        :rtype: CameraROI
        """
        pass
    
    @abstractmethod
    def get_sensor_range(self) -> CameraROI:
        pass

    @abstractmethod
    def set_full_frame(self) -> None:
        """Sets ROI to full frame.
        """
        pass

    @abstractmethod
    def get_acquisition(self) -> bool:
        """Returns current acquisition status.

        :return: True if camera is enabled, otherwise False.
        :rtype: bool
        """
        pass

    @abstractmethod
    def set_acquisition(self, is_enabled) -> None:
        """Sets current acquisition status.

        :param is_enabled: new acquisition status
        :type exposure: bool
        """
        pass

    @abstractmethod
    def get_frames_per_second(self) -> int:
        """Returns the current FPS of a given device.

        :return: the currently calculated FPS
        :rtype: int
        """
        pass

    def get_name(self) -> str:
        """Returns the camera name specified by camera_name

        :return: the camera name
        :rtype: str
        """
        return self.camera_name
