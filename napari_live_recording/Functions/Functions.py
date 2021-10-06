from napari_live_recording.Cameras.ICamera import ICamera

def acquire(camera : ICamera):
    """
    Acquires a grayscale image from the selected camera and returns it.
        
    Parameters
    ----------
        camera (ICamera) : interface camera object

    Returns
    -------
        2d numpy array / image
    """
    if camera is None:
        return None
    return camera.capture_image()