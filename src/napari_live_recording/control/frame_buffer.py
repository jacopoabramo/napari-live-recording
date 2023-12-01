import numpy as np
import threading
from collections import deque
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import ICamera
from qtpy.QtCore import QObject, Signal


class Framebuffer(QObject):
    appendingFinished = Signal(str)

    def __init__(
        self,
        stackSize: int,
        camera: ICamera,
        cameraKey: str,
        allowOverwrite: bool = True,
    ) -> None:
        super().__init__()

        self.stackSize = stackSize
        self.cameraKey = cameraKey
        self._appendedFrames = 0
        self.allowOverwrite = allowOverwrite
        self.shape = camera.roiShape.pixelSizes
        self.lock = threading.Lock()
        self.buffer = deque(maxlen=self.stackSize)

    def clearBuffer(self):
        with self.lock:
            self._appendedFrames = 0
            self.buffer.clear()

    def renewBuffer(self, newStacksize):
        try:
            with self.lock:
                self.stackSize = newStacksize
                self._appendedFrames = 0
                self.buffer = deque(maxlen=self.stackSize)
        except Exception as e:
            pass

    def addFrame(self, newFrame: np.array):
        try:
            with self.lock:
                if self._appendedFrames == self.stackSize and not self.allowOverwrite:
                    self.appendingFinished.emit(self.cameraKey)
                elif newFrame.shape == self.shape:
                    self.buffer.appendleft(newFrame)
                    self._appendedFrames += 1
                else:
                    self.shape = newFrame.shape
                    self.clearBuffer()
        except Exception as e:
            print("Adding Error", e)
            pass

    def popOldestFrame(self):
        with self.lock:
            try:
                frame = self.buffer.pop()
                return frame
            except Exception as e:
                pass

    def popNewestFrame(self):
        with self.lock:
            try:
                frame = self.buffer.popleft()
                return frame
            except Exception as e:
                pass

    def returnNewestFrame(self):
        with self.lock:
            return self.buffer[0]

    def returnOldestFrame(self):
        with self.lock:
            return self.buffer[-1]

    def changeROI(self, newROI: ROI):
        self.shape = newROI.pixelSizes
        self.clearBuffer()

    def changeStacksize(self, newStacksize: int):
        self.stackSize = newStacksize
        self.buffer = deque(maxlen=self.stackSize)

    @property
    def full(self) -> bool:
        return len(self.buffer) == self.stackSize

    @property
    def empty(self) -> bool:
        return len(self.buffer) == 0

    @property
    def length(self) -> int:
        return len(self.buffer)
