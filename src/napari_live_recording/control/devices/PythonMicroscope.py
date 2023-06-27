#%%
import numpy as np
from microscope.device_server import device
from microscope.simulators import SimulatedCamera, _ImageGenerator
from microscope.abc import Camera
import microscope
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
import importlib
import ximea
import logging
#from microscope.cameras.pvcam import PVCamera


class PythonMicroscope(ICamera):
  #%%
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
  temp_dic={}
  dic = {}  

  Cameras = [
       'microscope.cameras.pvcam',
       'microscope.cameras.andorsdk3',
       'microscope.cameras.atmcd',
       'microscope.cameras.ximea'
          ]  
  CamModul = []
 
  def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """ VideoCapture PYME.
        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
          # received ID will be the module of the camera and camera class name
          # in the format of "<module> <class_name>"
        module, cls = tuple(deviceID.split())
        
        import_str = "microscope."
        if module != "simulators":
             import_str += "cameras."
        import_str += module

        package = importlib.import_module(import_str)
        driver = getattr(package, cls)
        self.__camera: Camera = driver()

        sensorShape = ROI(offset_x=0, offset_y=0, height=self.__camera._roi.height // self.__camera._binning.v, width=self.__camera._roi.width // self.__camera._binning.h)
        '''_binning.h & _binning.v default value = 1'''

        parameters = {}
        

        for key, values in self.__camera.get_all_settings().items():
          
          describe = self.__camera.describe_setting(key)
        
          if key == 'roi':
               roi = values  
          
                      
          elif self.__camera.describe_setting(key)['type'] == 'enum' :
              
              #create dictionary for combobox
              test_keys = ([item[1] for item in self.__camera.describe_setting(key)['values']])
              test_value = ([item[0] for item in self.__camera.describe_setting(key)['values']])
              temp_dic = dict(zip(test_keys, test_value))
              self.dic[key] = temp_dic

              parameters[key] = ListParameter(value= values, 
                                             options= list(self.dic[key].keys()), 
                                             editable= not(self.__camera.describe_setting(key)['readonly']))
          
                         
          elif self.__camera.describe_setting(key)['type'] == 'int':
               min_value = self.__camera.describe_setting(key)['values'][0]
               max_value = self.__camera.describe_setting(key)['values'][1]
               parameters[key] = NumberParameter(value=self.__camera.describe_setting(key)['values'][0],                   
                                                  valueLimits=(min_value, max_value),  unit="unknown unit",
                                                  editable= not(self.__camera.describe_setting(key)['readonly']))    
                  
          elif self.__camera.describe_setting(key)['type'] == 'bool':
               parameters[key] = ListParameter(value=self.__camera.describe_setting(key)['values'], 
                                                       options=list(('True', 'False')), 
                                                       editable= not(self.__camera.describe_setting(key)['readonly']))
          '''
          else:
               parameters[key] = ListParameter(value= (self.__camera.describe_setting(key)['values']), 
                                                       options=list(describe['values']), 
                                                       editable= not(self.__camera.describe_setting(key)['readonly']))
          '''
        if 'Exposure' not in parameters:
             parameters['Exposure time'] = NumberParameter(value= self.__camera.get_exposure_time(), 
                                                            valueLimits=(2*10**(-3), 100*10**(-3)),  unit="s",     #min and max values were determined by try and error since they are not included in describe_settings()
                                                            editable=True)

        super().__init__(name, deviceID, parameters, sensorShape)

 
  def setAcquisitionStatus(self, started: bool) -> None: 
        pass
     

  def grabFrame(self) -> np.ndarray:
     buffer = queue.Queue()
     self.__camera.set_client(buffer)
     self.__camera.enable()
     #self.__camera.trigger()  # acquire image

     self.__camera._acquiring = True
     self.__camera._triggered = 1
     self.__camera._fetch_data() # acquire image'''

     img = buffer.get()  # retrieve image'''  

     return img  

  def changeParameter(self, name: str, value: Any) -> None:
       #self.ModuleComboBox.value[0] == "Simulated Camera": #checkes which camera is choosen in the ui
          if name == "Exposure time":
               #value = (self.msExposure[value])
               self.__camera.set_exposure_time(float(value))
          
          elif name == "transform":        # parameter type = 'enum'
               '''(False, False, False): 0, (False, False, True): 1, (False, True, False): 2, (False, True, True): 3,
               (True, False, False): 4,(True, False, True): 5, (True, True, False): 6, (True, True, True): 7'''
               value = eval((value))       #converts the datatype of value from str to tuple
               self.__camera.set_transform(value)    #set_transform methode does not work with index like the other enum parameter
               
          elif name == "a_setting":
               self.__camera.set_setting(name, value)

          elif name== 'display image number':
               self.__camera._image_generator.enable_numbering(value)
               
          elif name == "image pattern":    # parameter type = 'enum'
               '''(0, 'noise'), (1, 'gradient'), (2, 'sawtooth'), (3, 'one_gaussian'), (4, 'black'), (5, 'white')'''
               value = self.dic[name][value]
               self.__camera._image_generator.set_method(value)
               
          elif name ==  "image data type":      # parameter type = 'enum'
               '''(0, 'uint8'), (1, 'uint16'), (2, 'float')'''
               value = self.dic[name][value] 
               self.__camera._image_generator.set_data_type(value)
               
          elif name ==  "_error_percent":
               '''In _fetch_data an exception is raised, if a random number between 0 and 100 is less than _error_percent.
               This simulates an error condition during image acquisition.'''
               self.__camera._set_error_percent(value)

          elif name == "gain":
               self.__camera._set_gain(value)
          else:
               raise ValueError(f"Unrecognized value \"{value}\" for parameter \"{name}\"")
      #else:  real camera parameter change
      
  def changeROI(self, newROI: ROI):
        #newROI.height = newROI.height // self.__camera._binning.v
        #newROI.width= newROI.width // self.__camera._binning.h
        self.__camera._set_roi(newROI)
        
  
  def close(self) -> None:
        self.__camera._do_shutdown()