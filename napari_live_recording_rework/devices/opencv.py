import cv2
import numpy as np
from interface import Camera
from typing import Union
from common import ROI
from widgets.widgets import (
    WidgetEnum
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
        self.__capture = cv2.VideoCapture(deviceID, cv2.CAP_ANY)
        
        # read OpenCV parameters
        width = int(self.__capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.__capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.__exposure = int(self.__capture.get(cv2.CAP_PROP_EXPOSURE))
        
        # initialize device local properties
        self.__ROI = ROI(0, 0, height, width)
        self.__format = self.__pixelFormats["RGB"]
        self.__frameCounter = 0
        
        paramDict = {}
        self.addParameter(WidgetEnum.ComboBox, "Exposure time", "", list(self.__exposureDict.keys()), paramDict)
        self.addParameter(WidgetEnum.ComboBox, "Pixel format", "", list(self.__pixelFormats.keys()), paramDict)
        self.addParameter(WidgetEnum.LineEdit, "Frame rate", "FPS", 0)
        
        # call Camera.__init__ after initializing all parameters in paramDict
        super().__init__(name, deviceID, paramDict, self.__ROI)

    def setupWidgetsForStartup(self) -> None:
        self.parameters["Exposure time"].value = abs(self.__exposure)
        self.parameters["Frame rate"].isEnabled = False
    
    def connectSignals(self) -> None:
        self.parameters["Exposure time"].signals["currentTextChanged"].connect(self._updateExposure)
        self.parameters["Pixel format"].signals["currentTextChanged"].connect(self._updateFormat)

    def grabFrame(self) -> np.array:
        _, img = self.__capture.read()
        y, h = self.__ROI.offset_y, self.__ROI.offset_y + self.__ROI.height
        x, w = self.__ROI.offset_x, self.__ROI.offset_x + self.__ROI.width
        img = img[y:h, x:w]
        self.__frameCounter += 1
        return (cv2.cvtColor(img, self.__format) if self.__format is not None else img)
    
    def cameraInfo(self) -> list[str]:
        # todo: implement
        return []
    
    def closeDevice(self) -> None:
        self.__capture.release()

    def _updateExposure(self, exposure: str) -> None:
        self.__capture.set(cv2.CAP_PROP_EXPOSURE, self.__exposureDict[exposure])
    
    def _updateFormat(self, format: str):
        self.__format = self.__pixelFormats[format]