import numpy as np
import tifffile.tifffile as tiff
import os
import functools
from typing import Union
from contextlib import contextmanager
from napari.qt.threading import thread_worker, FunctionWorker
from qtpy.QtCore import QThread, QObject, Signal, QTimer, QSettings
from napari_live_recording.common import (
    TIFF_PHOTOMETRIC_MAP,
    WriterInfo,
    FileFormat,
    RecordType,
    ROI,
    settings,
    Settings,
    createPipelineFilter,
    filtersDict,
)
from napari_live_recording.control.devices.interface import ICamera
from napari_live_recording.control.frame_buffer import Framebuffer
from typing import Dict, NamedTuple
from functools import partial
from time import time
import pims


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
    newTimePoint = Signal(int)
    newMaxTimePoint = Signal(int)
    cameraDeleted = Signal(bool)

    def __init__(self) -> None:
        """Main Controller class. Stores all camera objects to access live and stack recordings."""
        super().__init__()
        self.deviceControllers: Dict[str, LocalController] = {}
        self.deviceLiveBuffer: Dict[str, np.ndarray] = {}
        self.deviceBuffers: Dict[str, Framebuffer] = {}
        self.recordingBuffers: Dict[str, Framebuffer] = {}
        self.processingBuffers: Dict[str, Framebuffer] = {}
        self.settings = Settings()
        self.filtersDict = filtersDict
        self.stackSize = 100
        self.idx = 0
        self.liveWorker = None
        self.__isAcquiring = {}
        self.recordLoopEnabled = False
        self.recordSignalCounter = SignalCounter()
        self.recordSignalCounter.maxCountReached.connect(
            lambda: self.recordFinished.emit()
        )

        self.bufferWorkers: Dict[str, FunctionWorker] = {}

    @property
    def isLive(self) -> dict:
        return self.__isAcquiring

    def addCamera(self, cameraKey: str, camera: ICamera) -> str:
        """Adds a new device in the controller, with a thread in which the device operates."""
        thread = QThread()
        camera.moveToThread(thread)
        deviceController = LocalController(thread, camera)
        self.deviceControllers[cameraKey] = deviceController
        self.deviceControllers[cameraKey].thread.start()
        self.deviceBuffers[cameraKey] = Framebuffer(self.stackSize, camera=camera)
        self.recordingBuffers[cameraKey] = Framebuffer(self.stackSize, camera=camera)
        self.processingBuffers[cameraKey] = Framebuffer(self.stackSize, camera=camera)
        print("Buffers created")

        self.recordSignalCounter.maxCount += 1

        self.deviceControllers[cameraKey].device.setAcquisitionStatus(True)
        self.bufferWorkers[cameraKey] = self.recordToBuffer(cameraKey)
        self.__isAcquiring[cameraKey] = True
        self.bufferWorkers[cameraKey].start()

        return cameraKey

    @thread_worker(worker_class=FunctionWorker, start_thread=False)
    def recordToBuffer(self, cameraKey: str):
        if self.__isAcquiring[cameraKey]:
            while self.__isAcquiring[cameraKey]:
                try:
                    currentFrame = np.copy(
                        self.deviceControllers[cameraKey].device.grabFrame()
                    )
                    self.deviceBuffers[cameraKey].addFrame(currentFrame)

                    if self.recordLoopEnabled:
                        self.recordingBuffers[cameraKey].addFrame(currentFrame)
                        self.processingBuffers[cameraKey].addFrame(currentFrame)
                except Exception as e:
                    print("Record to buffer", e)

    def changeCameraROI(self, cameraKey: str, newROI: ROI) -> None:
        self.deviceControllers[cameraKey].device.changeROI(newROI)
        self.deviceLiveBuffer[cameraKey] = np.zeros(shape=newROI.pixelSizes)
        self.deviceBuffers[cameraKey].changeROI(newROI)
        self.recordingBuffers[cameraKey].changeROI(newROI)
        self.processingBuffers[cameraKey].changeROI(newROI)

    def changeStackSize(self, newStackSize: int):
        self.stackSize = newStackSize
        for cameraKey in self.deviceControllers.keys():
            self.recordingBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )
            self.processingBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )

    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera device."""
        try:
            self.__isAcquiring[cameraKey] = False
            self.cameraDeleted.emit(False)

            self.deviceControllers[cameraKey].device.close()
            self.deviceControllers[cameraKey].thread.quit()
            self.deviceControllers[cameraKey].device.deleteLater()
            self.deviceControllers[cameraKey].thread.deleteLater()
            self.bufferWorkers[cameraKey].quit()
            self.deviceControllers[cameraKey].device.setAcquisitionStatus(False)

            _ = self.deviceBuffers.pop(cameraKey)
            _ = self.recordingBuffers.pop(cameraKey)
            _ = self.processingBuffers.pop(cameraKey)

            self.recordSignalCounter.maxCount -= 1
            print("Camera Deleted Signal")
        except RuntimeError:
            # camera already deleted
            pass

    def returnNewestFrame(self, cameraKey: str) -> None:
        if self.__isAcquiring[cameraKey]:
            self.newestFrame = self.deviceBuffers[cameraKey].returnNewestFrame()
            return self.newestFrame
        else:
            pass

    def process(self, filtersList: dict, writerInfo: WriterInfo) -> None:
        def closeFile(filename) -> None:
            files[filename].close()

        # def createPipelineFilter(filters):
        #     def composeFunctions(functionList):
        #         return functools.reduce(
        #             lambda f, g: lambda x: f(g(x)), functionList, lambda x: x
        #         )

        #     functionList = []
        #     for filter in filters.values():
        #         functionList.append(pims.pipeline(filter))

        #     composedFunction = composeFunctions(list(reversed(functionList)))
        #     return composedFunction

        def closeWorkerConnection(worker: FunctionWorker) -> None:
            self.recordSignalCounter.increaseCounter()
            worker.finished.disconnect()
            print("worker disconnected")

        def timeStackBuffer(camName: str, acquisitionTime: float):
            self.processingBuffers[camName].allowOverwrite = True
            self.processingBuffers[camName].renewBuffer(round(acquisitionTime * 30))

        def fixedStackBuffer(camName: str, stackSize: int):
            self.processingBuffers[camName].allowOverwrite = False
            self.processingBuffers[camName].renewBuffer(stackSize - 1)

        def toggledBuffer(camName: str):
            self.processingBuffers[camName].allowOverwrite = True

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def stackWriteToFile(filename: str, camName: str, writeFunc) -> str:
            try:
                while self.processingBuffers[camName].empty:
                    pass

                if filtersList[camName] == None:
                    while (
                        self.recordLoopEnabled
                        or not self.recordingBuffers[camName].empty
                    ):
                        try:
                            frame = self.processingBuffers[camName].popOldestFrame()
                            writeFunc(frame)
                        except:
                            pass
                else:
                    print("StackWrite", filtersList[camName])
                    filterFunction = createPipelineFilter(filtersList[camName])
                    print("StackWrite, fct", filterFunction)
                    while (
                        self.recordLoopEnabled
                        or not self.recordingBuffers[camName].empty
                    ):
                        try:
                            print("Still writing", self.recordLoopEnabled)
                            frame = filterFunction(
                                self.processingBuffers[camName].popOldestFrame()
                            )
                            writeFunc(frame)
                        except Exception as e:
                            print("Inner while process ", e)
                print("empty")
                return filename
            except Exception as e:
                print("Process stack write to file", e)

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            try:
                while self.recordLoopEnabled:
                    if filtersList[camName] is None:
                        writeFunc(self.deviceBuffers[camName].returnOldestFrame())
                    else:
                        writeFunc(
                            filtersList[camName](
                                self.deviceBuffers[camName].returnOldestFrame()
                            )
                        )
                return filename
            except:
                pass

        # when building the writer function for a specific type of
        # file format, we expect the dictionary to have the appropriate arguments;
        # this job is handled by the user interface, so we do not need to add
        # any type of try-except clauses for the dictionary keys
        filenames = [
            os.path.join(
                writerInfo.folder,
                camName.replace(":", "-").replace(" ", "-") + "_" + writerInfo.filename,
            )
            for camName in filtersList.keys()
        ]
        sizes = [
            self.deviceControllers[camName].device.roiShape.pixelSizes
            for camName in filtersList.keys()
        ]
        colorMaps = [
            self.deviceControllers[camName].device.colorType
            for camName in filtersList.keys()
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
        fileWorkers = []

        if writerInfo.recordType == RecordType["Number of frames"]:
            for camName in filtersList.keys():
                fixedStackBuffer(camName, writerInfo.stackSize)

            fileWorkers = [
                stackWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(
                    filenames, filtersList.keys(), writeFuncs
                )
            ]
        elif writerInfo.recordType == RecordType["Time (seconds)"]:
            for camName in filtersList.keys():
                timeStackBuffer(camName, writerInfo.acquisitionTime)
            fileWorkers = [
                stackWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(
                    filenames, filtersList.keys(), writeFuncs
                )
            ]
        elif writerInfo.recordType == RecordType["Toggled"]:
            # here we have to do some extra work and set to True the record loop flag
            for camName in filtersList.keys():
                toggledBuffer(camName)
            fileWorkers = [
                toggledWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(
                    filenames, filtersList.keys(), writeFuncs
                )
            ]

        for fileworker in fileWorkers:
            fileworker.finished.connect(lambda: closeWorkerConnection(fileworker))
            fileworker.start()

    def record(self, camNames: list, writerInfo: WriterInfo) -> None:
        self.recordingTimer = QTimer(singleShot=True)

        def closeFile(filename) -> None:
            files[filename].close()

        def closeWorkerConnection(worker: FunctionWorker) -> None:
            self.recordSignalCounter.increaseCounter()
            worker.finished.disconnect()
            print("worker disconnected")

        # def prepareBuffer(camName: str, buffersize: Union[int, float]):
        #     self.recordingBuffers[camName].allowOverwrite = False
        #     self.recordingBuffers[camName].renewBuffer(buffersize)

        def timeStackBuffer(camName: str, acquisitionTime: float):
            self.recordingBuffers[camName].allowOverwrite = True
            self.recordingBuffers[camName].renewBuffer(round(acquisitionTime * 30))
            self.recordingTimer.setInterval(round(acquisitionTime * 1000))
            self.recordingTimer.timeout.connect(self.stopRecord)
            print("connected")
            self.recordingTimer.start()
            self.recordLoopEnabled = True

        def fixedStackBuffer(camName: str, stackSize: int):
            self.recordingBuffers[camName].allowOverwrite = False
            self.recordingBuffers[camName].renewBuffer(stackSize - 1)
            self.recordingBuffers[camName].appendingFinished.connect(self.stopRecord)
            self.recordLoopEnabled = True

        def toggledBuffer(camName: str):
            self.recordingBuffers[camName].allowOverwrite = True
            self.recordLoopEnabled = True

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def stackWriteToFile(filename: str, camName: str, writeFunc) -> str:
            try:
                while self.recordingBuffers[camName].empty:
                    pass
                while (
                    self.recordLoopEnabled or not self.recordingBuffers[camName].empty
                ):
                    try:
                        # print("before pop", self.recordingBuffers[camName].length)
                        frame = self.recordingBuffers[camName].popOldestFrame()
                        # print("after pop", self.recordingBuffers[camName].length)
                        writeFunc(frame)
                    except Exception as e:
                        print("Inner while record ", e)
                print("empty")
                return filename
            except Exception as e:
                print("Record stack write to file", e)

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            try:
                while self.recordLoopEnabled:
                    writeFunc(self.deviceBuffers[camName].returnOldestFrame())
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
                for file, colorMap in zip(list(files.values()), colorMaps)
            ]
        else:
            # todo: implement HDF5 writing
            raise ValueError(
                "Unsupported file format selected for recording! HDF5 will be implemented in the future."
            )

        workers = []
        fileWorkers = []

        if writerInfo.recordType == RecordType["Number of frames"]:
            for camName in camNames:
                fixedStackBuffer(camName, writerInfo.stackSize)

            fileWorkers = [
                stackWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        elif writerInfo.recordType == RecordType["Time (seconds)"]:
            for camName in camNames:
                timeStackBuffer(camName, writerInfo.acquisitionTime)
            fileWorkers = [
                stackWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]
        elif writerInfo.recordType == RecordType["Toggled"]:
            # here we have to do some extra work and set to True the record loop flag
            for camName in camNames:
                toggledBuffer(camName)
            fileWorkers = [
                toggledWriteToFile(filename, camName, writeFunc)
                for filename, camName, writeFunc in zip(filenames, camNames, writeFuncs)
            ]

        for fileworker in fileWorkers:
            fileworker.finished.connect(lambda: closeWorkerConnection(fileworker))
            fileworker.start()

    def stopRecord(self):
        self.recordLoopEnabled = False
        self.recordSignalCounter.count = 0

    def cleanup(self):
        for key in self.deviceControllers.keys():
            self.deleteCamera(key)
