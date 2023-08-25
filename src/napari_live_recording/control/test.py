from napari_live_recording.control.devices.opencv import OpenCV
from napari_live_recording.control.frame_buffer import Framebuffer
import threading
import time
import numpy as np


camera = OpenCV("MyCam", 0)
camera.changeParameter("Pixel format", "Grayscale")
print(camera._roiShape)

framebuffer = Framebuffer(100, camera._roiShape)


def cameraFunc():
    while True:
        frame = camera.grabFrame()
        framebuffer.addFrame(frame)
        print("Running1")


def otherFunc():
    while True:
        # time.sleep(0.05)
        newestFrame = framebuffer.returnNewestFrame()
        # framebuffer.clearBuffer()
        print(framebuffer.returnNewestFrame())
        print("Running2")


def secondFunc():
    while True:
        frame = camera.grabFrame()
        framebuffer.addFrame(frame)
        print("Running3")
        print(framebuffer.returnNewestFrame())


def thirdFunc():
    while True:
        time.sleep(1)
        print("Running4")


cameraThread = threading.Thread(target=cameraFunc, daemon=True)

otherThread = threading.Thread(target=otherFunc, daemon=True)


secondThread = threading.Thread(target=secondFunc, daemon=True)
thirdThread = threading.Thread(target=thirdFunc, daemon=True)

array = np.empty(10)

print(array)


# import numpy as np
# import threading
# from napari_live_recording.common import ROI
# from napari_live_recording.control.devices.interface import ICamera


# class Framebuffer:
#     def __init__(self, stackSize: int, roi: ROI, allowOverwrite: bool = True) -> None:
#         self.stackSize = stackSize
#         self.allowOverwrite = allowOverwrite
#         self.shape = roi.pixelSizes
#         self.new = self.stackSize - 1
#         self.lock = threading.Lock()
#         self.old = (self.new + 1) % self.stackSize
#         self.buffer = np.zeros(shape=(self.stackSize,) + self.shape, dtype=np.uint32)

#     def clearBuffer(self):
#         try:
#             with self.lock:
#                 print("Clearing buffer")
#                 self.new = self.stackSize - 1
#                 self.old = (self.new + 1) % self.stackSize
#                 self.buffer = 0
#                 self.buffer = np.zeros(
#                     shape=(self.stackSize,) + self.shape, dtype=np.uint32
#                 )

#         except Exception as e:
#             print("Problems clearing the buffer", e)

#     def addFrame(self, newFrame: np.array):
#         try:
#             if self.full and not self.allowOverwrite:
#                 pass
#             else:
#                 if newFrame.shape == self.shape:
#                     with self.lock:
#                         self.new = (self.new + 1) % self.stackSize
#                         self.old = (self.new + 1) % self.stackSize
#                         self.buffer[self.new] = newFrame
#                 else:
#                     self.shape = newFrame.shape
#                     print("Shape changed")
#                     self.clearBuffer()
#         except TypeError:
#             pass

#     def popFrameLeft(self):
#         with self.lock:
#             frame = np.delete(self.buffer, self.old)
#         return frame

#     def replaceFrameAt(self, index: int, newFrame: np.array):
#         idx = (self.new + 1 + index) % self.stackSize
#         self.buffer[idx] = newFrame

#     def returnNewestFrame(self):
#         with self.lock:
#             return self.buffer[self.new]

#     def returnOldestFrame(self):
#         np.nonzero(self.buffer)
#         return self.buffer[self.old]

#     def returnFrameAt(self, index: int):
#         idx = (self.new + 1 + index) % self.stackSize
#         return self.buffer[idx]

#     def changeROI(self, newROI: ROI):
#         self.shape = newROI.pixelSizes
#         self.clearBuffer()

#     def changeStacksize(self, newStacksize: int):
#         stackDifference = newStacksize - self.stackSize
#         self.old = (self.new + 1) % self.stackSize
#         if stackDifference > 0:
#             emptyFrames = np.zeros(((stackDifference,) + self.shape))
#             self.buffer = np.insert(self.buffer, self.old, emptyFrames, axis=0)
#         elif stackDifference < 0:
#             if self.new > self.old:
#                 self.buffer = self.buffer[(self.new - newStacksize) + 1 : self.new + 1]
#             else:
#                 self.buffer = np.delete(
#                     self.buffer,
#                     np.s_[
#                         self.new + 1 : (self.new + 1 - stackDifference)
#                         if (self.new + 1 - stackDifference) <= self.stackSize - 1
#                         else None
#                     ],
#                     axis=0,
#                 )
#         else:
#             pass
#         self.stackSize = newStacksize
#         if self.old < self.new:
#             self.new = (self.new + stackDifference) % self.stackSize
#         self.old = (self.new + 1) % self.stackSize

#     @property
#     def full(self) -> bool:
#         return len(self) == self.stackSize


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
# print("OldestFrame")
# print(frameBuffer.returnOldestFrame())
# print(frameBuffer.buffer, frameBuffer.buffer.shape)
# print("old", frameBuffer.old, "new", frameBuffer.new)

# # print(
# #     "hdhfhdfhsdfhdhfo",
# #     # frameBuffer.popNewFrame(),
# #     frameBuffer.buffer[0],
# #     frameBuffer.buffer[1],
# #     frameBuffer.buffer[2],
# #     frameBuffer.buffer[3],
# # )
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
