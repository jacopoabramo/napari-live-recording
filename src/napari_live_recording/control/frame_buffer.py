import numpy as np
import threading
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import ICamera


class Framebuffer:
    def __init__(
        self, stackSize: int, camera: ICamera, allowOverwrite: bool = True
    ) -> None:
        self.stackSize = stackSize
        self._appendedFrames = 0
        self.allowOverwrite = allowOverwrite
        self.shape = camera.roiShape.pixelSizes
        self.new = self.stackSize - 1
        self.lock = threading.Lock()
        self.old = (self.new + 1) % self.stackSize
        self.buffer = np.zeros(shape=(self.stackSize,) + self.shape, dtype=np.uint32)

    def clearBuffer(self):
        try:
            with self.lock:
                print("Clearing buffer")
                self._appendedFrames = 0
                self.new = self.stackSize - 1
                self.old = (self.new + 1) % self.stackSize
                self.buffer = np.zeros(
                    shape=(self.stackSize,) + self.shape, dtype=np.uint32
                )

        except Exception as e:
            print("Problems clearing the buffer", e)

    def renewBuffer(self, newStacksize):
        try:
            with self.lock:
                self.stacksize = newStacksize
                self._appendedFrames = 0
                self.new = self.stackSize - 1
                self.old = (self.new + 1) % self.stackSize
                self.buffer = np.zeros(
                    shape=(self.stackSize,) + self.shape, dtype=np.uint32
                )
        except Exception as e:
            print(e)

    def addFrame(self, newFrame: np.array):
        try:
            with self.lock:
                if self.full and not self.allowOverwrite:
                    raise IndexError(
                        "ImageBuffer overflows, because overwrite is disabled."
                    )
                else:
                    if newFrame.shape == self.shape:
                        self.new = (self.new + 1) % self.stackSize
                        self.old = (self.new + 1) % self.stackSize
                        self.buffer[self.new] = newFrame
                        self._appendedFrames += 1
                    else:
                        self.shape = newFrame.shape
                        print("Shape changed")
                        self.clearBuffer()
        except Exception as e:
            print(e)
            pass

    def popOldestFrame(self):
        with self.lock:
            nonZeros = np.nonzero(np.any(np.any(self.buffer, axis=2), axis=1))
            print("Nonzeros in Buffer", len(nonZeros[0]))
            nonZeros_new = np.where(nonZeros[0] == self.new)[0][0]
            if len(nonZeros[0]) > 1:
                indexOfOldest = nonZeros[0][(nonZeros_new + 1) % len(nonZeros[0])]
                oldestFrame = np.copy(self.buffer[indexOfOldest])
                self.buffer[indexOfOldest] = np.zeros(self.shape)
                return oldestFrame
            elif len(nonZeros[0]) == 1:
                oldestFrame = np.copy(self.buffer[self.new])
                self.buffer[self.new] = np.zeros(self.shape)
                return oldestFrame
            else:
                print("nothing to pop")
                return None

    def popNewestFrame(self):
        with self.lock:
            newestFrame = np.delete(self.buffer, self.new)
        return newestFrame

    def replaceFrameAt(self, index: int, newFrame: np.array):
        idx = (self.new + 1 + index) % self.stackSize
        self.buffer[idx] = newFrame

    def returnNewestFrame(self):
        with self.lock:
            return self.buffer[self.new]

    def returnOldestFrame(self):
        try:
            nonZeros = np.nonzero(np.any(np.any(self.buffer, axis=2), axis=1))
            nonZeros_new = np.where(nonZeros[0] == self.new)[0][0]
            if len(nonZeros[0]) > 1:
                indexOfOldest = nonZeros[0][(nonZeros_new + 1) % len(nonZeros[0])]
                oldestFrame = self.buffer[indexOfOldest]
                return oldestFrame
            elif len(nonZeros[0]) == 1:
                oldestFrame = np.copy(self.buffer[self.new])
                return oldestFrame
            else:
                return None
        except Exception as e:
            print(e)

    def returnFrameAt(self, index: int):
        idx = (self.new + 1 + index) % self.stackSize
        return self.buffer[idx]

    def changeROI(self, newROI: ROI):
        self.shape = newROI.pixelSizes
        self.clearBuffer()

    def changeStacksize(self, newStacksize: int):
        stackDifference = newStacksize - self.stackSize
        self.old = (self.new + 1) % self.stackSize
        if stackDifference > 0:
            emptyFrames = np.zeros(((stackDifference,) + self.shape))
            self.buffer = np.insert(self.buffer, self.old, emptyFrames, axis=0)
        elif stackDifference < 0:
            if self.new > self.old:
                self.buffer = self.buffer[(self.new - newStacksize) + 1 : self.new + 1]
            else:
                self.buffer = np.delete(
                    self.buffer,
                    np.s_[
                        self.new + 1 : (self.new + 1 - stackDifference)
                        if (self.new + 1 - stackDifference) <= self.stackSize - 1
                        else None
                    ],
                    axis=0,
                )
        else:
            pass
        self.stackSize = newStacksize
        if self.old < self.new:
            self.new = (self.new + stackDifference) % self.stackSize
        self.old = (self.new + 1) % self.stackSize

    @property
    def full(self) -> bool:
        nonZeros = np.nonzero(np.any(np.any(self.buffer, axis=2), axis=1))
        return len(nonZeros[0]) == self.stackSize

    @property
    def empty(self) -> bool:
        nonZeros = np.nonzero(np.any(np.any(self.buffer, axis=2), axis=1))
        return len(nonZeros[0]) == 0

    @property
    def length(self) -> int:
        nonZeros = np.nonzero(np.any(np.any(self.buffer, axis=2), axis=1))
        return len(nonZeros[0])
