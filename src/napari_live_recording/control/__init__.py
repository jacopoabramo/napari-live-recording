import numpy as np
import tifffile.tifffile as tiff
import h5py
import os
from typing import Union
from contextlib import contextmanager
from napari.qt.threading import thread_worker, FunctionWorker
from qtpy.QtCore import QThread, QObject, Signal, QTimer
from napari_live_recording.common import (
    TIFF_PHOTOMETRIC_MAP,
    WriterInfo,
    RecordType,
    ROI,
    Settings,
    createPipelineFilter,
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
            print("MaxCount Reached")
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
        self.deviceBuffers: Dict[str, Framebuffer] = {}
        self.recordingBuffers: Dict[str, Framebuffer] = {}
        self.processingBuffers: Dict[str, Framebuffer] = {}
        self.processedBuffers: Dict[str, Framebuffer] = {}
        self.settings = Settings()
        self.filterGroupsDict = self.settings.getFilterGroupsDict()
        self.stackSize = 5000
        self.idx = 0
        self.bufferWorker = None
        self.__isAcquiring = False
        self.recordLoopEnabled = False
        self.processingRunning: Dict[str, bool] = {}
        self.recordingRunning: Dict[str, bool] = {}
        self.recordSignalCounter = SignalCounter()
        self.recordSignalCounter.maxCountReached.connect(
            lambda: self.recordFinished.emit()
        )
        self.recordFinished.connect(self.resetRecordingCounter)

    @property
    def isAcquiring(self) -> bool:
        return self.__isAcquiring

    @contextmanager
    def recordToBufferPaused(self):
        print("ContextManager")
        if self.isAcquiring:
            try:
                self.recordToBuffer(False)
                yield
            finally:
                self.recordToBuffer(True)
        else:
            yield

    def addCamera(self, cameraKey: str, camera: ICamera) -> str:
        """Adds a new device in the controller, with a thread in which the device operates."""
        thread = QThread()
        camera.moveToThread(thread)
        deviceController = LocalController(thread, camera)
        self.deviceControllers[cameraKey] = deviceController
        self.deviceControllers[cameraKey].thread.start()
        self.deviceBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey
        )
        self.recordingBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey
        )
        self.processingBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey
        )
        self.processedBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey
        )
        self.processingRunning[cameraKey] = False
        self.recordingRunning[cameraKey] = False

        self.recordSignalCounter.maxCount += 3
        return cameraKey

    def recordToBuffer(self, toggle: bool):
        print("Record to buffer", toggle)
        self.__isAcquiring = toggle

        @thread_worker(worker_class=FunctionWorker, start_thread=False)
        def recordToBufferLoop():
                while self.isAcquiring:
                    for cameraKey in self.deviceControllers.keys():
                        print("record To Buffer Loop Running")
                        try:
                            currentFrame = np.copy(
                                self.deviceControllers[cameraKey].device.grabFrame()
                            )
                            self.deviceBuffers[cameraKey].addFrame(currentFrame)

                            if self.recordingRunning[cameraKey]:
                                print("also Recording in Buffer Loop")
                                self.recordingBuffers[cameraKey].addFrame(currentFrame)
                                self.processingBuffers[cameraKey].addFrame(currentFrame)
                        except Exception as e:
                            pass

        if self.isAcquiring:
            print("Start Buffer Worker")
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(True)
            self.bufferWorker = recordToBufferLoop()
            self.bufferWorker.start()
        else:
            print("Quitting Buffer Worker")
            self.bufferWorker.quit()
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(False)

    def changeCameraROI(self, cameraKey: str, newROI: ROI) -> None:
        self.deviceControllers[cameraKey].device.changeROI(newROI)
        self.deviceLiveBuffer[cameraKey] = np.zeros(shape=newROI.pixelSizes)
        self.deviceBuffers[cameraKey].changeROI(newROI)
        self.recordingBuffers[cameraKey].changeROI(newROI)
        self.processingBuffers[cameraKey].changeROI(newROI)
        self.processedBuffers[cameraKey].changeROI(newROI)

    def changeStackSize(self, newStackSize: int):
        self.stackSize = newStackSize
        for cameraKey in self.deviceControllers.keys():
            self.recordingBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )
            self.processingBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )
            self.processedBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )

    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera device."""
        try:
            self.__isAcquiring = False
            self.processingRunning.pop(cameraKey)
            self.recordingRunning.pop(cameraKey)
            self.cameraDeleted.emit(False)

            self.deviceControllers[cameraKey].device.close()
            self.deviceControllers[cameraKey].thread.quit()
            self.deviceControllers[cameraKey].device.deleteLater()
            self.deviceControllers[cameraKey].thread.deleteLater()
            self.deviceControllers[cameraKey].device.setAcquisitionStatus(False)

            self.deviceBuffers.pop(cameraKey)
            self.recordingBuffers.pop(cameraKey)
            self.processingBuffers.pop(cameraKey)
            self.processedBuffers.pop(cameraKey)

            self.recordSignalCounter.maxCount -= 3
        except RuntimeError:
            # camera already deleted
            pass

    def returnNewestFrame(self, cameraKey: str) -> None:
        if self.isAcquiring:
            newestFrame = self.processedBuffers[cameraKey].returnTail()
            return newestFrame
        else:
            pass

    def snap(self, cameraKey: str, functionsDict) -> np.ndarray:
        self.deviceControllers[cameraKey].device.setAcquisitionStatus(True)
        if list(functionsDict.values())[0] == None:
            image = self.deviceControllers[cameraKey].device.grabFrame()
        else:
            image_ = self.deviceControllers[cameraKey].device.grabFrame()
            composedFunction = createPipelineFilter(functionsDict)
            image = composedFunction(image_)
        self.deviceControllers[cameraKey].device.setAcquisitionStatus(False)
        return image

    def processFrames(self, status, camName, selectedFilterGroup):
        print("Process frames", status)

        @thread_worker(
            worker_class=FunctionWorker,
            start_thread=False,
        )
        def processFramesLoop(camName: str) -> None:
            if list(selectedFilterGroup.values())[0] == None:
                print("none")
                while self.deviceBuffers[camName].empty:
                    pass

                while self.isAcquiring:
                    try:
                        frame = self.deviceBuffers[camName].popHead()
                        self.processedBuffers[camName].addFrame(frame)
                    except Exception as e:
                        pass

            else:
                print("Not none")
                filterFunction = createPipelineFilter(selectedFilterGroup)
                while self.deviceBuffers[camName].empty:
                    print("Empty")
                    pass

                while self.isAcquiring:
                    try:
                        print("Process loop try")
                        frame_processed = filterFunction(
                            self.deviceBuffers[camName].popHead()
                        )
                        self.processedBuffers[camName].addFrame(frame_processed)
                    except Exception as e:
                        print("processLoop", e)
                        pass

        processingWorker = processFramesLoop(camName)
        if status:
            print("Start process worker")
            processingWorker.start()
        else:
            print("Quitting processing workers")
            processingWorker.quit()

    def process(self, filtersList: dict, writerInfo: WriterInfo) -> None:
        for key in filtersList.copy().keys():
            if list(filtersList[key].values())[0] == None:
                self.recordSignalCounter.increaseCounter()
                self.recordSignalCounter.increaseCounter()
                del filtersList[key]
            else:
                pass

        def closeFile(filename) -> None:
            files[filename].close()

        def closeWorkerConnection(worker: FunctionWorker) -> None:
            self.recordSignalCounter.increaseCounter()
            print("Signal Count", self.recordSignalCounter.count)
            worker.finished.disconnect()

        def timeStackBuffer(camName: str, acquisitionTime: float):
            self.processingBuffers[camName].allowOverwrite = False
            self.processingBuffers[camName].clearBuffer()
            self.processingBuffers[camName].stackSize = round(acquisitionTime * 30)
            self.processedBuffers[camName].allowOverwrite = False
            self.processedBuffers[camName].clearBuffer()
            self.processedBuffers[camName].stackSize = round(acquisitionTime * 30)

        def fixedStackBuffer(camName: str, stackSize: int):
            self.processingBuffers[camName].allowOverwrite = False
            self.processingBuffers[camName].clearBuffer()
            self.processingBuffers[camName].stackSize = stackSize
            self.processedBuffers[camName].allowOverwrite = False
            self.processedBuffers[camName].clearBuffer()
            self.processedBuffers[camName].stackSize = stackSize

        def toggledBuffer(camName: str):
            self.processingBuffers[camName].allowOverwrite = True
            self.processedBuffers[camName].allowOverwrite = True

        @thread_worker(
            worker_class=FunctionWorker,
            start_thread=False,
        )
        def processFrames(camName: str) -> None:
            self.processingRunning[camName] = True
            filterFunction = createPipelineFilter(filtersList[camName])
            while self.processingBuffers[camName].empty:
                pass

            while (
                self.recordingRunning[camName]
                or not self.processingBuffers[camName].empty
            ):
                try:
                    frame_processed = filterFunction(
                        self.processingBuffers[camName].popHead()
                    )
                    self.processedBuffers[camName].addFrame(frame_processed)
                except Exception as e:
                    pass
            self.processingRunning[camName] = False
            print("Processing finished")

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def stackWriteToFile(filename: str, camName: str, writeFunc) -> str:
            while not self.processingRunning[camName]:
                pass
            while (
                not self.processedBuffers[camName].empty
                or self.processingRunning[camName]
            ):
                try:
                    if self.processedBuffers[camName].empty:
                        pass
                    else:
                        frame = self.processedBuffers[camName].popHead()
                        writeFunc(frame)
                except Exception as e:
                    pass

            print("Writing process finished")
            return filename

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            while not self.processingRunning[camName]:
                pass
            while (
                not self.processedBuffers[camName].empty
                or self.processingRunning[camName]
            ):
                try:
                    if self.processedBuffers[camName].empty:
                        pass
                    else:
                        frame = self.processedBuffers[camName].popHead()

                        writeFunc(frame)
                except Exception as e:
                    pass
            print("Writing process toggled finished")
            return filename

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
            # extension = ".hdf5"
            # files = {
            #     filename: h5py.File(filename + extension, **kwargs)
            #     for filename in filenames
            # }
            # for file in files.values():
            #     file.create_dataset()
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
            processingWorkers = [
                processFrames(camName) for camName in filtersList.keys()
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
            processingWorkers = [
                processFrames(camName) for camName in filtersList.keys()
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
            processingWorkers = [
                processFrames(camName) for camName in filtersList.keys()
            ]

        for processingworker in processingWorkers:
            processingworker.finished.connect(
                lambda: closeWorkerConnection(processingworker)
            )
            processingworker.start()

        for fileworker in fileWorkers:
            fileworker.finished.connect(lambda: closeWorkerConnection(fileworker))
            fileworker.start()

    def record(self, camNames: list, writerInfo: WriterInfo) -> None:
        self.recordingTimer = QTimer(singleShot=True)

        def closeFile(filename) -> None:
            files[filename].close()

        def closeWorkerConnection(worker: FunctionWorker) -> None:
            self.recordSignalCounter.increaseCounter()
            print("Signal Count", self.recordSignalCounter.count)
            worker.finished.disconnect()

        def timeStackBuffer(camName: str, acquisitionTime: float):
            self.recordingBuffers[camName].allowOverwrite = False
            self.recordingBuffers[camName].clearBuffer()
            self.recordingBuffers[camName].stackSize = round(acquisitionTime * 30)
            self.recordingBuffers[camName].appendingFinished.connect(
                self.stopRecordSingleCamera
            )
            self.recordingRunning[camName] = True

        def fixedStackBuffer(camName: str, stackSize: int):
            self.recordingBuffers[camName].allowOverwrite = False
            self.recordingBuffers[camName].clearBuffer()
            self.recordingBuffers[camName].stackSize = stackSize
            self.recordingBuffers[camName].appendingFinished.connect(
                self.stopRecordSingleCamera
            )
            self.recordingRunning[camName] = True

        def toggledBuffer(camName: str):
            self.recordingBuffers[camName].allowOverwrite = True
            self.recordingRunning[camName] = True

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
                    self.recordingRunning[camName]
                    or not self.recordingBuffers[camName].empty
                ):
                    try:
                        frame = self.recordingBuffers[camName].popHead()
                        writeFunc(frame)
                    except Exception as e:
                        pass
            except Exception as e:
                pass
            print("Writing record finished")
            return filename

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            while self.recordingBuffers[camName].empty:
                pass
                while (
                    self.recordingRunning[camName]
                    or not self.recordingBuffers[camName].empty
                ):
                    try:
                        writeFunc(self.recordingBuffers[camName].popHead())
                    except:
                        pass
            print("Writing record toggled finished")
            return filename

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

    def stopRecordSingleCamera(self, camName):
        self.recordingRunning[camName] = False

    def stopRecord(self):
        for key in self.recordingRunning.keys():
            self.recordingRunning[key] = False

    def resetRecordingCounter(self):
        self.recordSignalCounter.count = 0

    def cleanup(self):
        for key in self.deviceControllers.keys():
            self.deleteCamera(key)
