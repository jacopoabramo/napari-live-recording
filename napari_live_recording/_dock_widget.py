# Plugin imports
from typing import Any
from napari._qt.qthreading import WorkerBase, WorkerBaseSignals
from PyQt5.QtWidgets import QComboBox
from napari_plugin_engine import napari_hook_implementation
import numpy as np
from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton
from qtpy.QtCore import Signal

# Camera classes import
from abc import ABC, abstractmethod
import cv2
from platform import system

# Ximea camera support only provided by downloading the Ximea Software package
# see https://www.ximea.com/support/wiki/apis/APIs for more informations
from ximea.xiapi import Camera as XiCamera, Xi_error
from ximea.xiapi import Image as XiImage

CAM_OPENCV = "Default Camera (OpenCV)"
CAM_XIMEA  = "Ximea xiB-64"

class CameraError(Exception):
    def __init__(self, error: str) -> None:
        self.error_description = error
    
    def __str__(self) -> str:
        return self.error_description

class ICamera(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.camera_name = "ICamera"

    @abstractmethod
    def __del__(self) -> None:
        pass

    @abstractmethod
    def open_device(self) -> bool:
        pass
    
    @abstractmethod
    def close_device(self) -> None:
        pass

    @abstractmethod
    def capture_image(self) -> np.array:
        pass

    @abstractmethod
    def set_exposure(self, exposure) -> None:
        pass

    def get_name(self) -> str:
        return self.camera_name

class CameraOpenCV(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.video_capture = cv2.VideoCapture(0, cv2.CAP_ANY)
        self.camera_name = CAM_OPENCV

        # Windows platforms support discrete exposure times
        # These are mapped using a dictionary
        self.exposure_dict = {
            "1 s"      :  0,
            "500 ms"   : -1,
            "250 ms"   : -2,
            "125 ms"   : -3,
            "62.5 ms"  : -4,
            "31.3 ms"  : -5,
            "15.6 ms"  : -6,
            "7.8 ms"   : -7,
            "3.9 ms"   : -8,
            "2 ms"     : -9,
            "976.6 us" : -10,
            "488.3 us" : -11,
            "244.1 us" : -12,
            "122.1 us" : -13
        }

    def __del__(self) -> None:
        self.video_capture.release()
        del self.video_capture
    
    def __str__(self) -> str:
        return CAM_OPENCV
    
    def open_device(self) -> bool:
        if not self.video_capture.isOpened():
            return self.video_capture.open(0, cv2.CAP_ANY)
    
    def close_device(self) -> None:
        self.video_capture.release()
    
    def capture_image(self) -> np.array:
        _ , img = self.video_capture.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.waitKey(1)
        return img

    def set_exposure(self, exposure) -> None:
        if system() == "Windows":
            exposure = self.exposure_dict[exposure]
        self.video_capture.set(cv2.CAP_PROP_EXPOSURE, exposure)

class CameraXimea(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.camera = XiCamera()
        self.image = XiImage()
        self.camera_name = CAM_XIMEA
    
    def __del__(self) -> None:
        self.close_device()
    
    def __str__(self) -> str:
        return CAM_XIMEA
    
    def open_device(self) -> bool:
        try:
            self.camera.open_device()
        except Xi_error:
            return False
        return True

    def close_device(self) -> None:
        try:
            self.camera.stop_acquisition()
            self.camera.close_device()
            del self.camera
        except Xi_error: # Camera not connected or already closed
            pass
    
    def capture_image(self) -> np.array:
        try:
            self.camera.get_image(self.image)
            data = self.image.get_image_data_numpy()
        except Xi_error:
            data = None
        return data

    def set_exposure(self, exposure) -> None:
        try:
            self.camera.set_exposure(exposure)
        except Xi_error:
            pass

supported_cameras = {
    CAM_OPENCV : CameraOpenCV,
    CAM_XIMEA  : CameraXimea
}

class LiveWorkerSignals(WorkerBaseSignals):
    yielded = Signal(object)

class LiveWorker(WorkerBase):
    def __init__(self, camera : ICamera) -> None:
        super().__init__(SignalsClass=LiveWorkerSignals)
        self.camera = camera
    
    def work(self):
        while not self.abort_requested:
            yield self.camera.capture_image()

    def _acquire(self):
        """
        Acquires a grayscale image from the selected camera and returns it.

        Parameters
        ----------
            None

        Returns
        -------
            2d numpy array / image
        """
        if self.camera is None:
            return None
        return self.camera.capture_image()

class LiveRecordingWidget(QWidget):
    def __init__(self, napari_viewer) -> None:
        super().__init__()
        self.viewer = napari_viewer
        self.camera = None
        self.live_worker = LiveWorker(self.camera)
        self.live_worker.yielded.connect(self._update_layer)

        self.camera_connect_button = QPushButton("Connect camera")
        self.camera_connect_button.clicked.connect(self._on_connect_clicked)
        self.camera_connect_button.setEnabled(False)
        self.is_connect = False

        self.camera_live_button = QPushButton("Start live recording")
        self.camera_live_button.clicked.connect(self._on_live_clicked)
        self.camera_live_button.setEnabled(False)
        self.is_live = False

        self.camera_selection_combobox = QComboBox()
        self.camera_selection_combobox.addItem("Select camera")

        self.camera_selection_combobox.addItems(list(supported_cameras.keys()))
        self.camera_selection_combobox.currentIndexChanged.connect(self._on_cam_type_changed)

        self.setLayout(QGridLayout(self))
        self.layout().addWidget(self.camera_selection_combobox, 0, 0)
        self.layout().addWidget(self.camera_connect_button, 1, 0)
        self.layout().addWidget(self.camera_live_button, 1, 1)

    def _update_layer(self, data):
        for name, image in data.items():
            if image is not None:
                try:
                    self.viewer.layers[name].data = image
                except KeyError: # add layer if not existing
                    self.viewer.add_image(image, name = "Live recording")
    
    def _on_cam_type_changed(self, index):
        self.camera_connect_button.setEnabled(bool(index))
        camera_name = self.camera_selection_combobox.currentText()
        try: 
            camera_type = supported_cameras[camera_name]
            self.camera = camera_type() # constructs object of class specified by camera_name
        except KeyError:
            raise CameraError("Unsupported camera selected")
                        
    
    def _on_connect_clicked(self):
        if not self.is_connect:
            if self.camera.open_device():
                self.camera_connect_button.setText("Disconnect camera")
                self.is_connect = True
            else:
                raise CameraError(f"Error in opening {self.camera.get_name()}")
        else:
            self.camera_connect_button.setText("Connect camera")
            self.is_connect = False
            self.camera.close_device()

    def _on_live_clicked(self):
        if not self.is_live:
            self.camera_live_button.setText("Stop live recording")
            self.is_live = True
            self.live_worker.start()
        else:
            self.camera_live_button.setText("Start live recording")
            self.is_live = False
            self.live_worker.quit()

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [LiveRecordingWidget]
