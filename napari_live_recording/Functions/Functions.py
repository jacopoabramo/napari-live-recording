from numpy.lib.type_check import imag
from napari_live_recording.Cameras.ICamera import ICamera
import numpy as np

def average_image_stack(stack : np.array, stack_size : int) -> np.array:
    """Calculates the average of a stack of images

    :param stack: input image stack
    :type stack: numpy.array stack
    :param stack_size: input stack size
    :type stack: int
    :return: image representing the average of the stack
    :rtype: numpy.array
    """
    # sum all averaged images into an accumulator
    accumulator = np.zeros(stack[0].shape, np.float)
    for idx in range(0, stack_size):
        accumulator += stack[idx, :, :]
    accumulator /= stack_size

    # return rounded accumulator
    return np.array(np.round(accumulator), "uint16")
