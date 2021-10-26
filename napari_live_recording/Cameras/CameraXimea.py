from .ICamera import ICamera

# Ximea camera support only provided by downloading the Ximea Software package
# see https://www.ximea.com/support/wiki/apis/APIs for more informations
try:
    from ximea.xiapi import Camera as XiCamera, Xi_error
    from ximea.xiapi import Image as XiImage
    from contextlib import contextmanager
    from time import time
    import numpy as np

    CAM_XIMEA = "Ximea xiB-64"
    CONVERSION_FACTOR = 1000

    @contextmanager
    def _camera_disabled(camera):
        """Context manager to temporarily disable camera."""
        if camera.get_acquisition():
            try:
                camera.set_acquisition(False)
                yield camera
            finally:
                camera.set_acquisition(True)
        else:
            yield camera

    class CameraXimea(ICamera):

        def __init__(self) -> None:
            super().__init__()
            self.camera = XiCamera()
            self.image = XiImage()
            self.camera_name = CAM_XIMEA
            self.roi = [0, 0, 1280, 864]
            self.exposure = 1 * CONVERSION_FACTOR    # ms, default exposure
            self.sleep_time = 1 / CONVERSION_FACTOR  # ms
            self.pixel_formats = {
                "8-bit gray": "XI_MONO8",
                "16-bit gray": "XI_MONO16"
            }
            self.sensor_shape = (1280, 864)
            self.frame_counter = 0
            self.delta_time = 0

        def __del__(self) -> None:
            self.close_device()

        def __str__(self) -> str:
            return CAM_XIMEA

        def open_device(self) -> bool:
            try:
                self.camera.open_device()
                max_lut_idx = self.camera.get_LUTIndex_maximum()
                for idx in range(0, max_lut_idx):
                    self.camera.set_LUTIndex(idx)
                    self.camera.set_LUTValue(idx)
                self.camera.enable_LUTEnable()
                self.camera.set_exposure(self.exposure)
                self.camera.start_acquisition()
            except Xi_error:
                return False
            return True

        def close_device(self) -> None:
            try:
                self.camera.stop_acquisition()
                self.camera.close_device()
                del self.camera
            except Xi_error:  # Camera not connected or already closed
                pass

        def capture_image(self) -> np.array:
            try:
                self.camera.get_image(self.image)
                data = self.image.get_image_data_numpy()
                self.frame_counter += 1
            except Xi_error:
                data = None
            return data

        def set_exposure(self, exposure) -> None:
            try:
                self.exposure = exposure * CONVERSION_FACTOR
                self.sleep_time = exposure / CONVERSION_FACTOR
                self.camera.set_exposure_direct(self.exposure)
            except Xi_error:
                pass

        def set_roi(self, roi: list) -> None:
            # inspired from https://github.com/python-microscope/microscope/blob/master/microscope/cameras/ximea.py
            if ((roi[0] + roi[2] > self.sensor_shape[0]) or (roi[1] + roi[3]) > self.sensor_shape[1]):
                raise ValueError("ROI outside sensor boundaries")

            with _camera_disabled(self):
                self.camera.set_offsetX(0)            
                self.camera.set_offsetY(0)
                self.camera.set_width(roi[0])        
                self.camera.set_height(roi[1])
                self.camera.set_offsetX(roi[2])            
                self.camera.set_offsetY(roi[3])
                self.roi = roi

        def get_roi(self) -> list:
            return self.roi

        def get_acquisition(self) -> bool:
            return self.camera.get_acquisition_status()

        def set_acquisition(self, is_enabled) -> None:
            (self.camera.start_acquisition() if is_enabled else self.camera.stop_acquisition())
        
        def get_frames_per_second(self) -> int:
            frames = self.frame_counter
            self.frame_counter = 0
            return frames

except ImportError:
    pass
