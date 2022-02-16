import devices
from napari import Viewer
from napari_plugin_engine import napari_hook_implementation
from napari_live_recording_rework.widgets import CameraSelection
from napari_live_recording_rework.control import Controller
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class napari_live_recording(QWidget):
    def __init__(self, napari_viewer : Viewer) -> None:
        super().__init__()
        
        self.mainLayout = QVBoxLayout(self)
        self.selectionWidget = CameraSelection()
        self.selectionWidget.setAvailableCameras([devices.devicesDict.keys()])
        self.controller = Controller(napari_viewer)

        self.mainLayout.addLayout(self.selectionWidget.layout())

@napari_hook_implementation
def napari_live_recording_plugin():
    return [napari_live_recording]