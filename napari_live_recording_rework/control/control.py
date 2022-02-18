
import napari_live_recording_rework.common as common
from PyQt5.QtWidgets import QGroupBox
from napari_live_recording_rework.devices.interface import ICamera
from napari_live_recording_rework.widgets.widgets import Timer
from napari.viewer import Viewer

class Controller:
    def __init__(self, viewer: Viewer) -> None:
        """Main Controller class. Stores all camera objects to access live and stack recordings.

        Args:
            viewer (Viewer): reference to the napari Viewer object (provided by the plugin interface).
        """
        self.cameras : dict[str, ICamera] = {}
        self.viewer = viewer
        self.liveTimer = Timer()
        self.liveTimer.timeout.connect(self.refreshViewer)
        self.liveTimer.start(common.THIRTY_FPS_IN_MS)
    
    def __del__(self) -> None:
        self.liveTimer.stop()
        for cam in self.cameras.values():
            del cam

    def addCamera(self, camera: ICamera) -> QGroupBox:
        """Adds a camera, storing it into a dictionary.

        Args:
            camera (ICamera): new Camera object to add to the controller dictionary.

        Returns:
            QVBoxLayout: the camera widget layout.
        """
        cameraKey = f"{camera.name}:{str(camera.deviceID)}"
        self.cameras[cameraKey] = camera
        self.cameras[cameraKey].deleted.connect(self.deleteCamera)
        return self.cameras[cameraKey].group
    
    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera from the cameras dictionary.
        Clicked signal from the delete button is disconnected to 
        avoid problems.
        """
        self.cameras[cameraKey].delete.clicked.disconnect()
        del self.cameras[cameraKey]
    
    def refreshViewer(self) -> None:
        """Slot triggered every 30 Hz. Iterates over the added cameras to check if live acquisition is started.
        If that is the case, it pops a frame from each deque and shows it on the viewer.
        """
        for name, cam in self.cameras.items():
            if cam.isLive:
                try:
                    data = cam.latestLiveFrame
                    # this happens in case there is a change from
                    # a color base to grayscale image; we need
                    # to delete the layer and refresh it with
                    # new data
                    if data is not None:
                        if data.ndim != self.viewer.layers[f"Live ({name})"].data.ndim:
                            self.viewer.layers.remove(f"Live ({name})")
                            self.viewer.add_image(data, name = f"Live ({name})")
                except KeyError:
                    # needed in case the layer of that live recording does not exist
                    self.viewer.add_image(data, name = f"Live ({name})")