from pymmcore_plus import CMMCorePlus
import cv2
import numpy as np
from dataclasses import replace
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import (
    ICamera,
    NumberParameter,
    ListParameter,
)
from typing import Union, Any
from sys import platform


class MMC(ICamera):
    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """MMC-Core VideoCapture wrapper.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
        self.__capture = CMMCorePlus.instance()

        """"""

        moduleName, deviceName = deviceID.split(" ")
        self.__capture.loadDevice(name, moduleName, deviceName)
        self.__capture.initializeDevice(name)
        self.__capture.setCameraDevice(name)

        # read MMC-Core parameters
        width = int(self.__capture.getImageWidth())
        height = int(self.__capture.getImageHeight())

        # initialize region of interest
        # steps for height, width and offsets
        # are by default 1. We leave them as such
        sensorShape = ROI(offset_x=0, offset_y=0, height=height, width=width)

        parameters = {}
        properties = self.__capture.getDevicePropertyNames(name)

        for property in properties:
            if not self.__capture.isPropertyReadOnly(name, property):
                if property == "Exposure":
                    parameters[property] = NumberParameter(
                        value=float(self.__capture.getProperty(name, property)),
                        valueLimits=(
                            self.__capture.getPropertyLowerLimit(name, property),
                            self.__capture.getPropertyUpperLimit(name, property),
                        ),
                        unit="ms",
                        editable=True,
                    )

                elif len(self.__capture.getAllowedPropertyValues(name, property)) != 0:
                    parameters[property] = ListParameter(
                        value=self.__capture.getProperty(name, property),
                        options=list(
                            self.__capture.getAllowedPropertyValues(name, property)
                        ),
                        editable=True,
                    )

                elif self.__capture.hasPropertyLimits(name, property):
                    try:
                        parameters[property] = NumberParameter(
                            value=float(self.__capture.getProperty(name, property)),
                            valueLimits=(
                                self.__capture.getPropertyLowerLimit(name, property),
                                self.__capture.getPropertyUpperLimit(name, property),
                            ),
                            unit="",
                            editable=True,
                        )
                    except Exception as e:
                        pass

        super().__init__(name, deviceID, parameters, sensorShape)

    def setAcquisitionStatus(self, started: bool) -> None:
        print(self.__capture.isSequenceRunning())
        if started == True and self.__capture.isSequenceRunning() != True:
            self.__capture.startContinuousSequenceAcquisition()
        elif started == False:
            self.__capture.stopSequenceAcquisition()

    def grabFrame(self) -> np.ndarray:
        while self.__capture.getRemainingImageCount() == 0:
            pass
        rawImg = self.__capture.getLastImage()
        img = self.__capture.fixImage(rawImg)
        return img

    def changeParameter(self, name: str, value: Any) -> None:
        self.setAcquisitionStatus(False)
        self.__capture.waitForDevice(self.name)
        if name == "Exposure":
            self.__capture.setExposure(self.name, value)

        elif name in self.parameters.keys():
            self.__capture.setProperty(self.name, name, value)

        else:
            raise ValueError(f'Unrecognized value "{value}" for parameter "{name}"')

        self.__capture.waitForDevice(self.name)
        self.setAcquisitionStatus(True)

    def changeROI(self, newROI: ROI):
        self.setAcquisitionStatus(False)
        self.__capture.setROI(
            self.name, newROI.offset_x, newROI.offset_y, newROI.width, newROI.height
        )
        self.__capture.waitForDevice(self.name)
        self.setAcquisitionStatus(True)
        if newROI <= self.fullShape:
            self.roiShape = newROI

    def close(self) -> None:
        self.setAcquisitionStatus(False)
        self.__capture.unloadDevice(self.name)
