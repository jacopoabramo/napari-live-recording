import cv2
from interface import Camera
from typing import Union
from common import ROI
from widgets.widgets import (
    ComboBox,
    SpinBox, 
    DoubleSpinBox, 
    LabeledSlider, 
    LineEdit
)

class OpenCVCamera(Camera):
    __exposureDict = {
        "1 s":  0,
        "500 ms": -1,
        "250 ms": -2,
        "125 ms": -3,
        "62.5 ms": -4,
        "31.3 ms": -5,
        "15.6 ms": -6,
        "7.8 ms": -7,
        "3.9 ms": -8,
        "2 ms": -9,
        "976.6 us": -10,
        "488.3 us": -11,
        "244.1 us": -12,
        "122.1 us": -13
    }

    __pixelFormats = {
        "RGB" : cv2.COLOR_BGR2RGB, # default
        "RGBA" : cv2.COLOR_BGR2RGBA,
        "BGR" : None,
        "Grayscale" : cv2.COLOR_RGB2GRAY 
    }

    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """OpenCV VideoCapture wrapper.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera ID.
        """
        self.camera = cv2.VideoCapture(deviceID, cv2.CAP_ANY)
        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sensorShape = ROI(0, 0, height, width)
        
        paramDict = {}
        self.addParameter("ComboBox", "Exposure time", "", list(self.exposureDict.keys()), paramDict)

        super().__init__(name, deviceID, paramDict, sensorShape)