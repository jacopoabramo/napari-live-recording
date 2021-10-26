from .ICamera import ICamera
import numpy as np
from time import sleep

CAM_TEST = "Widget dummy camera"

class TestCamera(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.camera_name = CAM_TEST
        self.roi = [500, 500]
        self.fill_value = 0
        self.increase_factor = 1
        self.is_enabled = False
        self.sleep_time = 0.01
    
    def __del__(self) -> None:
        return super().__del__()

    def open_device(self) -> bool:
        print("Dummy camera opened!")
        self.is_enabled = True
        return self.is_enabled
    
    def close_device(self) -> None:
        print("Dummy camera closed!")
        self.is_enabled = False
        return self.is_enabled
    
    def capture_image(self) -> np.array:
        img = np.full(shape=tuple(self.roi), fill_value = self.fill_value, dtype="uint8")
        if self.increase_factor > 0:
            if self.fill_value == 255:
                self.increase_factor = -1
        else:
            if self.fill_value == 0:
                self.increase_factor = 1
        self.fill_value += self.increase_factor
        sleep(self.sleep_time)
        return img

    
    def set_exposure(self, exposure) -> None:
        print(f"Dummy camera exposure set to {exposure}")

    def set_roi(self, roi : list) -> None:
        self.roi = roi
    
    def get_roi(self) -> list:
        return self.roi
    
    def get_acquisition(self) -> bool:
        return self.is_enabled
    
    def set_acquisition(self, is_enabled) -> None:
        (self.open_device() if is_enabled else self.close_device())
    
    def get_frames_per_second(self) -> int:
        return round(1/(self.sleep_time))