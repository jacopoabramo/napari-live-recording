from napari_live_recording.Cameras.ICamera import ICamera, CameraError
from napari_live_recording.Cameras.TestCamera import TestCamera, CAM_TEST
from napari_live_recording.Cameras.CameraOpenCV import CameraOpenCV, CAM_OPENCV
from napari_live_recording.Cameras.CameraXimea import CameraXimea, CAM_XIMEA

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