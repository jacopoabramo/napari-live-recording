import numpy as np
from microscope.device_server import device
from microscope.simulators import SimulatedCamera
import typing
from typing import Union, Any, Tuple
from sys import platform
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import (
    ICamera,
    NumberParameter,
    ListParameter
)
import queue



class SimCamera(ICamera):
#uses time.sleep() therfore the exposure values have to be entered in sec
  msExposure = {
       "1 s":  1,
        "500 ms": 5*10**(-3),
        "250 ms": 250*10**(-3),
        "125 ms": 125*10**(-3),
        "62.5 ms": 62.5*10**(-3),
        "31.3 ms": 31.3*10**(-3),
        "15.6 ms": 15.6*10**(-3), # default
        "7.8 ms": 7.8*10**(-3),
        "3.9 ms": 3.9*10**(-3),
        "2 ms": 2*10**(-3),
        "976.6 us": 976.6*10**(-6),
        "488.3 us": 488.3*10**(-6),
        "244.1 us": 244.1*10**(-6),
        "122.1 us":122.1*10**(-6)
     }
  pixelFormats = {
       "RGB" : 0, # default
        "RGBA" : 1,
        "BGR" : 2,
        "Grayscale" : 3
     }
  methods = {
     "noise": 0,
       "gradient":1,
       "sawtooth":2,
       "one gaussian":3,
       "black":4,
       "white":5  
     }
   
  def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """simulated VideoCapture PYME.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
        self.__camera = SimulatedCamera()

        self.__camera.get_all_settings()

        self.__camera.set_setting("display image number", False)
        
        #self._roi = microscope.ROI(0, 0, *sensor_shape)   
        sensorShape = ROI(offset_x=0, offset_y=0, height=self.__camera._roi.height // self.__camera._binning.v, width=self.__camera._roi.width // self.__camera._binning.h)
        '''_binning.h & _binning.v default value = 1'''
        parameters = {}
     
        parameters["Exposure time"] = ListParameter(value=self.msExposure["15.6 ms"], 
                                                        options=list(self.msExposure.keys()), 
                                                        editable=True)
        ''' 
        parameters["Exposure time"] = NumberParameter(value=10e-3,                   #use this one for slider
                                                        valueLimits=(100e-6, 1),
                                                        unit="s",
                                                        editable=True)
        '''
        parameters["Pixel format"] = ListParameter(value=self.pixelFormats["RGB"],
                                                options=list(self.pixelFormats.keys()),
                                                editable=True)
        
        self.__format = self.pixelFormats["RGB"]

        super().__init__(name, deviceID, parameters, sensorShape )

 
  def setAcquisitionStatus(self, started: bool) -> None: 
        pass
     

  def grabFrame(self) -> np.ndarray:
     buffer = queue.Queue()
     self.__camera.set_client(buffer)
     self.__camera.enable()
     self.__camera.trigger()  # acquire image
     img = buffer.get()  # retrieve image  

     if img.dtype == np.uint8:
          #assert img.dtype in (np.uint8, np.uint16)
          img =np.asarray(img / np.iinfo(img.dtype).max, dtype='float64')

     return img  

  def changeParameter(self, name: str, value: Any) -> None:
       if name == "Exposure time":
            value = (self.msExposure[value])
            self.__camera.set_exposure_time(value)
       elif name == "Pixel format":
            self.__format = self.__camera.set_setting('Pixel format', value)          
       else:
            raise ValueError(f"Unrecognized value \"{value}\" for parameter \"{name}\"")
      
  def changeROI(self, newROI: ROI):
        #newROI = ROI(offset_x, offset_y, height, width)
        #newROI.height = newROI.height // self.__camera._binning.v
        #newROI.width= newROI.width // self.__camera._binning.h
        self.__camera._set_roi(newROI)
        #return newROI
  
  def close(self) -> None:
        self.__camera._do_shutdown()