import numpy as np
from napari.qt.threading import thread_worker
from collections import deque
from abc import abstractmethod
from typing import Union
from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QPushButton, QGroupBox, QFormLayout
from napari_live_recording.common import ROI, THIRTY_FPS_IN_MS
from napari_live_recording.widgets import (
    LocalWidget,
    ROIHandling,
    RecordHandling,
    ComboBox,
    SpinBox, 
    DoubleSpinBox, 
    LabeledSlider,
    LineEdit,
    WidgetEnum,
    Timer
)

ParameterType = Union[str, list[str], tuple[int, int, int], tuple[float, float, float]]

class ICamera(QObject):
    availableWidgets = {
        WidgetEnum.ComboBox : ComboBox,
        WidgetEnum.SpinBox : SpinBox,
        WidgetEnum.DoubleSpinBox : DoubleSpinBox,
        WidgetEnum.LabeledSlider : LabeledSlider,
        WidgetEnum.LineEdit : LineEdit
    }
    live = Signal(np.ndarray)
    snap = Signal(np.ndarray)
    album = Signal(np.ndarray)
    record = Signal(np.ndarray)
    deleted = Signal(str)

    def __init__(self, name: str, deviceID: Union[str, int], paramDict: dict[str, LocalWidget], sensorShape: ROI) -> None:
        """Generic camera device interface. Each device has a set of common widgets:

        - ROI handling widget;
        - Delete device button.

        Live and recording are handled using separate thread workers.

        Initializer must be called AFTER calling the child class initializer to ensure that parameter widgets
        can be accessed.

        Args:
            name (str): name of the camera device.
            deviceID (Union[str, int]): device ID.
            paramDict (dict[str, LocalWidget]): dictionary of parameters' widgets initialized for the specific device.
            sensorShape (ROI): camera physical shape and information related to the widget steps.
        """
        self.name = name
        self.deviceID = deviceID
        self.cameraKey = f"{self.name}:{self.__class__.__name__}:{str(self.deviceID)}"
        self.group = QGroupBox(f"{self.name} ({self.__class__.__name__}:{self.deviceID})")
        self.layout = QFormLayout()
        self.delete = QPushButton("Delete camera")
        self.sensorShape = sensorShape
        self.ROIHandling = ROIHandling(sensorShape)
        self.recordHandling = RecordHandling()

        # layout order
        # 1) record handling widgets
        # 2) custom widgets
        # 3) roi handling widgets
        # 4) delete device button
        parametersLayout = QFormLayout()
        self.parametersGroup = QGroupBox()
        for widget in paramDict.values():
            parametersLayout.addRow(widget.label, widget.widget)
        self.parametersGroup.setLayout(parametersLayout)

        self.layout.addRow(self.recordHandling.group)
        self.layout.addRow(self.parametersGroup)
        self.layout.addRow(self.ROIHandling.group)
        self.layout.addRow(self.delete)

        self.group.setLayout(self.layout)
        self.setupWidgetsForStartup()
        self.connectSignals()

        # ROI handling
        self.ROIHandling.signals["changeROIRequested"].connect(self.changeROI)
        self.ROIHandling.signals["fullROIRequested"].connect(lambda: self.changeROI(self.sensorShape))
        
        # live
        self.liveBuffer = deque([], maxlen=1000)
        self.liveWorker = None
        self.isLive = False
        self.liveTimer = Timer()
        self.liveTimer.setInterval(THIRTY_FPS_IN_MS)
        self.liveTimer.timeout.connect(self._sendLiveFrame)
        self.recordHandling.signals["liveRequested"].connect(self._handleLive)

        # snap
        self.recordHandling.signals["snapRequested"].connect(self._handleSnap)

        # album
        self.albumBuffer = deque([])
        self.recordHandling.signals["albumRequested"].connect(self._handleAlbum)

        # stack recording
        self.recordHandling.signals["recordRequested"].connect(self._handleRecord)

        # deletion button clicked
        self.delete.clicked.connect(lambda: self.deleted.emit(self.cameraKey))
    
    @abstractmethod
    def setupWidgetsForStartup(self) -> None:
        """Initializes widgets for device startup.
        """
        raise NotImplementedError()

    @abstractmethod
    def connectSignals(self) -> None:
        """Connects widgets signals to device slots.
        """
        raise NotImplementedError()

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
    def cameraInfo(self) -> list[str]:
        """Returns a list of strings containing relevant device informations.
        """
        raise NotImplementedError()

    def close(self) -> None:
        """Closes the device if necessary.
        """
        pass

    def addParameter(self, widgetType: WidgetEnum, name: str, unit: str, param: ParameterType, paramDict: dict[str, ParameterType], orientation="left") -> None:
        """Adds a parameter in the form of a widget, exposing the respective signals to enable connections to user-defined slots.
        If the parameter already exists, it will not be added to the parameter list.

        Args:
            - widgetType (WidgetEnum): type of widget created.
            - name (str): name of the added parameter (i.e. \"Exposure time\")
                - this will be the name shown in the GUI
            - unit (str): unit measure of the added parameter (i.e. \"ms\")
            - param (ParameterType): actual parameter items; parameters can be of the following type:
            ParameterType = Union[str, list[str], tuple[int, int, int], tuple[float, float, float]]
                - str
                - list[str]
                - tuple[int, int, int]
                - tuple[float, float, float]
            - paramDict (dict[str, ParameterType]): dictionary to store all parameters.
            - orientation (str, optional): orientation of the label for the parameter (can either be "left" or "right"). Default is "left".
        """
        if not name in paramDict:
            paramWidget = self.availableWidgets[widgetType](param, name, unit, orientation)
            paramDict[name] = paramWidget
    
    def _sendLiveFrame(self) -> None:
        try:
            self.live.emit(self.liveBuffer.pop())
        except IndexError:
            pass
    
    def _handleSnap(self) -> np.ndarray:
        """ Returns a camera snap. """
        self.snap.emit(self.grabFrame())
    
    def _handleAlbum(self) -> np.ndarray:
        """ Returns the currently accumulated buffer consisting of a snap album. """
        self.albumBuffer.append(self.grabFrame())
        self.album.emit(np.stack(self.albumBuffer))
    
    def _handleLive(self, isLive: bool) -> None:
        """Private slot to start/stop live acquisition. Signals start() and quit() are called
        when the thread needs to be started or stopped. When the thread is stopped, the live queue
        is cleared.
        The local controller spawns a second thread to store acquired images on a local buffer.
        Images are popped from the buffer with a 60 Hz refresh rate and sent to the napari viewer.

        Args:
            isLive (bool): True if live acquisition is started, otherwise False.
        """
        # inspired by https://github.com/haesleinhuepf/napari-webcam
        @thread_worker
        def acquire_images_forever():
            while True:  # infinite loop, quit signal makes it stop
                img = self.grabFrame()
                (self.liveBuffer.append(img) if img is not None else None)
                yield  # needed to return control

        self.isLive = isLive
        if isLive:
            self.liveWorker = acquire_images_forever()
            self.liveWorker.start()
            self.liveTimer.start()
        else:
            self.liveTimer.stop()
            self.liveWorker.toggle_pause()
            self.liveBuffer.clear()
    
    def _handleRecord(self) -> None:
        """ Runs a recording request. All the pushbuttons
        are disabled until the recording is complete. """
        @thread_worker(connect={"returned" : self.record.emit})
        def record_stack(stackSize):
            self.recordHandling.setWidgetsEnabling(False)
            self.parametersGroup.setEnabled(False)
            recordBuffer = deque([], maxlen=stackSize)
            for _ in range(recordBuffer.maxlen):
                recordBuffer.append(self.grabFrame())
            self.parametersGroup.setEnabled(True)
            self.recordHandling.setWidgetsEnabling(True)
            return np.stack(recordBuffer)
        
        record_stack(self.recordHandling.recordSize)
        

        


