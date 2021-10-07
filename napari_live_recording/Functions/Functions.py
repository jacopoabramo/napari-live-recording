from napari_live_recording.Cameras.ICamera import ICamera
import numpy as np

def average_image_stack(stack : list) -> np.array:
    """Calculates the average of a stack of images

    :param stack: input image stack
    :type stack: list
    :return: image representing the average of the stack
    :rtype: numpy.array
    """
    # sum all averaged images into an accumulator
    accumulator = np.zeros(stack[0].shape, np.float)
    for image in stack:
        accumulator += np.array(image, np.float)
    accumulator /= len(stack)

    # return rounded accumulator
    return np.array(np.round(accumulator), "uint8")
