from napari._qt.qthreading import WorkerBase
from PyQt5.QtWidgets import QComboBox
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton

from abc import ABC, abstractmethod
import cv2
from platform import system

class Camera(ABC):
    @abstractmethod
    def open_device(self):
        pass
    
    @abstractmethod
    def close_device(self):
        pass

    @abstractmethod
    def capture_image(self):
        pass

    @abstractmethod
    def set_exposure(self, exposure):
        pass

class CameraOpenCV(Camera):
    def __init__(self) -> None:
        super().__init__()
        self.video_capture = cv2.VideoCapture(0, cv2.CAP_ANY)
        self.system_name = system()

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
    
    def open_device(self):
        if not self.video_capture.isOpened():
            self.video_capture.open(0, cv2.CAP_ANY)
    
    def close_device(self):
        self.video_capture.release()
    
    def capture_image(self):
        _ , img = self.video_capture.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.waitKey(1)
        return img

    def set_exposure(self, exposure):
        if self.system_name == "Windows":
            exposure = self.exposure_dict[exposure]
        self.video_capture.set(cv2.CAP_PROP_EXPOSURE, exposure)

CAM_OPENCV = "Default Camera (OpenCV)"
# todo: Add CameraXimea class
# CAM_XIMEA  = "Ximea xiB-64"

supported_cameras = {
    CAM_OPENCV : CameraOpenCV,
}

class LiveWorker(WorkerBase):
    def __init__(self, camera : Camera) -> None:
        super().__init__()
        self.camera = camera

    def work(self):
        while not self.abort_requested:
            yield self._acquire()

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
        self.camera_selection_combobox.addItems(supported_cameras)
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
            camera_class = supported_cameras[camera_name]
            self.camera = camera_class() # constructs object of class specified by camera_name
        except KeyError:
            print("Unknown camera selected.")
            pass            
    
    def _on_connect_clicked(self):
        if not self.is_connect:
            self.camera_connect_button.setText("Disconnect camera")
            self.is_connect = True
            self.camera.open_device()
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
