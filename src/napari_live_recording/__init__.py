from qtpy.QtWidgets import QWidget, QApplication
from napari.viewer import Viewer
from napari_live_recording.ui import ViewerAnchor
from napari_live_recording.control import MainController


class NapariLiveRecording(QWidget):
    def __init__(self, napari_viewer: Viewer) -> None:
        super().__init__()
        self.app = QApplication.instance()
        self.mainController = MainController()
        self.anchor = ViewerAnchor(napari_viewer, self.mainController)
        self.setLayout(self.anchor.mainLayout)
        self.app.lastWindowClosed.connect(self.on_close_callback)

    def on_close_callback(self) -> None:
        self.anchor.cleanup()
