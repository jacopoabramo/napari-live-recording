from napari.viewer import Viewer
from napari_plugin_engine import napari_hook_implementation
import napari_live_recording.devices as devices
from napari_live_recording.widgets import CameraSelection
from napari_live_recording.control import Controller
from PyQt5.QtWidgets import QWidget, QFormLayout, QGroupBox

class LiveRecordingPlugin(QWidget):
    def __init__(self, napari_viewer : Viewer) -> None:
        super().__init__()
        
        self.mainLayout = QFormLayout()
        self.selectionWidget = CameraSelection()
        self.selectionWidget.setAvailableCameras(list(devices.devicesDict.keys()))
        self.controller = Controller(self)
        self.mainLayout.addRow(self.selectionWidget.group)
        self.viewer = napari_viewer

        # Creates a new camera object and passes it to the controller
        # whenever the add button is pressed
        self.selectionWidget.newCameraRequested.connect(self.addNewCamera)
        self.controller.cameraDeleted.connect(self.deleteCameraWidget)
        self.setLayout(self.mainLayout)
    
    def addNewCamera(self, type: str, name, idx: str) -> None:
        camera = devices.devicesDict[type](name, idx)
        self.mainLayout.addRow(self.controller.addCamera(camera))
    
    def deleteCameraWidget(self, widget: QGroupBox) -> None:
        self.mainLayout.removeRow(widget)
    
    def refreshLiveViewer(self, img, camName) -> None:
        """Slot triggered every time a camera acquires a live frame

        Args:
            img (np.ndarray): image data.
            camName (str): name of the camera.
        """
        if img is not None:
            try:
                if img.ndim != self.viewer.layers[f"Live ({camName})"].data.ndim:
                    self.viewer.layers.remove(f"Live ({camName})")
                    self.viewer.add_image(img, name = f"Live ({camName})")
                else:
                    self.viewer.layers[f"Live ({camName})"].data = img
            except KeyError:
                # needed in case the layer of that live recording does not exist
                self.viewer.add_image(img, name = f"Live ({camName})")
    
    def refreshSnapViewer(self, img, camName) -> None:
        """Slot triggered every time a camera acquires a new snap.

        Args:
            img (np.ndarray): image data.
            camName (str): name of the camera.
        """
        pass

    def refreshAlbumViewer(self, img, camName) -> None:
        """Slot triggered every time a camera acquires an image to add to an album.

        Args:
            img (np.ndarray): image data.
            camName (camName): name of the camera.
        """
        pass

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return [LiveRecordingPlugin]