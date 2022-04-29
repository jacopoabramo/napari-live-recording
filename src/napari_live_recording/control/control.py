from qtpy.QtWidgets import QGroupBox
from qtpy.QtCore import QThread, QObject, Signal
from napari_live_recording.devices.interface import ICamera
from typing import NamedTuple

class LocalController(NamedTuple):
    """Named tuple to wrap a camera device and the relative thread into which it is moved.
    """
    thread : QThread
    device : ICamera

class Controller(QObject):
    cameraDeleted = Signal(QGroupBox)

    def __init__(self, plugin) -> None:
        """Main Controller class. Stores all camera objects to access live and stack recordings.

        Args:
            plugin: reference to the plugin,
            acting as interface to napari viewer viewer.
        """
        super(Controller, self).__init__()
        self.localControllers : dict[str, LocalController] = {}
        self.plugin = plugin

    def addCamera(self, camera: ICamera) -> QGroupBox:
        """Adds a camera, storing it into a dictionary.

        Args:
            camera: new Camera object to add to the controller dictionary.

        Returns:
            QVBoxLayout: the camera widget layout.
        """
        thread = QThread()
        cameraKey = f"{camera.name}:{camera.__class__.__name__}:{str(camera.deviceID)}"
        camera.moveToThread(thread)
        self.localControllers[cameraKey] = LocalController(thread, camera)
        self.localControllers[cameraKey].device.live.connect(lambda img: self.plugin.refreshViewer(img, f"Live ({camera.name})"))
        self.localControllers[cameraKey].device.snap.connect(lambda img: self.plugin.refreshViewer(img, f"Snap ({camera.name})"))
        self.localControllers[cameraKey].device.album.connect(lambda img: self.plugin.refreshViewer(img, f"Album ({camera.name})"))
        self.localControllers[cameraKey].device.record.connect(lambda img: self.plugin.refreshViewer(img, f"Record ({camera.name})"))
        self.localControllers[cameraKey].device.deleted.connect(self.deleteCamera)
        self.localControllers[cameraKey].thread.start()
        return self.localControllers[cameraKey].device.group
    
    def deleteCamera(self, cameraKey: str) -> None:
        """Deletes a camera from the cameras dictionary.
        Clicked signal from the delete button is disconnected to 
        avoid problems.
        """
        if self.localControllers[cameraKey].device.isLive:
            self.localControllers[cameraKey].device.recordHandling.live.toggle()
        self.localControllers[cameraKey].device.close()
        self.localControllers[cameraKey].device.live.disconnect()
        self.localControllers[cameraKey].device.snap.disconnect()
        self.localControllers[cameraKey].device.album.disconnect()
        self.localControllers[cameraKey].device.record.disconnect()
        self.localControllers[cameraKey].device.deleted.disconnect()
        self.localControllers[cameraKey].thread.quit()
        self.localControllers[cameraKey].thread.wait()
        self.localControllers[cameraKey].thread.deleteLater()
        self.localControllers[cameraKey].device.deleteLater()
        self.cameraDeleted.emit(self.localControllers[cameraKey].device.group)
        del self.localControllers[cameraKey]
    
    def clearAlbumBuffer(self, event) -> None:
        """ Special callback to clear the album frame buffer
         of a specific device whenever the layer is deleted.        
        """
        for cameraKey in self.localControllers.keys():
            if cameraKey.split(":")[0] in event.value.name:
                self.localControllers[cameraKey].device.albumBuffer.clear()
                break