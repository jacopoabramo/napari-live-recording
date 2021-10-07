from napari_live_recording.Cameras.ICamera import ICamera
import numpy as np

def acquire(camera : ICamera):
    """Acquires a grayscale image from the selected camera and returns it.
        
    Arguments
    ----------
        camera (ICamera) : interface camera object

    Returns
    -------
        2D numpy array (captured image)
    """
    # checking if camera object actually exists
    # if not making this check and an error occurs
    # no image will be returned
    if camera is None:
        return None
    return camera.capture_image()

def average_image_stack(stack : list) -> np.array:
    """Calculates the average of a stack of sequential images

    Arguments
    ----------
        stack (list) : stack of captured images

    Returns
    -------
        2D numpy array (average of image stack)
    """
    # sum all averaged images into an accumulator
    accumulator = np.zeros(stack[0].shape, np.float)
    for image in stack:
        accumulator += np.array(image, np.float)
    accumulator /= len(stack)

    # return rounded accumulator
    return np.array(np.round(accumulator), "uint8")
