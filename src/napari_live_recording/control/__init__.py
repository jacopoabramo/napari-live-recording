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
    THIRTY_FPS,
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
from time import time, sleep


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
        self.rawBuffers: Dict[str, Framebuffer] = {}
        self.preProcessingBuffers: Dict[str, Framebuffer] = {}
        self.postProcessingBuffers: Dict[str, Framebuffer] = {}
        self.settings = Settings()
        self.filterGroupsDict = self.settings.getFilterGroupsDict()
        self.stackSize = 1000
        self.bufferWorker = None
        self.__isAcquiring = False
        self.isProcessing: Dict[str, bool] = {}
        self.isAppending: Dict[str, bool] = {}
        self.recordSignalCounter = SignalCounter()
        self.recordSignalCounter.maxCountReached.connect(
            lambda: self.recordFinished.emit()
        )
        self.recordFinished.connect(self.resetRecordingCounter)

    @property
    def isAcquiring(self) -> bool:
        return self.__isAcquiring

    @contextmanager
    def appendToBufferPaused(self):
        if self.isAcquiring:
            try:
                self.appendToBuffer(False)
                yield
            finally:
                self.appendToBuffer(True)
        else:
            yield

    def addCamera(self, cameraKey: str, camera: ICamera) -> str:
        """Adds a new device in the controller, with a thread in which the device operates."""
        thread = QThread()
        camera.moveToThread(thread)
        deviceController = LocalController(thread, camera)
        self.deviceControllers[cameraKey] = deviceController
        self.deviceControllers[cameraKey].thread.start()
        self.rawBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey, capacity=self.stackSize
        )
        self.preProcessingBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey, capacity=self.stackSize
        )
        self.postProcessingBuffers[cameraKey] = Framebuffer(
            self.stackSize, camera=camera, cameraKey=cameraKey, capacity=self.stackSize
        )
        # self.rawBuffers[cameraKey].roiChanged.connect(lambda:self.changeCameraROI)
        # self.preProcessingBuffers[cameraKey].roiChanged.connect(lambda:self.changeCameraROI)
        self.isProcessing[cameraKey] = False
        self.isAppending[cameraKey] = False

        self.recordSignalCounter.maxCount += 3
        return cameraKey

    def appendToBuffer(self, toggle: bool):
        self.__isAcquiring = toggle
        print("Append to Buffer", toggle)

        @thread_worker(worker_class=FunctionWorker, start_thread=False)
        def appendToBufferLoop():
            print("Appending to Buffers Loop")
            while self.isAcquiring:
                sleep(THIRTY_FPS / 1000)
                for cameraKey in self.deviceControllers.keys():
                    try:
                        currentFrame = np.copy(
                            self.deviceControllers[cameraKey].device.grabFrame()
                        )
                        if self.isAppending[cameraKey]:
                            print("Loop")
                            self.rawBuffers[cameraKey].addFrame(currentFrame)
                            self.preProcessingBuffers[cameraKey].addFrame(currentFrame)
                    except Exception as e:
                        print("Appending Error", e)
                        pass

        if self.isAcquiring:
            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(True)
            self.bufferWorker = appendToBufferLoop()
            self.bufferWorker.start()
        else:
            self.bufferWorker.quit()

            for key in self.deviceControllers.keys():
                self.deviceControllers[key].device.setAcquisitionStatus(False)
                try:
                    self.rawBuffers[key].appendingFinished.disconnect()
                except:
                    pass

    def processFrames(
        self, status: bool, type: str, camName: str, selectedFilterGroup: Dict
    ):
        @thread_worker(
            worker_class=FunctionWorker,
            start_thread=False,
        )
        def processFramesLoop(camName: str) -> None:
            self.isProcessing[camName] = True
            # if no filter-group is selected for camName
            if list(selectedFilterGroup.values())[0] == None:
                while self.preProcessingBuffers[camName].empty:
                    pass

                while (
                    self.isAppending[camName]
                    or not self.preProcessingBuffers[camName].empty
                ):
                    try:
                        self.postProcessingBuffers[camName].addFrame(
                            self.preProcessingBuffers[camName].popHead()
                        )
                    except Exception as e:
                        pass

            else:
                filterFunction = createPipelineFilter(selectedFilterGroup)
                while self.preProcessingBuffers[camName].empty:
                    pass

                while (
                    self.isAppending[camName]
                    or not self.preProcessingBuffers[camName].empty
                ):
                    try:
                        frame_processed = filterFunction(
                            self.preProcessingBuffers[camName].popHead()
                        )
                        self.postProcessingBuffers[camName].addFrame(frame_processed)
                    except Exception as e:
                        print("processLoop", e)
                        pass
            self.isProcessing[camName] = False

        if type == "live":
            processingWorker = processFramesLoop(camName)
            processingWorker.finished.connect(
                lambda: processingWorker.finished.disconnect()
            )
            if status:
                processingWorker.start()
            else:
                self.isProcessing[camName] = False
                # manually clear buffer so processing stops, cause empty buffer
                self.preProcessingBuffers[camName].clearBuffer()
                processingWorker.quit()

        # type == "recording"
        else:
            processingWorker = processFramesLoop(camName)

            processingWorker.finished.connect(
                lambda: self.closeWorkerConnection(processingWorker)
            )
            if status:
                processingWorker.start()
            else:
                self.isProcessing[camName] = False

                processingWorker.quit()

    def changeCameraROI(self, cameraKey: str, newROI: ROI) -> None:
        with self.appendToBufferPaused():
            self.rawBuffers[cameraKey].changeROI(newROI)
            self.preProcessingBuffers[cameraKey].changeROI(newROI)
            self.postProcessingBuffers[cameraKey].changeROI(newROI)

    def changeStackSize(self, newStackSize: int):
        self.stackSize = newStackSize
        for cameraKey in self.deviceControllers.keys():
            self.rawBuffers[cameraKey].changeStacksize(newStacksize=self.stackSize)
            self.preProcessingBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )
            self.postProcessingBuffers[cameraKey].changeStacksize(
                newStacksize=self.stackSize
            )

    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera device."""
        try:
            self.__isAcquiring = False
            self.isProcessing.pop(cameraKey)
            self.isAppending.pop(cameraKey)
            self.cameraDeleted.emit(False)

            self.deviceControllers[cameraKey].device.close()
            self.deviceControllers[cameraKey].thread.quit()
            self.deviceControllers[cameraKey].device.deleteLater()
            self.deviceControllers[cameraKey].thread.deleteLater()
            self.deviceControllers[cameraKey].device.setAcquisitionStatus(False)

            # self.deviceBuffers.pop(cameraKey)
            self.rawBuffers.pop(cameraKey)
            self.preProcessingBuffers.pop(cameraKey)
            self.postProcessingBuffers.pop(cameraKey)

            self.recordSignalCounter.maxCount -= 3
        except RuntimeError:
            # camera already deleted
            pass

    def returnNewestFrame(self, cameraKey: str) -> None:
        if self.isAcquiring:
            newestFrame = self.postProcessingBuffers[cameraKey].returnTail()
            return newestFrame
        else:
            pass

    def live(self, status: bool, filtersList: dict):
        for key in filtersList.keys():
            self.isAppending[key] = status
            self.rawBuffers[key].allowOverwrite = status
            self.preProcessingBuffers[key].allowOverwrite = status
            self.postProcessingBuffers[key].allowOverwrite = status
        for key in filtersList.keys():
            self.processFrames(status, "live", key, filtersList[key])

    def snap(self, cameraKey: str, selectedFilter) -> np.ndarray:
        self.deviceControllers[cameraKey].device.setAcquisitionStatus(True)
        if list(selectedFilter.values())[0] == None:
            image = self.deviceControllers[cameraKey].device.grabFrame()
        else:
            image_ = self.deviceControllers[cameraKey].device.grabFrame()
            composedFunction = createPipelineFilter(selectedFilter)
            image = composedFunction(image_)
        self.deviceControllers[cameraKey].device.setAcquisitionStatus(False)
        return image

    def closeWorkerConnection(self, worker: FunctionWorker) -> None:
        self.recordSignalCounter.increaseCounter()
        worker.finished.disconnect()

    def process(self, filtersList: dict, writerInfo: WriterInfo) -> None:
        def closeFile(filename) -> None:
            files[filename].close()

        def timeStackBuffer(camName: str, acquisitionTime: float):
            self.preProcessingBuffers[camName].allowOverwrite = False
            self.preProcessingBuffers[camName].clearBuffer()
            self.preProcessingBuffers[camName].stackSize = round(acquisitionTime * 30)
            self.postProcessingBuffers[camName].allowOverwrite = False
            self.postProcessingBuffers[camName].clearBuffer()
            self.postProcessingBuffers[camName].stackSize = round(acquisitionTime * 30)

        def fixedStackBuffer(camName: str, stackSize: int):
            self.preProcessingBuffers[camName].allowOverwrite = False
            self.preProcessingBuffers[camName].clearBuffer()
            self.preProcessingBuffers[camName].stackSize = stackSize
            self.postProcessingBuffers[camName].allowOverwrite = False
            self.postProcessingBuffers[camName].clearBuffer()
            self.postProcessingBuffers[camName].stackSize = stackSize

        def toggledBuffer(camName: str):
            self.preProcessingBuffers[camName].allowOverwrite = True
            self.postProcessingBuffers[camName].allowOverwrite = True

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def stackWriteToFile(filename: str, camName: str, writeFunc) -> str:
            while not self.isProcessing[camName]:
                pass
            while (
                not self.postProcessingBuffers[camName].empty
                or self.isProcessing[camName]
            ):
                try:
                    if self.postProcessingBuffers[camName].empty:
                        pass
                    else:
                        frame = self.postProcessingBuffers[camName].popHead()
                        writeFunc(frame)
                except Exception as e:
                    pass

            return filename

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            while not self.isProcessing[camName]:
                pass
            while (
                not self.postProcessingBuffers[camName].empty
                or self.isProcessing[camName]
            ):
                try:
                    if self.postProcessingBuffers[camName].empty:
                        pass
                    else:
                        frame = self.postProcessingBuffers[camName].popHead()

                        writeFunc(frame)
                except Exception as e:
                    pass
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

        for camName in filtersList.keys():
            self.processFrames(True, "recording", camName, filtersList[camName])

        for fileworker in fileWorkers:
            fileworker.finished.connect(lambda: self.closeWorkerConnection(fileworker))
            fileworker.start()

    def record(self, camNames: list, writerInfo: WriterInfo) -> None:
        self.recordingTimer = QTimer(singleShot=True)

        def closeFile(filename) -> None:
            files[filename].close()

        def timeStackBuffer(camName: str, acquisitionTime: float):
            self.rawBuffers[camName].allowOverwrite = False
            self.rawBuffers[camName].clearBuffer()
            self.rawBuffers[camName].stackSize = round(acquisitionTime * 30)
            self.rawBuffers[camName].appendingFinished.connect(
                self.stopAppendingForRecording
            )
            self.isAppending[camName] = True

        def fixedStackBuffer(camName: str, stackSize: int):
            self.rawBuffers[camName].allowOverwrite = False
            self.rawBuffers[camName].clearBuffer()
            self.rawBuffers[camName].stackSize = stackSize
            self.rawBuffers[camName].appendingFinished.connect(
                self.stopAppendingForRecording
            )
            self.isAppending[camName] = True

        def toggledBuffer(camName: str):
            self.rawBuffers[camName].allowOverwrite = True
            self.isAppending[camName] = True

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def stackWriteToFile(filename: str, camName: str, writeFunc) -> str:
            try:
                while self.rawBuffers[camName].empty:
                    pass
                while self.isAppending[camName] or not self.rawBuffers[camName].empty:
                    try:
                        frame = self.rawBuffers[camName].popHead()
                        writeFunc(frame)
                    except Exception as e:
                        pass
            except Exception as e:
                pass
            return filename

        @thread_worker(
            worker_class=FunctionWorker,
            connect={"returned": closeFile},
            start_thread=False,
        )
        def toggledWriteToFile(filename: str, camName: str, writeFunc) -> str:
            while self.rawBuffers[camName].empty:
                pass
                while self.isAppending[camName] or not self.rawBuffers[camName].empty:
                    try:
                        writeFunc(self.rawBuffers[camName].popHead())
                    except:
                        pass
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
            fileworker.finished.connect(lambda: self.closeWorkerConnection(fileworker))
            fileworker.start()

    def stopAppendingForRecording(self, camName):
        self.isAppending[camName] = False

    def resetRecordingCounter(self):
        self.recordSignalCounter.count = 0

    def cleanup(self):
        for key in self.deviceControllers.keys():
            self.deleteCamera(key)
