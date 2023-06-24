import numpy as np
import tifffile.tifffile as tiff
import os
from contextlib import contextmanager
from napari.qt.threading import thread_worker, FunctionWorker
from qtpy.QtCore import QThread, QObject, Signal
from napari_live_recording.common import (
    TIFF_PHOTOMETRIC_MAP,
    WriterInfo,
    FileFormat,
    RecordType,
    ROI,
)
from napari_live_recording.control.devices.interface import ICamera
from napari_live_recording.control.frame_buffer import Framebuffer
from typing import Dict, NamedTuple
from functools import partial
from time import time


class SignalCounter(QObject):
    maxCountReached = Signal()

    def __init__(self) -> None:
        self.maxCount = 0
        self.count = 0
        super().__init__()

    def increaseCounter(self):
        self.count += 1
        if self.count == self.maxCount:
            self.maxCountReached.emit()
            self.count = 0


class LocalController(NamedTuple):
    """Named tuple to wrap a camera device and the relative thread into which the device lives."""

    thread: QThread
    device: ICamera


class MainController(QObject):
    recordFinished = Signal()

    def __init__(self) -> None:
        """Main Controller class. Stores all camera objects to access live and stack recordings."""
        super().__init__()
        self.deviceControllers: Dict[str, LocalController] = {}
        self.deviceLiveBuffer: Dict[str, np.ndarray] = {}
        self.deviceRecordingBuffer: Dict[str, Framebuffer] = {}
        self.stackSize = 100
        self.liveWorker = None
        self.__isLive = False
        self.recordLoopEnabled = False
        self.recordSignalCounter = SignalCounter()
        self.recordSignalCounter.maxCountReached.connect(
            lambda: self.recordFinished.emit()
        )

    @property
    def isLive(self) -> bool:
        return self.__isLive

    @contextmanager
    def livePaused(self):
        if self.isLive:
            try:
                self.live(False)
                yield
            finally:
                self.live(True)
        else:
            yield

    def addCamera(self, cameraKey: str, camera: ICamera) -> str:
        """Adds a new device in the controller, with a thread in which the device operates."""
        thread = QThread()
        camera.moveToThread(thread)
        deviceController = LocalController(thread, camera)
        self.deviceControllers[cameraKey] = deviceController
        self.deviceControllers[cameraKey].thread.start()
        self.deviceLiveBuffer[cameraKey] = np.zeros(
            shape=camera.roiShape.pixelSizes, dtype=np.uint16
        )
        self.deviceRecordingBuffer[cameraKey] = Framebuffer(
            self.stackSize, camera=camera
        )
        self.recordSignalCounter.maxCount += 1
        return cameraKey

    def changeCameraROI(self, cameraKey: str, newROI: ROI) -> None:
        self.deviceControllers[cameraKey].device.changeROI(newROI)
        self.deviceLiveBuffer[cameraKey] = np.zeros(shape=newROI.pixelSizes)
        self.deviceRecordingBuffer[cameraKey].changeROI(newROI)

    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera device."""
        with self.livePaused():
            try:
                self.deviceControllers[cameraKey].device.close()
                self.deviceControllers[cameraKey].thread.quit()
                self.deviceControllers[cameraKey].device.deleteLater()
                self.deviceControllers[cameraKey].thread.deleteLater()
                self.recordSignalCounter.maxCount -= 1
            except RuntimeError:
                # camera already deleted
                pass

    def snap(self, cameraKey: str) -> np.ndarray:
        return self.deviceControllers[cameraKey].device.grabFrame()

    def live(self, toggle: bool) -> None:
        self.__isLive = toggle

        @thread_worker(worker_class=FunctionWorker, start_thread=False)
        def liveLoop():
            while True:
                for key in self.deviceControllers.keys():
                    self.deviceLiveBuffer[key] = np.copy(
                        self.deviceControllers[key].device.grabFrame()
                    )

        if self.isLive:
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(True)
            self.liveWorker = liveLoop()
            self.liveWorker.start()
        else:
            self.liveWorker.quit()
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(False)

    def record(self, camNames: list, writerInfo: WriterInfo) -> None:
        def closeFile(filename) -> None:
            files[filename].close()

        def closeWorkerConnection(worker: FunctionWorker) -> None:
            self.recordSignalCounter.increaseCounter()
            worker.finished.disconnect()

        def changeStackSize(newStackSize: int):
            self.stackSize = newStackSize
            for cam in camNames:
                self.deviceRecordingBuffer[cam].changeStacksize(
                    newStacksize=self.stackSize
                )

        # thread for writing frames to the buffer
        @thread_worker(worker_class=FunctionWorker, start_thread=False)
        def captureBuffer(camName: str):
            detector = self.deviceControllers[camName].device
            with detector:
                while True:
                    self.deviceRecordingBuffer[camName].addFrame(detector.grabFrame())
            # TODO start writing files only when buffer was filled once

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def fixedStackToFile(
            filename: str, camName: str, stackSize: int, writeFunc
        ) -> str:
            idx = 0
            try:
                while (idx < stackSize) and self.recordLoopEnabled:
                    writeFunc(self.deviceRecordingBuffer[camName].returnOldestFrame())
                    idx += 1

                return filename
            except:
                pass

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def timeStackToFile(
            filename: str, camName: str, acquisitionTime: float, writeFunc
        ) -> str:
            startTime = time()
            try:
                while (
                    time() - startTime <= acquisitionTime
                ) and self.recordLoopEnabled:
                    writeFunc(self.deviceRecordingBuffer[camName].returnOldestFrame())

                return filename
            except:
                pass

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            try:
                while self.recordLoopEnabled:
                    writeFunc(self.deviceRecordingBuffer[camName].returnOldestFrame())

                return filename
            except:
                pass

        # when building the writer function for a specific type of
        # file format, we expect the dictionary to have the appropriate arguments;
        # this job is handled by the user interface, so we do not need to add
        # any type of try-except clauses for the dictionary keys
        filenames = [
            os.path.join(
                writerInfo.folder, camName.replace(":", "-") + "_" + writerInfo.filename
            )
            for camName in camNames
        ]
        sizes = [
            self.deviceControllers[camName].device.roiShape.pixelSizes
            for camName in camNames
        ]
        colorMaps = [
            self.deviceControllers[camName].device.colorType for camName in camNames
        ]
        files = {}
        extension = ""
        if writerInfo.fileFormat in [1, 2]:
            kwargs = dict()
            if writerInfo.fileFormat == 1:  # ImageJ TIFF
                extension = ".tif"
                kwargs.update(dict(imagej=True))
            else:  # OME-TIFF
                extension = ".ome.tif"
                kwargs.update(dict(ome=True))
            files = {
                filename: tiff.TiffWriter(filename + extension, **kwargs)
                for filename in filenames
            }
            writeFuncs = [
                partial(
                    file.write,
                    photometric=TIFF_PHOTOMETRIC_MAP[colorMap][0],
                    software="napari-live-recording",
                    contiguous=kwargs.get("imagej", False),
                )
                for file, size, colorMap in zip(list(files.values()), sizes, colorMaps)
            ]
        else:
            # todo: implement HDF5 writing
            raise ValueError("Unsupported file format selected for recording!")

        workers = []
        bufferWorkers = [captureBuffer(camName) for camName in camNames]

        if writerInfo.recordType == RecordType["Number of frames"]:
            workers = [
                fixedStackToFile(filename, camName, writerInfo.stackSize, writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        elif writerInfo.recordType == RecordType["Time (seconds)"]:
            workers = [
                timeStackToFile(
                    filename, camName, writerInfo.acquisitionTime, writeFunc
                )
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        elif writerInfo.recordType == RecordType["Toggled"]:
            # here we have to do some extra work and set to True the record loop flag
            workers = [
                toggledWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]

        self.recordLoopEnabled = True
        for worker in bufferWorkers:
            worker.finished.connect(lambda: closeWorkerConnection(worker))
            worker.start()

        def startSaving(self):
            for worker in workers:
                worker.finished.connect(lambda: closeWorkerConnection(worker))
                worker.start()

    def stopRecord(self):
        self.recordLoopEnabled = False
        self.recordSignalCounter.count = 0

    def cleanup(self):
        if self.isLive:
            self.live(False)
        for key in self.deviceControllers.keys():
            self.deleteCamera(key)
