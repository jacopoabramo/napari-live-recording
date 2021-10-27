supported_cameras = {}

from .ICamera import ICamera, CameraROI
from .CameraError import CameraError

from .TestCamera import TestCamera, CAM_TEST
supported_cameras[CAM_TEST] = TestCamera

try:
    from .CameraOpenCV import CameraOpenCV, CAM_OPENCV
except ImportError:
    pass
else:
    supported_cameras[CAM_OPENCV] = CameraOpenCV

try:
    from .CameraXimea import CameraXimea, CAM_XIMEA
except ImportError:
    pass
else:
    supported_cameras[CAM_XIMEA] = CameraXimea