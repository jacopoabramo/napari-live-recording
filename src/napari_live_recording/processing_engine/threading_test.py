import numpy as np
import threading
from frame_buffer import Framebuffer
import time

shape = (3, 3)
framebuffer = Framebuffer(7, shape)
ls = []


def producer(framebuffer: Framebuffer):
    idx = 0
    while idx < 11:
        time.sleep(0.1)
        frame = np.zeros(shape=shape) + idx + 1
        framebuffer.addFrame(frame)
        print(framebuffer.buffer)
        print("Producer")
        idx += 1


def consumer(framebuffer: Framebuffer):
    print(framebuffer.empty)
    while framebuffer.empty:
        pass
    while not framebuffer.empty:
        time.sleep(0.11)
        frame = framebuffer.popOldestFrame()
        ls.append(frame)
        print("Consumer")
        print(framebuffer.buffer)


threadConsumer = threading.Thread(target=consumer, args=(framebuffer,))
threadProducer = threading.Thread(target=producer, args=(framebuffer,))

threadProducer.start()

threadConsumer.start()


threadProducer.join()
threadConsumer.join()

print(ls)
