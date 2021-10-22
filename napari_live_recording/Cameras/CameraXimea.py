from .ICamera import ICamera

# Ximea camera support only provided by downloading the Ximea Software package
# see https://www.ximea.com/support/wiki/apis/APIs for more informations
from ximea.xiapi import Camera as XiCamera, Xi_error
from ximea.xiapi import Image as XiImage
from time import sleep
import numpy as np

CAM_XIMEA = "Ximea xiB-64"



CONVERSION_FACTOR = 1000

class CameraXimea(ICamera):

    def __init__(self) -> None:
        super().__init__()
        self.camera = XiCamera()
        self.image = XiImage()
        self.camera_name = CAM_XIMEA
        self.roi = [0, 0, 1280, 864]
        self.exposure = 10 * CONVERSION_FACTOR    # ms, default exposure
        self.sleep_time = 10 / CONVERSION_FACTOR  # ms
    
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
            self.camera.set_exposure(self.exposure)
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
        # sleep(self.sleep_time)
        return data

    def set_exposure(self, exposure) -> None:
        try:
            self.exposure = exposure * CONVERSION_FACTOR
            self.sleep_time = exposure / CONVERSION_FACTOR
            self.camera.set_exposure(self.exposure)
        except Xi_error:
            pass
    
    def set_roi(self, roi : list) -> None:
        print("Setting new ROI:")
        print(f"Offset X: {roi[0]} - Offset Y: {roi[1]}")
        print(f"Width: {roi[2]} - Height: {roi[3]}")
        if self.roi[0] != roi[0]:
            self.camera.set_offsetX(roi[0])
        if self.roi[1] != roi[1]:
            self.camera.set_offsetY(roi[1])
        if self.roi[2] != roi[2]:
            self.camera.set_width(roi[2])
        if self.roi[3] != roi[3]:
            self.camera.set_height(roi[3])
        self.roi = roi

    def get_roi(self) -> list:
        return self.roi