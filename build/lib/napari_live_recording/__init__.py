from qtpy.QtWidgets import QWidget
from napari.viewer import Viewer
from napari_live_recording.ui import ViewerAnchor
from napari_live_recording.control import MainController

class NapariLiveRecording(QWidget):
    def __init__(self, napari_viewer: Viewer) -> None:
        super().__init__()
        self.mainController = MainController()
        self.anchor = ViewerAnchor(napari_viewer, self.mainController)
        self.setLayout(self.anchor.mainLayout)