import numpy as np
from napari_live_recording.common import ROI


class Framebuffer:
    def __init__(self, stackSize: int, roi: ROI) -> None:
        self.stackSize = stackSize
        self.height = roi.height
        self.width = roi.width
        self.tail = self.stackSize - 1
        self.head = (self.tail + 1) % self.stackSize
        self.buffer = np.zeros((self.stackSize, self.height, self.width))

    def clearBuffer(self):
        self.tail = self.stackSize - 1
        self.head = (self.tail + 1) % self.stackSize
        self.buffer = np.zeros((self.stackSize, self.height, self.width))

    def addFrame(self, newFrame: np.array):
        self.tail = (self.tail + 1) % self.stackSize
        self.head = (self.tail + 1) % self.stackSize
        self.buffer[self.tail] = newFrame

    def replaceFrameAt(self, index: int, newFrame: np.array):
        idx = (self.tail + 1 + index) % self.stackSize
        self.buffer[idx] = newFrame

    def returnNewestFrame(self):
        return self.buffer[self.tail]

    def returnOldestFrame(self):
        return self.buffer[self.head]

    def returnFrameAt(self, index: int):
        idx = (self.tail + 1 + index) % self.stackSize
        return self.buffer[idx]

    def changeROI(self, newROI: ROI):
        self.height = newROI.height
        self.width = newROI.width
        self.clearBuffer()

    def changeStacksize(self, newStacksize: int):
        stackDifference = newStacksize - self.stackSize
        self.head = (self.tail + 1) % self.stackSize
        if stackDifference > 0:
            emptyFrames = np.zeros((stackDifference, self.height, self.width))
            self.buffer = np.insert(self.buffer, self.head, emptyFrames, axis=0)
        elif stackDifference < 0:
            if self.tail > self.head:
                self.buffer = self.buffer[
                    (self.tail - newStacksize) + 1 : self.tail + 1
                ]
            else:
                self.buffer = np.delete(
                    self.buffer,
                    np.s_[
                        self.tail + 1 : (self.tail + 1 - stackDifference)
                        if (self.tail + 1 - stackDifference) <= self.stackSize - 1
                        else None
                    ],
                    axis=0,
                )
        else:
            pass
        self.stackSize = newStacksize
        if self.head < self.tail:
            self.tail = (self.tail + stackDifference) % self.stackSize
        self.head = (self.tail + 1) % self.stackSize


roi = ROI(height=3, width=2)

newROI = ROI(height=4, width=7)

array_1 = np.zeros((roi.height, roi.width)) + 1

array_2 = np.zeros((roi.height, roi.width)) + 2

array_3 = np.zeros((roi.height, roi.width)) + 3


frameBuffer = Framebuffer(22, roi=roi)

print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)
frameBuffer.addFrame(array_1)

frameBuffer.addFrame(array_2)

frameBuffer.addFrame(array_3)
frameBuffer.addFrame(array_2)

print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)

frameBuffer.changeStacksize(7)


print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)
frameBuffer.changeStacksize(4)
print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)

frameBuffer.addFrame(array_1)

print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)
frameBuffer.changeStacksize(9)


print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)

frameBuffer.changeStacksize(9)


print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)


frameBuffer.changeROI(newROI=newROI)

print(frameBuffer.buffer, frameBuffer.buffer.shape)
print("Head", frameBuffer.head, "Tail", frameBuffer.tail)
