# Plugin imports
from napari._qt.qthreading import thread_worker
from PyQt5.QtWidgets import QComboBox, QFileDialog, QLabel, QSpinBox
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton
from imageio import mimwrite
from napari_live_recording.Cameras import *
from napari_live_recording.functions import *

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
