Camera interface description
=============================

Each camera device is inherited by the generic ``ICamera``, which provides a series of abstract methods to implement your own device interface.

An example of such interfaces is provided by the class ``TestCamera``, which generates a waving grayscale image:

.. code-block:: python

    from .ICamera import ICamera
    import numpy as np
    from time import sleep

    CAM_TEST = "Widget dummy camera"

    class TestCamera(ICamera):
        def __init__(self) -> None:
            super().__init__()
            self.camera_name = CAM_TEST
            self.roi = [500, 500]
            self.fill_value = 0
            self.increase_factor = 1
        
        def __del__(self) -> None:
            return super().__del__()

        def open_device(self) -> bool:
            print("Dummy camera opened!")
            return True
        
        def close_device(self) -> None:
            print("Dummy camera closed!")
        
        def capture_image(self) -> np.array:
            img = np.full(shape=tuple(self.roi), fill_value = self.fill_value, dtype="uint8")
            if self.increase_factor > 0:
                if self.fill_value == 255:
                    self.increase_factor = -1
            else:
                if self.fill_value == 0:
                    self.increase_factor = 1
            self.fill_value += self.increase_factor
            sleep(0.01)
            return img

        
        def set_exposure(self, exposure) -> None:
            print(f"Dummy camera exposure set to {exposure}")

        def set_roi(self, roi : list) -> None:
            self.roi = roi
        
        def get_roi(self) -> list:
            return self.roi

The string ``CAM_TEST`` serves as an identifier of the device class. 