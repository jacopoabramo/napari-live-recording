from napari import Viewer
from napari_plugin_engine import napari_hook_implementation
from napari_live_recording_rework.widgets import CameraSelection
from napari_live_recording_rework.control import Controller
from PyQt5.QtWidgets import QWidget
from napari_live_recording_rework.devices.opencv import Camera
# from napari_live_recording_rework.devices.ximea import Ximea

class napari_live_recording(QWidget):
    def __init__(self, napari_viewer : Viewer) -> None:
        super().__init__()
        self.selectionWidget = CameraSelection()
        self.controller = Controller(napari_viewer)

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [napari_live_recording]