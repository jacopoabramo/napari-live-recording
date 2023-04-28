from pymmcore_plus import CMMCorePlus
import cv2
import numpy as np
from dataclasses import replace
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import (
    ICamera,
    NumberParameter,
    ListParameter
)
from typing import Union, Any
from sys import platform

class MMC(ICamera):



    '''pixelFormats = {
            "RGB" : None, # standard format of mmc is RGB
            "RGBA" : cv2.COLOR_RGB2RGBA,
            "BGR" : cv2.COLOR_RGB2BGR,
            "Grayscale" : cv2.COLOR_RGB2GRAY
        }'''




    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """MMC-Core VideoCapture wrapper.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
        self.__capture = CMMCorePlus.instance()

        ''''''

        moduleName, deviceName = deviceID.split(" ")#User has to input the moduleName and deviceName as defined in the cfg file separated by space       
        self.__capture.loadDevice(name, moduleName, deviceName)#arguments label, moduleName (the name of the device adapter module (short name, not full file name)), deviceName	the name of the device. The name must correspond to one of the names recognized by the specific plugin library.
        self.__capture.initializeAllDevices()
        self.__capture.setCameraDevice(name)



        '''self.pixelFormats = dict(zip(self.__capture.getAllowedPropertyValues(name,'PixelType'),
            self.__capture.getAllowedPropertyValues(name,'PixelType')))'''
        
        # read MMC-Core parameters
        width = int(self.__capture.getImageWidth())
        height = int(self.__capture.getImageHeight())
        #defaultPixelType = self.__capture.getProperty(name, "PixelType")

        # initialize region of interest
        # steps for height, width and offsets
        # are by default 1. We leave them as such
        sensorShape = ROI(offset_x=0, offset_y=0, height=height, width=width)
        
        parameters = {}
        properties = self.__capture.getDevicePropertyNames(name)

        '''parameters["Exposure time"] = NumberParameter(value=1.0,
                                                        valueLimits=(100e-3, 1000),
                                                        unit="ms",
                                                        editable=True)'''
        '''parameters["Pixel type"] = ListParameter(value=self.pixelFormats[defaultPixelType],
                                                options=list(self.pixelFormats.keys()),
                                                editable=True)'''
        
        for property in properties:
            if not self.__capture.isPropertyReadOnly(name, property):
                if property == "Exposure":
                    parameters[property] = NumberParameter(value = float(self.__capture.getProperty(name, property)),
                                    valueLimits=(self.__capture.getPropertyLowerLimit(name, property), self.__capture.getPropertyUpperLimit(name, property)),
                                unit="ms",
                                editable=True)

                elif len(self.__capture.getAllowedPropertyValues(name, property)) !=0:
                    parameters[property] = ListParameter(value = self.__capture.getProperty(name, property),
                                                         options= list(self.__capture.getAllowedPropertyValues(name, property)),
                                                         editable=True)
                    
                elif self.__capture.hasPropertyLimits(name, property):
                    try:
                        parameters[property] = NumberParameter(value = float(self.__capture.getProperty(name, property)),
                                                         valueLimits=(self.__capture.getPropertyLowerLimit(name, property), self.__capture.getPropertyUpperLimit(name, property)),
                                                        unit="",
                                                        editable=True)
                    except Exception as e:
                        print(str(e))
        

        #self.__format = self.pixelFormats[defaultPixelType]
        super().__init__(name, deviceID, parameters, sensorShape)
    
    def setAcquisitionStatus(self, started: bool) -> None:
        print(self.__capture.isSequenceRunning())
        if started == True and self.__capture.isSequenceRunning() != True:
            self.__capture.startContinuousSequenceAcquisition()
        elif started==False:
            self.__capture.stopSequenceAcquisition()
       
    
    def grabFrame(self) -> np.ndarray:
        while self.__capture.getRemainingImageCount()==0:
            pass
        rawImg = self.__capture.getLastImage()
        img = self.__capture.fixImage(rawImg)
        y, h = self.roiShape.offset_y, self.roiShape.offset_y + self.roiShape.height
        x, w = self.roiShape.offset_x, self.roiShape.offset_x + self.roiShape.width
        img = img[y:h, x:w]
        return img
    
    def changeParameter(self, name: str, value: Any) -> None:
        self.setAcquisitionStatus(False)
        self.__capture.waitForDevice(self.name)
        if name == "Exposure":
            self.__capture.setExposure(self.name, value)

        elif name in self.parameters.keys():
            self.__capture.setProperty(self.name, name, value)

        else:
            raise ValueError(f"Unrecognized value \"{value}\" for parameter \"{name}\"")
        
        self.__capture.waitForDevice(self.name)
        self.setAcquisitionStatus(True)
    
    def changeROI(self, newROI: ROI):
        if newROI <= self.fullShape:
            self.roiShape = newROI
    
    def close(self) -> None:
        self.setAcquisitionStatus(False)
        self.__capture.unloadDevice(self.name)
        pass
        #self.__capture.release()