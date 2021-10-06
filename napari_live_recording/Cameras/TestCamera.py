from napari_live_recording.Cameras.ICamera import ICamera
import numpy as np

CAM_TEST = "Widget dummy camera"

class TestCamera(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.camera_name = CAM_TEST
        self.roi = [500, 500]
    
    def __del__(self) -> None:
        return super().__del__()

    def open_device(self) -> bool:
        print("Dummy camera opened!")
        return True
    
    def close_device(self) -> None:
        print("Dummy camera closed!")
    
    def capture_image(self) -> np.array:
        print("Acquiring dummy image!")
        return np.random.randint(low=0, high=2**8, size=tuple(self.roi), dtype="uint8")
    
    def set_exposure(self, exposure) -> None:
        print(f"Dummy camera exposure set to {exposure}")

    def set_roi(self, roi : list) -> None:
        self.roi = roi
    
    def get_roi(self) -> list:
        return self.roi