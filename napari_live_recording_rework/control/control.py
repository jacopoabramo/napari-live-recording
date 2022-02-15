
import common
from PyQt5.QtWidgets import QVBoxLayout
from devices.interface import Camera
from widgets.widgets import Timer
from napari.viewer import Viewer

class Controller:
    def __init__(self, viewer: Viewer) -> None:
        """Main Controller class. Stores all camera objects to access live and stack recordings.

        Args:
            viewer (Viewer): reference to the napari Viewer object (provided by the plugin interface).
        """
        self.cameras : dict[str, Camera] = {}
        self.viewer = viewer
        self.liveTimer = Timer()
        self.liveTimer.timeout.connect(self.refreshViewer)
        self.liveTimer.start(common.THIRTY_FPS_IN_MS)
    
    def __del__(self) -> None:
        self.liveTimer.stop()
        for cam in self.cameras.values():
            del cam

    def addCamera(self, camera: Camera) -> QVBoxLayout:
        """Adds a camera, storing it into a dictionary.

        Args:
            camera (Camera): new Camera object to add to the controller dictionary.

        Returns:
            QVBoxLayout: the camera widget layout.
        """
        cameraKey = f"{camera.name}:{str(camera.deviceID)}"
        self.cameras[cameraKey] = camera
        self.cameras[cameraKey].deleted.connect(self.deleteCamera)
        return self.cameras[cameraKey].layout
    
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
                    if data.ndim != self.viewer.layers[f"Live ({name})"].data.ndim:
                        self.viewer.layers.remove(f"Live ({name})")
                        self.viewer.add_image(data, name = f"Live ({name})")
                except KeyError:
                    # needed in case the layer of that live recording does not exist
                    self.viewer.add_image(data, name = f"Live ({name})")            
                except IndexError:
                    pass