from napari import Viewer
from napari_plugin_engine import napari_hook_implementation
import napari_live_recording_rework.devices as devices
from napari_live_recording_rework.widgets import CameraSelection
from napari_live_recording_rework.control import Controller
from PyQt5.QtWidgets import QWidget, QFormLayout

class LiveRecordingPlugin(QWidget):
    def __init__(self, napari_viewer : Viewer) -> None:
        super().__init__()
        
        self.mainLayout = QFormLayout()
        self.selectionWidget = CameraSelection()
        cameras = list(devices.devicesDict.keys())
        self.selectionWidget.setAvailableCameras(cameras)
        self.controller = Controller(napari_viewer)
        self.mainLayout.addRow(self.selectionWidget.group)

        # Creates a new camera object and passes it to the controller
        # whenever the add button is pressed
        self.selectionWidget.newCameraRequested.connect(self.addNewCameraToController)
        self.setLayout(self.mainLayout)
    
    def addNewCameraToController(self, name: str, idx: str) -> None:
        self.mainLayout.addRow(self.controller.addCamera(devices.devicesDict[name](name, idx)))

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [LiveRecordingPlugin]