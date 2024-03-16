import numpy as np
from contextlib import contextmanager
from pymmcore_plus import CMMCorePlus
from pymmcore_widgets._device_property_table import DevicePropertyTable
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import ICamera
from typing import Union, Any


class MicroManager(ICamera):
    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """MMC-Core VideoCapture wrapper.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
        self.__capture = CMMCorePlus.instance()
        moduleName, deviceName = deviceID.split(" ")
        self.__capture.loadDevice(name, moduleName, deviceName)
        self.__capture.initializeDevice(name)
        self.__capture.setCameraDevice(name)
        self.__capture.initializeCircularBuffer()
        self.name = name
        self.settingsWidget = DevicePropertyTable()
        self.settingsWidget.filterDevices("camera", include_read_only=False)

        # read MMC-Core parameters
        width = int(self.__capture.getImageWidth())
        height = int(self.__capture.getImageHeight())

        # initialize region of interest
        # steps for height, width and offsets
        # are by default 1. We leave them as such
        sensorShape = ROI(offset_x=0, offset_y=0, height=height, width=width)

        parameters = {}

        super().__init__(name, deviceID, parameters, sensorShape)

    def setAcquisitionStatus(self, started: bool) -> None:
        if started == True and self.__capture.isSequenceRunning() != True:
            self.__capture.startContinuousSequenceAcquisition()
        elif started == False:
            self.__capture.stopSequenceAcquisition()

    def grabFrame(self) -> np.ndarray:
        while self.__capture.getRemainingImageCount() == 0:
            pass
        try:
            rawImg = self.__capture.getLastImage()
            img = self.__capture.fixImage(rawImg)
            return img
        except:
            pass

    def changeParameter(self, name: str, value: Any) -> None:
        # parameters handled via a different widget
        pass

    def changeROI(self, newROI: ROI):
        try:
            with self.acquisitionSuspended():
                self.__capture.setROI(
                    self.name,
                    newROI.offset_x,
                    newROI.offset_y,
                    newROI.width,
                    newROI.height,
                )
            if newROI <= self.fullShape:
                self.roiShape = newROI
        except Exception as e:
            print("ROI", e)

    def close(self) -> None:
        if self.__capture.isSequenceRunning():
            self.setAcquisitionStatus(False)
        self.__capture.unloadDevice(self.name)

    @contextmanager
    def acquisitionSuspended(self):
        if self.__capture.isSequenceRunning():
            try:
                self.setAcquisitionStatus(False)
                yield
            finally:
                self.setAcquisitionStatus(True)
        else:
            yield
