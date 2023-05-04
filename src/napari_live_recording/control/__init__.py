import numpy as np
import tifffile.tifffile as tiff
from napari.qt.threading import thread_worker, GeneratorWorker, FunctionWorker
from qtpy.QtCore import QThread, QObject, Signal
from napari_live_recording.common import FileFormat, ROI
from napari_live_recording.control.devices.interface import ICamera
from typing import Dict, NamedTuple
from functools import partialmethod
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
        self.liveWorker = None
        self.recordLoopEnabled = False
        self.recordSignalCounter = SignalCounter()
        self.recordSignalCounter.maxCountReached.connect(self.recordFinished.emit)

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
        self.recordSignalCounter.maxCount += 1
        return cameraKey

    def changeCameraROI(self, cameraKey: str, newROI: ROI) -> None:
        self.deviceControllers[cameraKey].device.changeROI(newROI)
        self.deviceLiveBuffer[cameraKey] = np.zeros(shape=newROI.pixelSizes)

    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera device."""
        self.deviceControllers[cameraKey].device.close()
        self.deviceControllers[cameraKey].thread.quit()
        self.deviceControllers[cameraKey].device.deleteLater()
        self.deviceControllers[cameraKey].thread.deleteLater()
        self.recordSignalCounter.maxCount -= 1
        del self.deviceControllers[cameraKey]
        del self.deviceLiveBuffer[cameraKey]

    def snap(self, cameraKey: str) -> np.ndarray:
        return self.deviceControllers[cameraKey].device.grabFrame()

    def live(self, toggle: bool) -> None:
        @thread_worker(worker_class=FunctionWorker, start_thread=False)
        def liveLoop():
            while True:
                for key in self.deviceControllers.keys():
                    self.deviceLiveBuffer[key] = np.copy(
                        self.deviceControllers[key].device.grabFrame()
                    )

        if toggle:
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(True)
            self.liveWorker = liveLoop()
            self.liveWorker.start()
        else:
            self.liveWorker.quit()
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(False)

    def record(self, camNames: list, writerInfo: dict) -> None:
        def closeFile(filename) -> None:
            files[filename].close()

        def closeWorkerConnection(worker: FunctionWorker) -> None:
            self.recordSignalCounter.increaseCounter()
            worker.finished.disconnect()

        @thread_worker(worker_class=FunctionWorker, connect={"returned": closeFile})
        def recordFixedStack(
            filename: str, camName: str, stackSize: int, writeFunc
        ) -> str:
            for _ in range(stackSize):
                writeFunc(self.deviceControllers[camName].device.grabFrame())
            return filename

        @thread_worker(worker_class=FunctionWorker, connect={"returned": closeFile})
        def recordTimeStack(
            filename: str, camName: str, acquisitionTime: float, writeFunc
        ) -> str:
            startTime = time()
            while time() - startTime <= acquisitionTime:
                writeFunc(self.deviceControllers[camName].device.grabFrame())
            return filename

        @thread_worker(worker_class=FunctionWorker, connect={"returned": closeFile})
        def recordToggledStack(filename: str, camName: str, writeFunc) -> str:
            while self.recordLoopEnabled:
                writeFunc(self.deviceControllers[camName].device.grabFrame())
            return filename

        # when building the writer function for a specific type of
        # file format, we expect the dictionary to have the appropriate arguments;
        # this job is handled by the user interface, so we do not need to add
        # any type of try-except clauses for the dictionary keys
        filenames = [
            camName
            + "_"
            + writerInfo["filename"]
            + "."
            + writerInfo["format"].name.lower()
            for camName in camNames
        ]
        sizes = [
            self.deviceControllers[camName].device.roiShape.pixelSizes
            for camName in camNames
        ]
        files = {}
        if writerInfo["format"] == FileFormat.TIFF:
            files = {
                filename: tiff.TiffWriter(filename, bigtiff=True, append=True)
                for filename in filenames
            }
            writeFuncs = [
                partialmethod(
                    file.write, shape=size, photometric=tiff.PHOTOMETRIC.MINISBLACK
                )
                for file, size in zip(list(files.values()), sizes)
            ]
        else:
            # todo: implement HDF5 writing
            raise ValueError("Unsupported file format selected for recording!")

        workers = []
        if writerInfo["recordtype"] == "frames":
            workers = [
                recordFixedStack(filename, camName, writerInfo["stackSize"], writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        elif writerInfo["recordtype"] == "time":
            workers = [
                recordTimeStack(
                    filename, camName, writerInfo["acquisitionTime"], writeFunc
                )
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        elif writerInfo["recordtype"] == "toggled":
            # here we have to do some extra work and set to True the record loop flag
            workers = [
                recordToggledStack(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        for worker in workers:
            worker.finished.connect(lambda: closeWorkerConnection(worker))
            worker.start()

    def toggleRecord(self, status: bool):
        self.recordLoopEnabled = status
