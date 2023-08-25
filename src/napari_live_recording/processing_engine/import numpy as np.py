import numpy as np
import threading
from frame_buffer import Framebuffer

shape = (3, 3)
framebuffer = Framebuffer(4, shape)
array_1 = np.zeros((shape[0], shape[1])) + 1

array_2 = np.zeros((shape[0], shape[1])) + 2

array_3 = np.zeros((shape[0], shape[1])) + 3
array_4 = np.zeros((shape[0], shape[1])) + 4
array_5 = np.zeros((shape[0], shape[1])) + 5
array_6 = np.zeros((shape[0], shape[1])) + 6
array_7 = np.zeros((shape[0], shape[1])) + 7
array_8 = np.zeros((shape[0], shape[1])) + 8
array_9 = np.zeros((shape[0], shape[1])) + 9
array_10 = np.zeros((shape[0], shape[1])) + 10
array_11 = np.zeros((shape[0], shape[1])) + 11
framebuffer.addFrame(array_1)
framebuffer.addFrame(array_2)
framebuffer.addFrame(array_3)
# framebuffer.addFrame(array_4)
# framebuffer.addFrame(array_5)
# framebuffer.addFrame(array_6)
# framebuffer.addFrame(array_7)
# framebuffer.clearBuffer()

# print(framebuffer.buffer)
# print("oldest", framebuffer.returnOldestFrame())
# print("NewArray", framebuffer.buffer)
# print("popOldest", framebuffer.popOldestFrame())
# print("NewArray", framebuffer.buffer)
# print("oldest", framebuffer.returnOldestFrame())
# print("NewArray", framebuffer.buffer)
# print("popOldest", framebuffer.popOldestFrame())
# print("NewArray", framebuffer.buffer)

framebuffer.addFrame(array_4)
framebuffer.addFrame(array_5)
# print("NewArray", framebuffer.buffer)

# print("oldest", framebuffer.returnOldestFrame())
# print("NewArray", framebuffer.buffer)
# print("popOldest", framebuffer.popOldestFrame())
# print("NewArray", framebuffer.buffer)
framebuffer.addFrame(array_6)
# print("NewArray", framebuffer.buffer)
# print("oldest", framebuffer.returnOldestFrame())
# print("NewArray", framebuffer.buffer)
# print("popOldest", framebuffer.popOldestFrame())
# print("NewArray", framebuffer.buffer)
framebuffer.addFrame(array_7)
# print("popOldest", framebuffer.popOldestFrame())
print("NewArray", framebuffer.buffer)
print("oldest", framebuffer.returnOldestFrame())
print("NewArray", framebuffer.buffer)
print("popOldest", framebuffer.popOldestFrame())
print("NewArray", framebuffer.buffer)
framebuffer.addFrame(array_8)
print("NewArray", framebuffer.buffer)
print("popOldest", framebuffer.popOldestFrame())
print("NewArray", framebuffer.buffer)
framebuffer.addFrame(array_9)
print("NewArray", framebuffer.buffer)

framebuffer.addFrame(array_10)
print("NewArray", framebuffer.buffer)
framebuffer.addFrame(array_11)
print("NewArray", framebuffer.buffer)
print("popOldest", framebuffer.popOldestFrame())
print(framebuffer.empty)
print("NewArray", framebuffer.buffer)

print("popOldest", framebuffer.popOldestFrame())
print("lentght", framebuffer.length)
print("NewArray", framebuffer.buffer)

print("popOldest", framebuffer.popOldestFrame())
print("length", framebuffer.length)
print("NewArray", framebuffer.buffer)

print("popOldest", framebuffer.popOldestFrame())
print("length", framebuffer.length)
print("NewArray", framebuffer.buffer)


# array = np.array(
#     [
#         [[0, 0, 0], [0, 0, 0]],
#         [[1, 1, 2], [1, 2, 3]],
#         [[1, 1, 2], [1, 2, 3]],
#         [[0, 1, 2], [1, 2, 3]],
#     ]
# )
# print(array, array.shape)
# print(array[...])
# # print(np.any(np.any(array, axis=2), axis=1))
# # print(np.nonzero(np.any(np.any(array, axis=2), axis=1)))
# # print(np.any(np.array([0, 0, 0])))


array = np.array([1, 2, 3, 4])
i = np.where(array == 2)[0][0]
print(i)


thread1 = threading.Thread()
thread2 = threading.Thread()
