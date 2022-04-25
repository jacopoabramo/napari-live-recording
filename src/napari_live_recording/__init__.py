from napari.viewer import Viewer
import napari_live_recording.devices as devices
from napari_live_recording.widgets import CameraSelection
from napari_live_recording.control import Controller
from qtpy.QtWidgets import QWidget, QFormLayout, QGroupBox

class NapariLiveRecording(QWidget):
    def __init__(self, napari_viewer : Viewer) -> None:
        super().__init__()
        
        
        self.viewer = napari_viewer
        self.mainLayout = QFormLayout()
        self.selectionWidget = CameraSelection()
        self.selectionWidget.setAvailableCameras(list(devices.devicesDict.keys()))
        self.controller = Controller(self)
        self.mainLayout.addRow(self.selectionWidget.group)
        self.viewer.layers.events.removed.connect(self.controller.clearAlbumBuffer)

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
    
    def refreshViewer(self, img, layerName) -> None:
        """ Slot triggered every time a camera acquires a frame.
        Creates a new layer on the viewer with the received image as content.
        If the layer already exists, it updates its content.

        Args:
            img (np.ndarray): image data.
            layerName (str): name of the layer to create/update.
        """
        if img is not None:
            try:
                # layer is recreated in case the image changes type (i.e. grayscale -> RGB and viceversa)
                if img.ndim != self.viewer.layers[layerName].data.ndim:
                    self.viewer.layers.remove(layerName)
                    self.viewer.add_image(img, name = layerName)
                else:
                    self.viewer.layers[layerName].data = img
            except KeyError:
                # needed in case the layer of that live recording does not exist
                self.viewer.add_image(img, name = layerName)