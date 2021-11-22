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
            self.roi    = None
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
                self.roi = CameraROI(
                    offset_x    = self.camera.get_offsetX(),
                    ofs_x_step  = self.camera.get_offsetX_increment(),
                    offset_y    = self.camera.get_offsetY(),
                    ofs_y_step  = self.camera.get_offsetY_increment(),
                    width       = self.camera.get_width(),
                    width_step  = self.camera.get_width_increment(),
                    height      = self.camera.get_height(),
                    height_step = self.camera.get_height_increment()                   
                )
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
                # to properly update the Ximea ROI
                # first set the height and width
                # make sure that a minimum step is calculated
                width_incr = self.camera.get_width_increment()
                height_incr = self.camera.get_height_increment()
                self.roi.width = (round(roi.width/width_incr)*width_incr if (roi.width % width_incr) != 0 else roi.width)
                self.roi.height = (round(roi.height/height_incr)*height_incr if (roi.height % height_incr) != 0 else roi.height)

                self.camera.set_width(self.roi.width)
                self.camera.set_height(self.roi.height)

                # now we can properly update offset X and Y
                offx_incr  = self.camera.get_offsetX_increment()
                offy_incr  = self.camera.get_offsetY_increment()
                self.roi.offset_x = (round(roi.offset_x / offx_incr)*offx_incr if (roi.offset_x % offx_incr) != 0 else roi.offset_x)
                self.roi.offset_y = (round(roi.offset_y / offy_incr)*offy_incr if (roi.offset_y % offy_incr) != 0 else roi.offset_y)

                self.camera.set_offsetX(self.roi.offset_x)
                self.camera.set_offsetY(self.roi.offset_y)

                # we also update the single increment steps for each value of the ROI
                self.roi.ofs_x_step  = offx_incr
                self.roi.ofs_y_step  = offy_incr
                self.roi.width_step  = width_incr
                self.roi.height_step = height_incr 

        def get_roi(self) -> CameraROI:
            return self.roi
        
        def get_sensor_range(self) -> CameraROI:
            return CameraROI(offset_x    = 0,
                            offset_y     = 0,
                            width        = 1280,
                            height       = 864,
                            ofs_x_step   = 32,
                            ofs_y_step   = 2,
                            width_step   = 32, 
                            height_step  = 4)
        
        def set_full_frame(self) -> CameraROI:
            with _camera_disabled(self):
                self.camera.set_offsetX(0)
                self.camera.set_offsetY(0)
                self.camera.set_width(1280)
                self.camera.set_height(864)
            self.roi = CameraROI(offset_x    = 0,
                                 offset_y    = 0,
                                 width       = 1280,
                                 height      = 864,
                                 ofs_x_step  = 32,
                                 ofs_y_step  = 2,
                                 width_step  = 32, 
                                 height_step = 4)
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
