try:
    # We need a try-except structure because
    # Ximea Python APIs need to be installed manually.
    # See https://www.ximea.com/support/wiki/apis/Python
    import numpy as np
    from time import time
    from copy import copy
    from contextlib import contextmanager
    from ximea.xiapi import Camera as XiCam, Image as XiImg, Xi_error as XiError
    from napari_live_recording_rework.devices.interface import ICamera
    from napari_live_recording_rework.widgets import WidgetEnum, Timer
    from napari_live_recording_rework.common import ROI, ONE_SECOND_IN_MS
    from dataclasses import dataclass
    from PyQt5.QtCore import QObject
    from typing import Union

    class Ximea(ICamera):

        @dataclass(frozen=True)
        class XimeaPixelFormat:
            data = {
                "8-bit gray" : "XI_MONO8",
                "16-bit gray" : "XI_MONO16"
            }
        
        @dataclass(frozen=True)
        class XimeaCounterSelector:
            data = {
                "Transfered frames" : "XI_CNT_SEL_TRANSPORT_TRANSFERRED_FRAMES",
                "Transport skipped frames" : "XI_CNT_SEL_TRANSPORT_SKIPPED_FRAMES",
                "API skipped frames" : "XI_CNT_SEL_API_SKIPPED_FRAMES",
                "Frames missed due to overlap" : "XI_CNT_SEL_FRAME_MISSED_TRIGGER_DUETO_OVERLAP",
                "Frames missed due to overflow" : "XI_CNT_SEL_FRAME_MISSED_TRIGGER_DUETO_FRAME_BUFFER_OVR",
                "Frame buffer overflow" : "XI_CNT_SEL_FRAME_BUFFER_OVERFLOW"
            }
        
        MAX_FRAME_COUNT = 10

        def __init__(self, name: str, deviceID: Union[str, int]) -> None:
            QObject.__init__(self)

            self.__camera = XiCam()
            self.__img = XiImg()

            self.__frameCounter = 0
            self.__startTime = 0

            try:
                deviceID = int(deviceID)
                self.__camera.dev_id = deviceID
                self.__camera.open_device()
            except ValueError:
                self.__camera.open_device_by_SN(deviceID)

            height = self.__camera.get_height()
            width = self.__camera.get_width()
            minExp, maxExp = self.__camera.get_exposure_minimum(), (ONE_SECOND_IN_MS/10)*1e3
            startExp = int(maxExp/10)

            self.__camera.set_exposure(startExp)

            self.__ROI = ROI(width=width, height=height)
            self.__cntSel = "Transfered frames"

            self.parameters = {}
            self.addParameter(WidgetEnum.ComboBox, "Pixel format", "", list(self.XimeaPixelFormat.data.keys()), self.parameters)
            self.addParameter(WidgetEnum.LabeledSlider, "Exposure time", "µs", (minExp, maxExp, startExp), self.parameters)
            self.addParameter(WidgetEnum.ComboBox, "Frame counter selector", "", list(self.XimeaCounterSelector.data.keys()), self.parameters)
            self.addParameter(WidgetEnum.LineEdit, "Frame counter", "", "", self.parameters)

            super().__init__(name, deviceID, self.parameters, self.__ROI)
        
        @contextmanager
        def _camera_disabled(self):
            """Context manager to temporarily disable camera."""
            if self.__camera.get_acquisition_status():
                try:
                    self.__camera.stop_acquisition()
                    yield
                finally:
                    self.__camera.start_acquisition()
            else:
                yield
            
        def setupWidgetsForStartup(self) -> None:
            self.parameters["Frame counter"].value = str(0)
            self.parameters["Frame counter"].isEnabled = False
        
        def connectSignals(self) -> None:
            self.parameters["Exposure time"].signals["valueChanged"].connect(self._updateExposure)
            self.parameters["Pixel format"].signals["currentTextChanged"].connect(self._updateFormat)
            self.parameters["Frame counter selector"].signals["currentTextChanged"].connect(self._updateCounterSelection)
            self.recordHandling.signals["liveRequested"].connect(lambda enabled: self._updateAcquisitionStatus(enabled))

        def grabFrame(self) -> np.array:
            try:
                self.__camera.get_image(self.__img)
                data = self.__img.get_image_data_numpy()
                self.__frameCounter += 1
                if self.__frameCounter == self.MAX_FRAME_COUNT:
                    self._updateFrameCounter()
            except XiError:
                data = None
            return data
        
        def changeROI(self, newROI: ROI):
            with self._camera_disabled():
                try:
                    self.__camera.set_width(newROI.width)
                    self.__camera.set_height(newROI.height)
                    self.__camera.set_offsetX(newROI.offset_x)
                    self.__camera.set_offsetY(newROI.offset_x)
                    self.__ROI = copy(newROI)
                except XiError:
                    # to properly update the Ximea ROI
                    # first set the height and width
                    # make sure that a minimum step is calculated
                    width_incr = self.__camera.get_width_increment()
                    height_incr = self.__camera.get_height_increment()
                    self.__ROI.width = (round(newROI.width/width_incr)*width_incr if (newROI.width % width_incr) != 0 else newROI.width)
                    self.__ROI.height = (round(newROI.height/height_incr)*height_incr if (newROI.height % height_incr) != 0 else newROI.height)

                    self.__camera.set_width(self.__ROI.width)
                    self.__camera.set_height(self.__ROI.height)

                    # now we can properly update offset X and Y
                    offx_incr  = self.__camera.get_offsetX_increment()
                    offy_incr  = self.__camera.get_offsetY_increment()
                    self.__ROI.offset_x = (round(newROI.offset_x / offx_incr)*offx_incr if (newROI.offset_x % offx_incr) != 0 else newROI.offset_x)
                    self.__ROI.offset_y = (round(newROI.offset_y / offy_incr)*offy_incr if (newROI.offset_y % offy_incr) != 0 else newROI.offset_y)

                    self.__camera.set_offsetX(self.__ROI.offset_x)
                    self.__camera.set_offsetY(self.__ROI.offset_y)

                    # we also update the single increment steps for each value of the ROI
                    self.__ROI.ofs_x_step  = offx_incr
                    self.__ROI.ofs_y_step  = offy_incr
                    self.__ROI.width_step  = width_incr
                    self.__ROI.height_step = height_incr 
        
        def cameraInfo(self) -> list[str]:
            # todo: implement
            return []
        
        def close(self) -> None:
            if self.__camera.get_acquisition_status():
                self.__camera.stop_acquisition()
            self.__camera.close_device()
        
        def _updateAcquisitionStatus(self, enabled: bool) -> None:
            if enabled:
                self.__camera.start_acquisition()
                self.__startTime = time()
                # we need to do this to make sure that the counter works at startup
                self.__camera.set_counter_selector(self.XimeaCounterSelector.data[self.__cntSel])
            else:
                self.__camera.stop_acquisition()

        def _updateExposure(self, exposure: str) -> None:
            if self.__camera.get_acquisition_status():
                self.__camera.set_exposure_direct(int(exposure))
            else:
                self.__camera.set_exposure(int(exposure))
        
        def _updateFormat(self, format: str) -> None:
            with self._camera_disabled():
                self.__camera.set_imgdataformat(self.XimeaPixelFormat.data[format])
        
        def _updateCounterSelection(self, counter: str) -> None:
            with self._camera_disabled():
                self.__camera.set_counter_selector(self.XimeaCounterSelector.data[counter])
                self.__cntSel = counter
                self.parameters["Frame counter"].value = str(0)
        
        def _updateFrameCounter(self) -> None:
            self.parameters["Frame counter"].value = str(round(self.__frameCounter / (time() - self.__startTime), 2))
            self.__frameCounter = 0
            self.__startTime = time()
except ImportError:
    pass