from PyQt5 import QtCore
from napari._qt.qthreading import thread_worker
from PyQt5.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QLabel, QSpinBox, QVBoxLayout
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton
from imageio import mimwrite, imwrite
from napari_live_recording.Cameras import *
from napari_live_recording.Functions import *
from collections import deque
from time import time

class LiveRecording(QWidget):
    def __init__(self, napari_viewer) -> None:
        super().__init__()
        self.viewer = napari_viewer
        self.camera = None
        self.live_worker = None
        self.live_image_buffer = deque([], maxlen=10000)
        self.record_worker = None

        self.outer_layout = QVBoxLayout()
        self.options_layout = QGridLayout()
        self.roi_layout = QGridLayout()

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
        self.camera_record_spinbox.setValue(2000)
        self.camera_record_spinbox.setEnabled(False)

        self.special_function_checkbox = QCheckBox("Special function", self)
        self.special_function_checkbox.stateChanged.connect(self._on_special_function_enabled)

        self.special_function = None
        self.special_function_combobox = QComboBox(self)
        self.special_function_combobox.currentTextChanged.connect(self._on_special_function_changed)

        self.frames_per_second_label = QLabel("Frames Per Second (FPS)", self)
        self.frames_per_second_label.setAlignment(QtCore.Qt.AlignCenter)

        self.frames_per_second_line_edit = QLabel(self)
        self.frames_per_second_line_edit.setAlignment(QtCore.Qt.AlignCenter)

        self.options_layout.addWidget(self.camera_selection_combobox, 0, 0)
        self.options_layout.addWidget(self.camera_connect_button, 1, 0)
        self.options_layout.addWidget(self.camera_live_button, 1, 1)
        self.options_layout.addWidget(self.camera_record_button, 2, 0, 1, 2)
        self.options_layout.addWidget(self.camera_record_buffer_label, 3, 0)
        self.options_layout.addWidget(self.camera_record_spinbox, 3, 1)
        self.options_layout.addWidget(self.special_function_checkbox, 4, 0)
        self.options_layout.addWidget(self.special_function_combobox, 4, 1)
        self.options_layout.addWidget(self.frames_per_second_label, 5, 0)
        self.options_layout.addWidget(self.frames_per_second_line_edit, 5, 1)

        self.camera_roi_x_offset_label = QLabel("Offset X (px)", self)
        self.camera_roi_x_offset_label.setAlignment(QtCore.Qt.AlignCenter)

        self.camera_roi_x_offset_spinbox = QSpinBox(self)
        self.camera_roi_x_offset_spinbox.setRange(0, 1280)
        self.camera_roi_x_offset_spinbox.setSingleStep(32)
        self.camera_roi_x_offset_spinbox.setValue(0)

        self.camera_roi_y_offset_label = QLabel("Offset Y (px)", self)
        self.camera_roi_y_offset_label.setAlignment(QtCore.Qt.AlignCenter)

        self.camera_roi_y_offset_spinbox = QSpinBox(self)
        self.camera_roi_y_offset_spinbox.setRange(0, 64)
        self.camera_roi_y_offset_spinbox.setSingleStep(4)
        self.camera_roi_y_offset_spinbox.setValue(0)

        self.camera_roi_width_label = QLabel("Width (px)", self)
        self.camera_roi_width_label.setAlignment(QtCore.Qt.AlignCenter)

        self.camera_roi_width_spinbox = QSpinBox(self)
        self.camera_roi_width_spinbox.setRange(32, 1280)
        self.camera_roi_width_spinbox.setSingleStep(32)
        self.camera_roi_width_spinbox.setValue(1280)
        
        self.camera_roi_height_label = QLabel("Height (px)", self)
        self.camera_roi_height_label.setAlignment(QtCore.Qt.AlignCenter)

        self.camera_roi_height_spinbox = QSpinBox(self)
        self.camera_roi_height_spinbox.setRange(4, 864)
        self.camera_roi_height_spinbox.setSingleStep(4)
        self.camera_roi_height_spinbox.setValue(864)

        self.camera_roi_change_button = QPushButton("Set ROI", self)
        self.camera_roi_change_button.clicked.connect(self._on_roi_change_requested)
        self.camera_roi_change_button.setEnabled(False)

        self.roi_layout.addWidget(self.camera_roi_x_offset_label, 0, 0)
        self.roi_layout.addWidget(self.camera_roi_x_offset_spinbox, 0, 1)
        self.roi_layout.addWidget(self.camera_roi_y_offset_spinbox, 0, 2)
        self.roi_layout.addWidget(self.camera_roi_y_offset_label, 0, 3)

        self.roi_layout.addWidget(self.camera_roi_width_label, 1, 0)
        self.roi_layout.addWidget(self.camera_roi_width_spinbox, 1, 1)
        self.roi_layout.addWidget(self.camera_roi_height_spinbox, 1, 2)
        self.roi_layout.addWidget(self.camera_roi_height_label, 1, 3)
        self.roi_layout.addWidget(self.camera_roi_change_button, 2, 0, 1, 4)
        
        self.options_layout.setAlignment(QtCore.Qt.AlignTop)
        self.roi_layout.setAlignment(QtCore.Qt.AlignBottom)

        self.outer_layout.addLayout(self.options_layout)
        self.outer_layout.addLayout(self.roi_layout)
        self.setLayout(self.outer_layout)

        self.roi = [
            self.camera_roi_x_offset_spinbox.value(), # 0: offset x
            self.camera_roi_y_offset_spinbox.value(), # 1: offset y
            self.camera_roi_width_spinbox.value(),    # 2: width
            self.camera_roi_height_spinbox.value()    # 3: height
        ]
    
    def _on_cam_type_changed(self, index):
        if self.is_connect:
            if self.is_live:
                self.camera_live_button.setText("Start live recording")
                self.is_live = False
                self.live_worker.quit()
            self.camera.close_device()
            self.camera_connect_button.setText("Connect camera")
            self.is_connect = False
            self._set_widgets_enabled(False)
        self.camera_connect_button.setEnabled(bool(index))
        camera_name = self.camera_selection_combobox.currentText()
        try:
            self.camera = supported_cameras[camera_name]() # constructs object of class specified by camera_name
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
            if index > 0: # skipping index of selection string
                raise CameraError("Unsupported camera selected")
    
    def _delete_exposure_widget(self):
        if self.camera_exposure_label is not None:
            self.options_layout.removeWidget(self.camera_exposure_label)
            self.camera_exposure_widget.deleteLater()
            self.camera_exposure_widget = None
        if self.camera_exposure_widget is not None:
            if isinstance(self.camera_exposure_widget, QComboBox):
                self.camera_exposure_widget.currentTextChanged.disconnect(self._on_exposure_changed)
            else:
                self.camera_exposure_widget.valueChanged.disconnect(self._on_exposure_changed)
            self.options_layout.layout().removeWidget(self.camera_exposure_widget)
            self.camera_exposure_widget.deleteLater()
            self.camera_exposure_widget = None
    
    def _set_widgets_enabled(self, enabled : bool):
        self.camera_live_button.setEnabled(enabled)
        self.camera_record_button.setEnabled(enabled)
        self.camera_record_spinbox.setEnabled(enabled)
        self.camera_roi_change_button.setEnabled(enabled)

    def _add_opencv_exposure(self):
        self._delete_exposure_widget()
        self.camera_exposure_label = QLabel("Exposure", self)
        self.options_layout.addWidget(self.camera_exposure_label, 6, 0)
        self.camera_exposure_widget = QComboBox(self)
        self.camera_exposure_widget.addItems(list(self.camera.exposure_dict.keys()))
        self.camera_exposure_widget.currentTextChanged.connect(self._on_exposure_changed)
        self.options_layout.addWidget(self.camera_exposure_widget, 6, 1)


    def _add_camera_exposure(self):
        self._delete_exposure_widget()
        self.camera_exposure_label = QLabel("Exposure (ms)", self)
        self.options_layout.addWidget(self.camera_exposure_label, 6, 0)
        self.camera_exposure_widget = QDoubleSpinBox(self)
        self.camera_exposure_widget.setRange(0.1, 1000)
        self.camera_exposure_widget.setValue(10)
        self.camera_exposure_widget.valueChanged.connect(self._on_exposure_changed)
        self.options_layout.addWidget(self.camera_exposure_widget, 6, 1)
    
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
            prev_frame_time = 0.01
            view_time = time()
            while True: # infinite loop, quit signal makes it stop
                img = self.camera.capture_image()
                (self.live_image_buffer.append(img) if img is not None else None)
                new_frame_time = time()
                try:
                    self.frames_per_second_line_edit.setText(str(round(1/(new_frame_time-prev_frame_time))))
                except ZeroDivisionError:
                    pass
                prev_frame_time = new_frame_time
                if(new_frame_time - view_time > (1/60)):
                    yield self.live_image_buffer.pop()
                    view_time = time()
                    
        
        if not self.is_live:
            self.live_worker = yield_acquire_images_forever()
            self.camera_live_button.setText("Stop live recording")
            self.is_live = True
        else:
            self.is_live = False
            self.live_worker.quit()
            self.live_image_buffer.clear()
            self.camera_live_button.setText("Start live recording")

    def _on_exposure_changed(self, exposure):
        self.camera.set_exposure(exposure)

    def _on_record_clicked(self):

        def process_stack_images(is_process : bool, stack : list):
            if is_process:
                stack = self.special_function(stack)
            return stack

        @thread_worker
        def acquire_stack_images(stack_size, file_path):
            stack = [None] * stack_size
            for idx in range(0, stack_size):
                stack[idx] = self.camera.capture_image()
            processed = process_stack_images(self.special_function_checkbox.isChecked(), stack)
            if isinstance(processed, list):
                mimwrite(file_path, processed)
            else:
                imwrite(file_path, processed)

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

    def _on_special_function_enabled(self, enabled):
        if enabled:
            self.special_function_combobox.addItems(list(special_functions.keys()))
        else:
            self.special_function_combobox.clear()
            self.special_function = None
    
    def _on_special_function_changed(self, function):
        if function != "":
            self.special_function = special_functions[function]
    
    def _on_offset_x_changed(self, offset):
        self.roi[0] = offset

    def _on_offset_y_changed(self, offset):
        self.roi[1] = offset

    def _on_width_changed(self, width):
        self.roi[2] = width

    def _on_height_changed(self, height):
        self.roi[3] = height
    
    def _on_roi_change_requested(self):
        if self.camera is not None:
            self.camera.set_roi(self.roi)

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [LiveRecording]
