import common
from PyQt5.QtCore import QSignalMapper
from devices.interface import Camera
from widgets.widgets import Timer
from napari.viewer import Viewer
from typing import Dict

class Controller:
    def __init__(self, viewer: Viewer) -> None:
        self.cameras : Dict[str, Camera] = {}
        self.viewer = viewer
        self.liveTimer = Timer()
        self.liveTimer.setInterval(common.THIRTY_FPS_IN_MS)
        self.liveTimer.timeout.connect(self.refreshViewer)

    def addCamera(self, camera: Camera) -> None:
        cameraKey = f"{camera.name}:{str(camera.deviceID)}"
        self.cameras[cameraKey] = camera
        self.cameras[cameraKey].deleted.connect(self.deleteCamera)
        self.cameras[cameraKey].recordHandling.signals["liveRequested"].connect()
    
    def deleteCamera(self, cameraKey: str) -> None:
        self.cameras[cameraKey].delete.clicked.disconnect()
        del self.cameras[cameraKey]
    
    def refreshViewer(self) -> None:
        pass