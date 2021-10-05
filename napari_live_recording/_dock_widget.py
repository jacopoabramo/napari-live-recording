# Plugin imports
from PyQt5 import QtGui
from napari._qt.qthreading import thread_worker
from PyQt5.QtWidgets import QComboBox, QFileDialog, QLabel, QSpinBox
from napari_plugin_engine import napari_hook_implementation
import numpy as np
from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton
from imageio import mimwrite

# Camera classes import
from abc import ABC, abstractmethod
import cv2
from platform import system
from time import sleep

# Ximea camera support only provided by downloading the Ximea Software package
# see https://www.ximea.com/support/wiki/apis/APIs for more informations
from ximea.xiapi import Camera as XiCamera, Xi_error
from ximea.xiapi import Image as XiImage

CAM_TEST   = "Widget dummy camera"
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
        self.roi = []

    @abstractmethod
    def __del__(self) -> None:
        return super().__del__()

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

    @abstractmethod
    def set_roi(self, roi : list) -> None:
        self.roi = roi

    @abstractmethod
    def get_roi(self) -> list:
        return self.roi

    def get_name(self) -> str:
        return self.camera_name

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

class CameraOpenCV(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.camera_idx = 0
        self.camera_api = cv2.CAP_ANY
        self.camera = None
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
        if self.camera is not None:
            self.camera.release()
    
    def __str__(self) -> str:
        return CAM_OPENCV
    
    def open_device(self) -> bool:
        if self.camera is None:
            self.camera = cv2.VideoCapture(self.camera_idx, self.camera_api)
            return self.camera.isOpened()
        return self.camera.open(self.camera_idx, self.camera_api)
    
    def close_device(self) -> None:
        self.camera.release()
    
    def capture_image(self) -> np.array:
        _ , img = self.camera.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.waitKey(1)
        return img

    def set_exposure(self, exposure) -> None:
        if system() == "Windows":
            exposure = self.exposure_dict[exposure]
        self.camera.set(cv2.CAP_PROP_EXPOSURE, exposure)

class CameraXimea(ICamera):
    def __init__(self) -> None:
        super().__init__()
        self.camera = XiCamera()
        self.image = XiImage()
        self.camera_name = CAM_XIMEA
        self.roi = [500, 500]
    
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
            self.camera.start_acquisition()
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
        sleep(0.01)
        return data

    def set_exposure(self, exposure) -> None:
        try:
            self.camera.set_exposure(exposure)
        except Xi_error:
            pass
    
    def set_roi(self, roi : list) -> None:
        self.roi = roi

    def get_roi(self) -> list:
        return self.roi

supported_cameras = {
    CAM_TEST   : TestCamera,
    CAM_OPENCV : CameraOpenCV,
    CAM_XIMEA  : CameraXimea
}

def acquire(camera : ICamera):
    """
    Acquires a grayscale image from the selected camera and returns it.
        
    Parameters
    ----------
        camera (ICamera) : interface camera object

    Returns
    -------
        2d numpy array / image
    """
    if camera is None:
        return None
    return camera.capture_image()

class LiveRecording(QWidget):
    def __init__(self, napari_viewer) -> None:
        super().__init__()
        self.viewer = napari_viewer
        self.camera = None
        self.live_worker = None
        self.record_worker = None

        self.camera_connect_button = QPushButton("Connect camera", self)
        self.camera_connect_button.clicked.connect(self._on_connect_clicked)
        self.camera_connect_button.setEnabled(False)
        self.is_connect = False

        self.camera_live_button = QPushButton("Start live recording", self)
        self.camera_live_button.clicked.connect(self._on_live_clicked)
        self.camera_live_button.setEnabled(False)
        self.is_live = False

        self.camera_selection_combobox = QComboBox(self)
        self.camera_selection_combobox.addItem("Select camera")
        self.camera_selection_combobox.addItems(list(supported_cameras.keys()))
        self.camera_selection_combobox.currentIndexChanged.connect(self._on_cam_type_changed)
        
        self.camera_exposure_label  = None
        self.camera_exposure_widget = None

        self.camera_record_button = QPushButton("Record video", self)
        self.camera_record_button.clicked.connect(self._on_record_clicked)
        self.camera_record_button.setEnabled(False)

        self.camera_record_buffer_label = QLabel("Frame buffer size", self)
        self.camera_record_spinbox = QSpinBox(self)
        self.camera_record_spinbox.setMaximum(10000)
        self.camera_record_spinbox.setMinimum(10)
        self.camera_record_spinbox.setValue(10)
        self.camera_record_spinbox.setEnabled(False)

        self.setLayout(QGridLayout(self))
        self.layout().addWidget(self.camera_selection_combobox, 0, 0)
        self.layout().addWidget(self.camera_connect_button, 1, 0)
        self.layout().addWidget(self.camera_live_button, 1, 1)
        self.layout().addWidget(self.camera_record_button, 2, 0, 1, 2)
        self.layout().addWidget(self.camera_record_buffer_label, 3, 0)
        self.layout().addWidget(self.camera_record_spinbox, 3, 1)
    
    def _on_cam_type_changed(self, index):
        self.camera_connect_button.setEnabled(bool(index))
        camera_name = self.camera_selection_combobox.currentText()
        try:
            camera_type = supported_cameras[camera_name]
            self.camera = camera_type() # constructs object of class specified by camera_name
            if isinstance(self.camera, CameraOpenCV):
                self._add_opencv_exposure()
            else:
                self._add_camera_exposure()
        except KeyError: # unsupported camera found
            if self.camera_exposure_label is not None:
                self._delete_exposure_widget()
                self.layout().removeWidget(self.camera_exposure_label)
                self.camera_exposure_label.deleteLater()
                self.camera_exposure_label = None
            if index > 0: # skipping indexes of selection string
                raise CameraError("Unsupported camera selected")
    
    def _delete_exposure_widget(self):
        if self.camera_exposure_label is not None:
            self.layout().removeWidget(self.camera_exposure_label)
            self.camera_exposure_widget.deleteLater()
            self.camera_exposure_widget = None
        if self.camera_exposure_widget is not None:
            if isinstance(self.camera_exposure_widget, QComboBox):
                self.camera_exposure_widget.currentTextChanged.disconnect(self._on_exposure_changed)
            else:
                self.camera_exposure_widget.valueChanged.disconnect(self._on_exposure_changed)
            self.layout().removeWidget(self.camera_exposure_widget)
            self.camera_exposure_widget.deleteLater()
            self.camera_exposure_widget = None
    
    def _set_widgets_enabled(self, enabled : bool):
        self.camera_live_button.setEnabled(enabled)
        self.camera_record_button.setEnabled(enabled)
        self.camera_record_spinbox.setEnabled(enabled)

    def _add_opencv_exposure(self):
        self._delete_exposure_widget()
        self.camera_exposure_label = QLabel("Exposure", self)
        self.layout().addWidget(self.camera_exposure_label, 4, 0)
        self.camera_exposure_widget = QComboBox(self)
        self.camera_exposure_widget.addItems(list(self.camera.exposure_dict.keys()))
        self.camera_exposure_widget.currentTextChanged.connect(self._on_exposure_changed)
        self.layout().addWidget(self.camera_exposure_widget, 4, 1)


    def _add_camera_exposure(self):
        self._delete_exposure_widget()
        self.camera_exposure_label = QLabel("Exposure (\u03BCs)", self)
        self.layout().addWidget(self.camera_exposure_label, 4, 0)
        self.camera_exposure_widget = QSpinBox(self)
        self.camera_exposure_widget.setMaximum(5000)
        self.camera_exposure_widget.setMinimum(20)
        self.camera_exposure_widget.setValue(200)
        self.camera_exposure_widget.valueChanged.connect(self._on_exposure_changed)
        self.layout().addWidget(self.camera_exposure_widget, 4, 1)
    
    def _on_connect_clicked(self):
        if not self.is_connect:
            if self.camera.open_device():
                self.camera_connect_button.setText("Disconnect camera")
                self.is_connect = True
                self._set_widgets_enabled(True)
            else:
                raise CameraError(f"Error in opening {self.camera.get_name()}")
        else:
            self.camera.close_device()
            self.camera_connect_button.setText("Connect camera")
            self.is_connect = False
            self._set_widgets_enabled(False)

    def _on_live_clicked(self):
        # inspired by https://github.com/haesleinhuepf/napari-webcam
        def update_layer(data):
                if data is not None:
                    try:
                        # replace layer if it exists already
                        self.viewer.layers["Live recording"].data = data
                    except KeyError:
                        # add missing layer (only needed on first acquisition)
                        self.viewer.add_image(data, name="Live recording")
        
        # inspired by https://github.com/haesleinhuepf/napari-webcam 
        @thread_worker(connect={"yielded" : update_layer})
        def yield_acquire_images_forever():
            while True: # infinite loop, quit signal makes it stop
                yield acquire(camera=self.camera)

        if not isinstance(self.camera, TestCamera):
            if self.live_worker is None:
                self.live_worker = yield_acquire_images_forever()

            if not self.is_live:
                self.camera_live_button.setText("Stop live recording")
                self.is_live = True
            else:
                self.camera_live_button.setText("Start live recording")
                self.is_live = False
                self.live_worker.quit()
                del self.live_worker
                self.live_worker = None
        else:
            if not self.is_live:
                self.camera_live_button.setText("Stop live recording")
                self.is_live = True
                print("Dummy self record started!")
            else:
                self.camera_live_button.setText("Start live recording")
                self.is_live = False
                print("Dummy self record stopped!")

    def _on_exposure_changed(self, exposure):
        if self.is_live:
            self.live_worker.pause()
            self.camera.set_exposure(exposure)
            self.live_worker.resume()
        else:
            self.camera.set_exposure(exposure)

    def _on_record_clicked(self):
        @thread_worker
        def acquire_stack_images(stack_size, file_path):
            stack = [None] * stack_size
            for idx in range(0, stack_size):
                stack[idx] = self.camera.capture_image()
            mimwrite(file_path, stack)

        dlg = QFileDialog(self)
        dlg.setDefaultSuffix(".tiff")
        video_name = dlg.getSaveFileName(self, caption="Save video", filter="TIFF stack (.tif)")[0]
        if video_name != "":
            video_name += ".tiff" if not video_name.endswith('.tiff') else ""
            self.record_worker = acquire_stack_images(self.camera_record_spinbox.value(), video_name)
            self.record_worker.start()
        else:
            print("No file name specified!")
        pass

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [LiveRecording]
