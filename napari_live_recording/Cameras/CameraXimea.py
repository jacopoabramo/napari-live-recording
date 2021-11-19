from .ICamera import CameraROI, ICamera

# Ximea camera support only provided by downloading the Ximea Software package
# see https://www.ximea.com/support/wiki/apis/APIs for more informations
try:
    from ximea.xiapi import Camera as XiCamera, Xi_error
    from ximea.xiapi import Image as XiImage
    from contextlib import contextmanager
    import numpy as np

    CAM_XIMEA = "Ximea"
    CONVERSION_FACTOR = 1000
    DEFAULT_ROI = CameraROI(offset_x=0,
                            offset_y=0,
                            width = 1280,
                            height = 864,
                            ofs_x_step = 32,
                            ofs_y_step = 2,
                            width_step = 32, 
                            height_step = 4)
    

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
            self.exposure = 1 * CONVERSION_FACTOR    # ms, default exposure
            self.sleep_time = 1 / CONVERSION_FACTOR  # ms
            self.dict_pixel_formats = {
                "16-bit gray": ["XI_MONO16", np.uint16], # default
                "8-bit gray" : ["XI_MONO8", np.uint8]
            }
            self.format = self.dict_pixel_formats["16-bit gray"]
            self.roi = DEFAULT_ROI
            self.frame_counter = 0

        def __del__(self) -> None:
            try:
                self.close_device()
            except Xi_error:
                pass

        def __str__(self) -> str:
            return CAM_XIMEA

        def open_device(self) -> bool:
            try:
                self.camera.open_device()
                self.camera.set_imgdataformat(self.format[0])
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
        
        def get_available_pixel_formats(self) -> list:
            return list(self.dict_pixel_formats.keys())
        
        def set_pixel_format(self, format) -> None:
            self.format = self.dict_pixel_formats[format]
            with _camera_disabled(self):
                self.camera.set_imgdataformat(self.format[0])

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

        def set_roi(self, roi: CameraROI) -> None:
            with _camera_disabled(self):
                self.camera.set_offsetX(0)            
                self.camera.set_offsetY(0)
                self.camera.set_width(roi.width)        
                self.camera.set_height(roi.height)
                self.camera.set_offsetX(roi.offset_x)            
                self.camera.set_offsetY(roi.offset_y)
                self.roi = roi

        def get_roi(self) -> CameraROI:
            return self.roi
        
        def get_sensor_range(self) -> CameraROI:
            return DEFAULT_ROI
        
        def set_full_frame(self) -> CameraROI:
            with _camera_disabled(self):
                self.camera.set_offsetX(DEFAULT_ROI.offset_x)            
                self.camera.set_offsetY(DEFAULT_ROI.offset_y)
                self.camera.set_width(DEFAULT_ROI.width)        
                self.camera.set_height(DEFAULT_ROI.height)
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
