import numpy as np
from napari.qt.threading import thread_worker
from collections import deque
from abc import abstractmethod
from typing import Union
from qtpy.QtCore import QObject, Signal, QTimer
from napari_live_recording.common import ROI, THIRTY_FPS_IN_MS
from typing import Dict, List, Any
from collections import deque
from np_image_buffer import ImageBuffer

class ICamera(QObject):

    liveRequest = Signal(bool)
    liveData = Signal(np.ndarray)

    snapRequest = Signal()
    snapData = Signal(np.ndarray)

    albumRequest = Signal(bool)
    albumData = Signal(np.ndarray)

    recordRequest = Signal()
    recordData = Signal(np.ndarray)

    def __init__(self, name: str, deviceID: Union[str, int], paramDict: Dict[str, Any], sensorShape: ROI, bufferSize: int) -> None:
        """Generic camera device interface. Each device is initialized with a series of parameters.
        Live and recording are handled using child thread workers.
        
        Args:
            name (str): name of the camera device.
            deviceID (`Union[str, int]`): device ID.
            paramDict (`Dict[str, Any]`): dictionary of parameters of the specific device.
            sensorShape (`ROI`): camera physical shape and information related to the widget steps.
            bufferSize (`int`): size of the recording buffer.
        """
        super().__init__(self)
        self.name = name
        self.deviceID = deviceID
        self.cameraKey = f"{self.name}:{self.__class__.__name__}:{str(self.deviceID)}"
        self.parameters = paramDict
        self.sensorShape = sensorShape
        self.liveTimer = QTimer()
        self.liveTimer.setInterval(THIRTY_FPS_IN_MS)
        
        self.albumBuffer = deque([])

        # todo: ImageBuffer requires a rework to include a reshape method
        # for when the region of interest changes. 
        self.recordBuffer = ImageBuffer(shape=(bufferSize, sensorShape.height, sensorShape.width))

        # connecting request signals
        self.liveRequest.connect(self._handleLive)
        self.albumRequest.connect(self._handleAlbum)
        self.snapRequest.connect(self._handleSnap)
        self.recordRequest.connect(self._handleRecord)

    
    @abstractmethod
    def grabFrame(self) -> np.ndarray:
        """Returns the latest captured frame as a numpy array.
        """
        raise NotImplementedError()
    
    @abstractmethod
    def changeROI(self, newROI: ROI):
        """Changes the Region Of Interest of the sensor's device.
        """
        raise NotImplementedError()

    @abstractmethod
    def cameraInfo(self) -> List[str]:
        """Returns a List of strings containing relevant device informations.
        """
        raise NotImplementedError()

    def close(self) -> None:
        """Optional method to close the device.
        """
        pass
    
    def _handleSnap(self) -> np.ndarray:
        """ Returns a camera snap. """
        self.snapData.emit(self.grabFrame())
    
    def _handleAlbum(self, keepAppending: bool) -> np.ndarray:
        """ Returns the currently accumulated buffer consisting of a snap album. 
        
        Args:
            keepAppending (`bool`): flag for appending new frames to the buffer if True,
            or to clear it if False.
        """
        if keepAppending:
            self.albumBuffer.append(self.grabFrame())
            self.albumData.emit(np.stack(self.albumBuffer))
        else:
            self.albumBuffer.clear()
            self.albumData.emit(None)
    
    def _handleLive(self, isLive: bool) -> None:
        """
        Private slot to start/stop live acquisition.
        A timer sends an image grabbed from the device every 60 Hz.

        Args:
            isLive (bool): True if live acquisition is started, otherwise False.
        """
        if isLive:
            self.liveTimer.timeout.connect(lambda: self.liveData.emit(self.grabFrame()))
            self.liveTimer.start()
        else:
            self.liveTimer.stop()
            self.liveTimer.timeout.disconnect()
    
    def _handleRecord(self, recordOptions: dict) -> None:
        """ Runs a recording request. 
        The request spawns a thread which keeps capturing images
        until a certain condition is met, terminating the thread.
        """

        # todo: recordOptions should contain information 
        # relative to the type of recording:
        # - 1. number of frames
        # - 2. number of seconds
        # - 3. infinite until toggled
        # - 4. ??? triggered by something?

        @thread_worker(connect={"returned" : self.record.emit})
        def recordNumberedStack(stackSize: int):
            self.recordHandling.setWidgetsEnabling(False)
            self.parametersGroup.setEnabled(False)
            recordBuffer = deque([], maxlen=stackSize)
            for _ in range(recordBuffer.maxlen):
                recordBuffer.append(self.grabFrame())
            self.parametersGroup.setEnabled(True)
            self.recordHandling.setWidgetsEnabling(True)
            return np.stack(recordBuffer)
        
        recordNumberedStack(self.recordHandling.recordSize)