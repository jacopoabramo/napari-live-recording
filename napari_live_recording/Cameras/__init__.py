from .ICamera import *
from .TestCamera import *
from .CameraOpenCV import *
from .CameraXimea import *

supported_cameras = {
    CAM_TEST   : TestCamera,
    CAM_OPENCV : CameraOpenCV,
    CAM_XIMEA  : CameraXimea
}

__all__ = [
    "ICamera",
    "CameraError",
    # list of supported cameras below
    "TestCamera",
    "CameraOpenCV",
    "CameraXimea",
    # list of supported cameras above
    "supported_cameras",
]