from abc import ABC, abstractmethod
import numpy as np

class CameraError(Exception):
    def __init__(self, error: str) -> None:
        self.error_description = error
    
    def __str__(self) -> str:
        return self.error_description

class ICamera(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.camera_name = "ICamera"
        self.roi = []

    @abstractmethod
    def __del__(self) -> None:
        return super().__del__()

    @abstractmethod
    def __del__(self) -> None:
        pass

    @abstractmethod
    def open_device(self) -> bool:
        pass
    
    @abstractmethod
    def close_device(self) -> None:
        pass

    @abstractmethod
    def capture_image(self) -> np.array:
        pass

    @abstractmethod
    def set_exposure(self, exposure) -> None:
        pass

    @abstractmethod
    def set_roi(self, roi : list) -> None:
        self.roi = roi

    @abstractmethod
    def get_roi(self) -> list:
        return self.roi

    def get_name(self) -> str:
        return self.camera_name