import numpy as np
import microscope
from microscope.abc import Camera
from typing import Union, Any
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import (
    ICamera,
    NumberParameter,
    ListParameter
)
import queue
import importlib


class Microscope(ICamera):

     index_dict = {}

     def __init__(self, name: str, deviceID: Union[str, int]) -> None:
          """ VideoCapture from Python Microscope.
          Args:
               name (str): user-defined camera name.
               deviceID (Union[str, int]): camera identifier.
          """
          # received ID will be the module of the camera and camera class name
          # in the format of "<module> <class_name>"

          self.__module, cls = deviceID.split()

          import_str = "microscope."
          if self.__module != "simulators":
               import_str += "cameras."
          import_str += self.__module

          package = importlib.import_module(import_str)
          driver = getattr(package, cls)
          self.__camera: Camera = driver()

          cam_roi: microscope.ROI = self.__camera.get_roi()
          cam_binning: microscope.Binning = self.__camera.get_binning()

          sensorShape = ROI(offset_x=0, offset_y=0, height=cam_roi.height // cam_binning.v, width=cam_roi.width // cam_binning.h)

          parameters = {}

          for key, _ in self.__camera.get_all_settings().items():
               if key == "display image number":
                    # TODO: skipping;
                    # this causes errors
                    # on microscope side
                    self.__camera.set_setting("display image number", False)
                    continue
               if self.__camera.describe_setting(key)['type'] == 'enum':
                    # create dictionary for combobox
                    test_keys = ([item[1] for item in self.__camera.describe_setting(key)['values']])
                    test_value = ([item[0] for item in self.__camera.describe_setting(key)['values']])
                    temp_dic = dict(zip(test_keys, test_value))
                    self.index_dict[key] = temp_dic
                    parameters[key] = ListParameter(value=list(self.index_dict[key].keys())[0],
                                                  options=list(self.index_dict[key].keys()),
                                                  editable=not (self.__camera.describe_setting(key)['readonly']))

               elif self.__camera.describe_setting(key)['type'] == 'int':
                    min_value = self.__camera.describe_setting(key)['values'][0]
                    max_value = self.__camera.describe_setting(key)['values'][1]
                    parameters[key] = NumberParameter(value= self.__camera.describe_setting(key)['values'][0],
                                                       valueLimits = (min_value, max_value),
                                                       unit = "unknown unit",
                                                       editable = not (self.__camera.describe_setting(key)['readonly']))

               elif self.__camera.describe_setting(key)['type'] == 'bool':
                    parameters[key] = ListParameter(value=self.__camera.describe_setting(key)['values'],
                                                  options=list(('True', 'False')),
                                                  editable=not (self.__camera.describe_setting(key)['readonly']))
          # initialize exposure time at 10 ms
          self.__camera.set_exposure_time(10e-3)
          if 'Exposure' not in parameters:
               parameters['Exposure time'] = NumberParameter(value=self.__camera.get_exposure_time(),
                                                       # min and max values were determined by try and error since they are not included in describe_settings() for simulated camera
                                                       valueLimits=(2e-3, 100e-3),  unit="s",
                                                       editable=True)

          self.__buffer = queue.Queue()
          self.__camera.set_client(self.__buffer)
          
          super().__init__(name, deviceID, parameters, sensorShape)
 
     def setAcquisitionStatus(self, started: bool) -> None: 
          if started:
               self.__camera.enable()
          else:
               self.__camera.disable()

     def grabFrame(self) -> np.ndarray:
          # TODO: microscope works
          # by calling the trigger() method
          # for each frame to be acquired;
          # can this be done in a more efficient way?
          self.__camera.trigger()
          img = self.__buffer.get()
          return img


     def changeParameter(self, name: str, value: Any) -> None:
          if name == "Exposure time":
               self.__camera.set_exposure_time(float(value))
          elif name == "transform":          # parameter type = 'enum'
               '''(False, False, False): 0, (False, False, True): 1, (False, True, False): 2, (False, True, True): 3,
               (True, False, False): 4,(True, False, True): 5, (True, True, False): 6, (True, True, True): 7'''
               value_tuple = eval((value))         # converts the datatype of value from str to tuple
               self.__camera.set_transform(value_tuple)    # set_transform method does not work with index like the other enum parameter
          else:
               # the enum microscope settings behave using index instead of the actual value;
               # we perform a preventive checks on the parameter type to avoid errors
               paramType = type(self.parameters[name])
               if paramType == ListParameter:
                    if self.__camera.describe_setting(name)['type'] == 'enum':
                         self.__camera.set_setting(name, self.index_dict[name][value])
                    else:
                         self.__camera.set_setting(name, value)
          self.parameters[name].value = value
          
     def changeROI(self, newROI: ROI):
          self.__camera.set_roi(microscope.ROI(newROI.offset_x, newROI.offset_y, newROI.width, newROI.height))
          self._roiShape = newROI
     
     def close(self) -> None:
          self.__camera.set_client(None)
          self.__camera.shutdown() 
