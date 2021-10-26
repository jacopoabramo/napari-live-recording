from .ICamera import ICamera
from platform import system
import cv2
import numpy as np

CAM_OPENCV = "Default Camera (OpenCV)"

class CameraOpenCV(ICamera):
    """Generic OpenCV camera handler

    :param ICamera: [description]
    :type ICamera: [type]
    """

    def __init__(self) -> None:
        super().__init__()
        self.camera_idx = 0
        self.camera_api = cv2.CAP_ANY
        self.camera = None
        self.camera_name = CAM_OPENCV
        self.roi = [500, 500]

        # Windows platforms support discrete exposure times
        # These are mapped using a dictionary
        self.exposure_dict = {
            "1 s"      :  0,
            "500 ms"   : -1,
            "250 ms"   : -2,
            "125 ms"   : -3,
            "62.5 ms"  : -4,
            "31.3 ms"  : -5,
            "15.6 ms"  : -6,
            "7.8 ms"   : -7,
            "3.9 ms"   : -8,
            "2 ms"     : -9,
            "976.6 us" : -10,
            "488.3 us" : -11,
            "244.1 us" : -12,
            "122.1 us" : -13
        }

    def __del__(self) -> None:
        if self.camera is not None:
            self.camera.release()
    
    def __str__(self) -> str:
        return CAM_OPENCV
    
    def open_device(self) -> bool:
        if self.camera is None:
            self.camera = cv2.VideoCapture(self.camera_idx, self.camera_api)
            return self.camera.isOpened()
        return self.camera.open(self.camera_idx, self.camera_api)
    
    def close_device(self) -> None:
        self.camera.release()
    
    def capture_image(self) -> np.array:
        _ , img = self.camera.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.waitKey(1)
        return img

    def set_exposure(self, exposure) -> None:
        if system() == "Windows":
            exposure = self.exposure_dict[exposure]
        self.camera.set(cv2.CAP_PROP_EXPOSURE, exposure)
    
    def set_roi(self, roi : list) -> None:
        # todo: implement actual ROI
        self.roi = roi
    
    def get_roi(self) -> list:
        return self.roi

    def get_acquisition(self) -> bool:
        return self.camera.isOpened()
    
    def set_acquisition(self, is_enabled) -> None:
        if is_enabled:
            self.camera = cv2.VideoCapture(self.camera_idx, self.camera_api)
        else:
            self.camera.release()