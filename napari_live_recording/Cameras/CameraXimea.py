from .ICamera import ICamera

# Ximea camera support only provided by downloading the Ximea Software package
# see https://www.ximea.com/support/wiki/apis/APIs for more informations
from ximea.xiapi import Camera as XiCamera, Xi_error
from ximea.xiapi import Image as XiImage
from time import sleep
import numpy as np

CAM_XIMEA = "Ximea xiB-64"

class CameraXimea(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.camera = XiCamera()
        self.image = XiImage()
        self.camera_name = CAM_XIMEA
        self.roi = [500, 500]
        self.frame_rate = 0.01
    
    def __del__(self) -> None:
        self.close_device()
    
    def __str__(self) -> str:
        return CAM_XIMEA
    
    def open_device(self) -> bool:
        try:
            self.camera.open_device()
            max_lut_idx = self.camera.get_LUTIndex_maximum()
            for idx in range(0, max_lut_idx):
                self.camera.set_LUTIndex(idx)
                self.camera.set_LUTValue(idx)
            self.camera.enable_LUTEnable()
            self.camera.start_acquisition()
        except Xi_error:
            return False
        return True

    def close_device(self) -> None:
        try:
            self.camera.stop_acquisition()
            self.camera.close_device()
            del self.camera
        except Xi_error: # Camera not connected or already closed
            pass
    
    def capture_image(self) -> np.array:
        try:
            self.camera.get_image(self.image)
            data = self.image.get_image_data_numpy()
        except Xi_error:
            data = None
        sleep(0.01)
        return data

    def set_exposure(self, exposure) -> None:
        try:
            self.camera.set_exposure(exposure)
            self.frame_rate = float(1.0 / exposure)
        except Xi_error:
            pass
    
    def set_roi(self, roi : list) -> None:
        # todo: needs implementation using Ximea APIs
        self.roi = roi

    def get_roi(self) -> list:
        return self.roi