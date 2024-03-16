import numpy as np
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
        capacity: int,
        allowOverwrite: bool = True,
    ) -> None:
        super().__init__()
        self.stackSize = stackSize
        self.cameraKey = cameraKey
        self._appendedFrames = 0
        self.allowOverwrite = allowOverwrite
        self.frameShape = camera.roiShape.pixelSizes
        self.buffer = deque(maxlen=capacity)

    def clearBuffer(self):
        """Clearing the buffer and resetting the appended frames to zero"""
        try:
            self._appendedFrames = 0
            self.buffer.clear()
        except Exception as e:
            print("Clearing Error", e)

    def addFrame(self, newFrame):
        """Method for attaching a new frame to the buffer."""
        try:
            # if required number of frames is reached and not toggled recording
            if self._appendedFrames == self.stackSize and not self.allowOverwrite:
                self.appendingFinished.emit(self.cameraKey)

            # when shapes of frames in buffer and new frame match, attach the frame and raise number of appended frames
            elif newFrame.shape == self.frameShape:
                self.buffer.appendleft(newFrame)
                if not self.allowOverwrite:
                    self._appendedFrames += 1

            # when shapes do not match, set the new shape as default
            elif newFrame.shape != self.frameShape:
                self.frameShape = newFrame.shape
        except Exception as e:
            pass

    def popHead(self):
        """Return and delete the head (oldest frame) of the buffer"""
        try:
            frame = np.copy(self.buffer.pop())
            return frame
        except Exception as e:
            pass

    def popTail(self):
        """Return and delete the tail (newest frame) of the buffer"""
        try:
            frame = np.copy(self.buffer.popleft())
            return frame
        except Exception as e:
            pass

    def returnTail(self):
        """Return the tail (newest frame) of the buffer"""
        return np.copy(self.buffer[0])

    def returnHead(self):
        """Return the head (oldest frame) of the buffer"""
        return np.copy(self.buffer[-1])

    def changeROI(self, newROI: ROI):
        """Change the default shape when the ROI is changed"""
        self.frameShape = newROI.pixelSizes
        self.clearBuffer()

    def changeStacksize(self, newStacksize: int):
        self.stackSize = newStacksize

    @property
    def full(self) -> bool:
        return len(self.buffer) == self.stackSize

    @property
    def empty(self) -> bool:
        return len(self.buffer) == 0

    @property
    def length(self) -> int:
        return len(self.buffer)
