# Creating a camera interface

The documentation is work in progress. For a first glance on how the Python interface looks like, please refer to the OpenCV grabber implementation in `napari-live-recording/control/devices/opencv.py`:

```py
import cv2
import numpy as np
from napari_live_recording.common import ROI, ColorType
from napari_live_recording.control.devices.interface import (
    ICamera,
    NumberParameter,
    ListParameter
)
from typing import Union, Any
from sys import platform

class OpenCV(ICamera):

    msExposure = {
        "1 s":  0,
        "500 ms": -1,
        "250 ms": -2,
        "125 ms": -3,
        "62.5 ms": -4,
        "31.3 ms": -5,
        "15.6 ms": -6, # default
        "7.8 ms": -7,
        "3.9 ms": -8,
        "2 ms": -9,
        "976.6 us": -10,
        "488.3 us": -11,
        "244.1 us": -12,
        "122.1 us": -13
    }

    pixelFormats = {
        "RGB" : (cv2.COLOR_BGR2RGB, ColorType.RGB), # default
        "RGBA" : (cv2.COLOR_BGR2RGBA, ColorType.RGB),
        "BGR" : (None, ColorType.RGB),
        "Grayscale" : (cv2.COLOR_RGB2GRAY, ColorType.GRAYLEVEL)
    }

    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """OpenCV VideoCapture wrapper.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
        self.__capture = cv2.VideoCapture(int(deviceID))

        # read OpenCV parameters
        width = int(self.__capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.__capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # initialize region of interest
        # steps for height, width and offsets
        # are by default 1. We leave them as such
        sensorShape = ROI(offset_x=0, offset_y=0, height=height, width=width)
        
        parameters = {}

        # exposure time in OpenCV is treated differently on Windows, 
        # as exposure times may only have a finite set of values
        if platform.startswith("win"):
            parameters["Exposure time"] = ListParameter(value=self.msExposure["15.6 ms"], 
                                                        options=list(self.msExposure.keys()), 
                                                        editable=True)
        else:
            parameters["Exposure time"] = NumberParameter(value=10e-3,
                                                        valueLimits=(100e-6, 1),
                                                        unit="s",
                                                        editable=True)
        parameters["Pixel format"] = ListParameter(value=self.pixelFormats["RGB"],
                                                options=list(self.pixelFormats.keys()),
                                                editable=True)

        super().__init__(name, deviceID, parameters, sensorShape)
        format = self.pixelFormats["RGB"]
        self.__format = format[0]
        self._colorType = format[1]
    
    def setAcquisitionStatus(self, started: bool) -> None:
        pass
    
    def grabFrame(self) -> np.ndarray:
        _, img = self.__capture.read()
        y, h = self.roiShape.offset_y, self.roiShape.offset_y + self.roiShape.height
        x, w = self.roiShape.offset_x, self.roiShape.offset_x + self.roiShape.width
        img = img[y:h, x:w]
        img = (cv2.cvtColor(img, self.__format) if self.__format is not None else img)
        return img
    
    def changeParameter(self, name: str, value: Any) -> None:
        if name == "Exposure time":
            value = (self.msExposure[value] if platform.startswith("win") else value)
            self.__capture.set(cv2.CAP_PROP_EXPOSURE, value)
        elif name == "Pixel format":
            newFormat = self.pixelFormats[value]
            self.__format = newFormat[0]
            self._colorType = newFormat[1]
        else:
            raise ValueError(f"Unrecognized value \"{value}\" for parameter \"{name}\"")
    
    def changeROI(self, newROI: ROI):
        if newROI <= self.fullShape:
            self.roiShape = newROI
    
    def close(self) -> None:
        self.__capture.release()
```

