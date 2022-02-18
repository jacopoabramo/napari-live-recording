from napari import Viewer
from napari_plugin_engine import napari_hook_implementation
# import napari_live_recording_rework.devices as devices
from napari_live_recording_rework.widgets import CameraSelection
from napari_live_recording_rework.control import Controller
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox
from napari_live_recording_rework.devices.opencv import OpenCV

supportedCameras = {"OpenCV" : OpenCV}

class LiveRecordingPlugin(QWidget):
    def __init__(self, napari_viewer : Viewer) -> None:
        super().__init__()
        
        self.mainLayout = QVBoxLayout()
        self.selectionWidget = CameraSelection()
        cameras = list(supportedCameras.keys())
        self.selectionWidget.setAvailableCameras(cameras)
        self.controller = Controller(napari_viewer)
        self.mainLayout.addWidget(self.selectionWidget.group)

        # Creates a new camera object and passes it to the controller
        # whenever the add button is pressed
        self.selectionWidget.newCameraRequested.connect(self.addNewCameraToController)
        self.mainLayout.addStretch(1)
        self.setLayout(self.mainLayout)
    
    def addNewCameraToController(self, name: str, idx: str) -> None:
        self.mainLayout.addWidget(self.controller.addCamera(supportedCameras[name](name, idx)))

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [LiveRecordingPlugin]