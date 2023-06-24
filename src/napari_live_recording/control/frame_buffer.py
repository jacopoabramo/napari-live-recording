import numpy as np
from napari_live_recording.common import ROI
from napari_live_recording.control.devices.interface import ICamera


class Framebuffer:
    def __init__(self, stackSize: int, camera: ICamera) -> None:
        self.stackSize = stackSize
        self.shape = camera.roiShape.pixelSizes
        self.new = self.stackSize - 1
        self.old = (self.new + 1) % self.stackSize
        self.buffer = np.zeros(shape=(self.stackSize,) + self.shape, dtype=np.uint16)
        self.addedFrames = 0

    def clearBuffer(self):
        self.new = self.stackSize - 1
        self.old = (self.new + 1) % self.stackSize
        self.buffer = np.zeros(shape=(self.stackSize,) + self.shape, dtype=np.uint16)

    def addFrame(self, newFrame: np.array):
        self.new = (self.new + 1) % self.stackSize
        self.old = (self.new + 1) % self.stackSize
        self.buffer[self.new] = newFrame

    def replaceFrameAt(self, index: int, newFrame: np.array):
        idx = (self.new + 1 + index) % self.stackSize
        self.buffer[idx] = newFrame

    def returnNewestFrame(self):
        return self.buffer[self.new]

    def returnOldestFrame(self):
        return self.buffer[self.old]

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


# roi = ROI(height=3, width=2)

# newROI = ROI(height=4, width=7)

# array_1 = np.zeros((roi.height, roi.width)) + 1

# array_2 = np.zeros((roi.height, roi.width)) + 2

# array_3 = np.zeros((roi.height, roi.width)) + 3


# frameBuffer = Framebuffer(22, roi=roi)

# # print(frameBuffer.buffer, frameBuffer.buffer.shape)
# # print("old", frameBuffer.old, "new", frameBuffer.new)
# frameBuffer.addFrame(array_1)

# frameBuffer.addFrame(array_2)

# frameBuffer.addFrame(array_3)
# frameBuffer.addFrame(array_2)


# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)

# print(
#     "hdhfhdfhsdfhdhfo",
#     # frameBuffer.popNewFrame(),
#     frameBuffer.buffer[0],
#     frameBuffer.buffer[1],
#     frameBuffer.buffer[2],
#     frameBuffer.buffer[3],
# )
# # print(frameBuffer.returnNewestFrame())

# print("BREAKBREAKBREKA")

# frameBuffer.changeStacksize(7)
# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)
# frameBuffer.changeStacksize(4)
# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)

# frameBuffer.addFrame(array_1)


# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)
# frameBuffer.changeStacksize(9)


# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)

# frameBuffer.changeStacksize(9)


# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)


# frameBuffer.changeROI(newROI=newROI)

# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)
