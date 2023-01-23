from napari.viewer import Viewer
import napari_live_recording.devices as devices
from napari_live_recording.control.control import MainController
from  ._widgets import *

class ViewerAnchor:
    """Class which handles the UI elements of the plugin.
    """
    def __init__(self, napari_viewer : Viewer, mainController: MainController) -> None:
        self.viewer = napari_viewer
        
        self.mainController = mainController
        self.mainLayout = QFormLayout()
        self.selectionWidget = CameraSelection()
        self.selectionWidget.setAvailableCameras(list(devices.devicesDict.keys()))
        self.mainLayout.addRow(self.selectionWidget.group)
        self.viewer.layers.events.removed.connect(self.mainController.clearAlbumBuffer)

        # Creates a new camera object and passes it to the controller
        # whenever the add button is pressed
        self.selectionWidget.newCameraRequested.connect(self.addCameraUI)


        self.controller.cameraDeleted.connect(self.deleteCameraWidget)
        self.setLayout(self.mainLayout)
    
    def addCameraUI(self, interface: str, name: str, idx: int):
        camera : devices.ICamera = devices.devicesDict[interface](name, idx)
        camera.parametersGroup

        self.mainLayout.addRow(self.controller.addCamera(camera))

    def deleteCameraUI(self):
        pass
    
    def refreshViewer(self):
        pass