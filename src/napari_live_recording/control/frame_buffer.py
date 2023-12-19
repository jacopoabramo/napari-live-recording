import numpy as np
import threading
from numpy.typing import NDArray
from collections import deque
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import ICamera
from qtpy.QtCore import QObject, Signal


class Framebuffer(QObject):
    """Class for a ring like buffer to store frames temporarily."""

    # signal for ending the recording as soon as the required number of frames were added
    appendingFinished = Signal(str)

    def __init__(
        self,
        stackSize: int,
        camera: ICamera,
        cameraKey: str,
        allowOverwrite: bool = True,
    ) -> None:
        super().__init__()
        # stacksize is used for initialisation to define the maxlen of the deque, it is used for recording to define how many frames should be recorded
        self.stackSize = stackSize
        self.cameraKey = cameraKey
        self._appendedFrames = 0
        self.allowOverwrite = allowOverwrite
        self.shape = camera.roiShape.pixelSizes
        self.lock = threading.Lock()
        self.buffer = deque(maxlen=self.stackSize)

    def clearBuffer(self):
        """Clearing the buffer and resetting the append frames to zero"""
        with self.lock:
            self._appendedFrames = 0
            self.buffer.clear()

    def addFrame(self, newFrame: NDArray):
        """Method for attaching a new frame to the buffer."""
        try:
            with self.lock:
                # if required number of frames is reached and not toggled recording
                if self._appendedFrames == self.stackSize and not self.allowOverwrite:
                    self.appendingFinished.emit(self.cameraKey)
                # when shapes of frames in buffer and new frame match, attach the frame and raise number of appended frames
                elif newFrame.shape == self.shape:
                    self.buffer.appendleft(newFrame)
                    if not self.allowOverwrite:
                        self._appendedFrames += 1
                # when shapes do not match, clear buffer and set the new shape as default
                else:
                    print("new shape")
                    self.shape = newFrame.shape
                    self.clearBuffer()
        except Exception as e:
            print("Adding Error", e)
            pass

    def popHead(self):
        """Return and delete the head (oldest frame) of the buffer"""
        with self.lock:
            try:
                frame = self.buffer.pop()
                return frame
            except Exception as e:
                pass

    def popTail(self):
        """Return and delete the tail (newest frame) of the buffer"""
        with self.lock:
            try:
                frame = self.buffer.popleft()
                return frame
            except Exception as e:
                pass

    def returnTail(self):
        """Return the tail (newest frame) of the buffer"""
        with self.lock:
            return np.copy(self.buffer[0])

    def returnHead(self):
        """Return the head (oldest frame) of the buffer"""
        with self.lock:
            return np.copy(self.buffer[-1])

    def changeROI(self, newROI: ROI):
        """Change the default shape when the ROI is changed"""
        self.shape = newROI.pixelSizes
        self.clearBuffer()

    def changeStacksize(self, newStacksize: int):
        self.stackSize = newStacksize
        # self.buffer = deque(maxlen=self.stackSize)

    @property
    def full(self) -> bool:
        return len(self.buffer) == self.stackSize

    @property
    def empty(self) -> bool:
        return len(self.buffer) == 0

    @property
    def length(self) -> int:
        return len(self.buffer)
