from .ICamera import ICamera, CameraError
from .TestCamera import TestCamera, CAM_TEST
from .CameraOpenCV import CameraOpenCV, CAM_OPENCV
from .CameraXimea import CameraXimea, CAM_XIMEA

supported_cameras = {
    CAM_TEST   : TestCamera,
    CAM_OPENCV : CameraOpenCV,
    CAM_XIMEA  : CameraXimea
}

__all__ = [
    "ICamera",
    "CameraError",
    "TestCamera",
    "CameraOpenCV",
    "CameraXimea",
    # insert new cameras below

    # insert new cameras above
    "supported_cameras",
]