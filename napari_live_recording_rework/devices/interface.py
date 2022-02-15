import numpy as np
from abc import ABC, abstractmethod
from typing import Any, Union
from PyQt5.QtCore import QObject, Signal
from PyQt5.QtWidgets import QPushButton, QVBoxLayout
from napari.qt.threading import thread_worker
from collections import deque
from common import ROI
from widgets.widgets import (
    LocalWidget,
    ROIHandling,
    RecordHandling,
    ComboBox,
    SpinBox, 
    DoubleSpinBox, 
    LabeledSlider,
    LineEdit,
    WidgetEnum
)

ParameterType = Union[str, list[str], tuple[int, int, int], tuple[float, float, float]]

class Camera(ABC, QObject):
    availableWidgets = {
        WidgetEnum.ComboBox : ComboBox,
        WidgetEnum.SpinBox : SpinBox,
        WidgetEnum.DoubleSpinBox : DoubleSpinBox,
        WidgetEnum.LabeledSlider : LabeledSlider,
        WidgetEnum.LineEdit : LineEdit
    }

    def __init__(self, name: str, deviceID: Union[str, int], paramDict: dict[str, LocalWidget], sensorShape: ROI) -> None:
        """Generic camera device. Each device has a set of common widgets:

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
        self.layout = QVBoxLayout()
        self.delete = QPushButton("Delete camera")
        self.recordHandling = RecordHandling()
        self.ROIHandling = ROIHandling(sensorShape)
        self.parameters = paramDict
        self.recorded = Signal(np.array)
        self.deleted = Signal(str)

        # layout order
        # 1) record handling widgets
        # 2) custom widgets
        # 3) roi handling widgets
        # 4) delete device button
        self.layout.addLayout(self.recordHandling.layout)
        for widget in self.parameters.values():
            self.layout.addLayout(widget.layout)
        self.layout.addLayout(self.ROIHandling.layout)
        self.layout.addWidget(self.delete)
        self.setupWidgetsForStartup()
        self.connectSignals()
        
        # live recording
        self.isLive = False
        self.liveDeque = deque([], maxlen=10000)
        self.liveWorker = self._acquireForever()
        self.recordHandling.signals["liveRequested"].connect(self._handleLive)

        # stack recording
        # todo: add implementation

        # deletion button clicked
        self.delete.clicked.connect(lambda: self.deleted.emit(f"{self.name}:{self.deviceID}"))
    
    def __del__(self) -> None:
        # make sure that if live thread 
        # is running, this quits it
        self.recordHandling.signals["liveRequested"].emit(False)
        self.close()
        self.layout.deleteLater()

    @property
    def latestLiveFrame(self) -> np.array:
        """Pops a frame from the live deque, returning it.
        """
        return self.liveDeque.pop()
    
    @abstractmethod
    def setupWidgetsForStartup(self) -> None:
        """Initializes widgets for device startup.
        """
        pass

    @abstractmethod
    def connectSignals(self) -> None:
        """Connects widgets signals to device slots.
        """
        pass

    @abstractmethod
    def grabFrame(self) -> np.array:
        """Returns the latest captured frame as a numpy array.
        """
        pass

    @abstractmethod
    def cameraInfo(self) -> list[str]:
        """Returns a list of strings containing relevant device informations.
        """
        pass

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
            - param (ParameterType): actual parameter items
            - paramDict (dict[str, ParameterType]): dictionary to store all parameters.
            - orientation (str, optional): orientation of the label for the parameter (can either be "left" or "right"). Default is "left".
        """
        if not name in self.parameters:
            paramWidget = self.availableWidgets[widgetType](param, name, unit, orientation)
            paramDict[name] = paramWidget
    
    @thread_worker(start_thread=False)
    def _acquireForever(self):
        """Private thread worker for live view acquisitions.
        Captured images are stored in a ring buffer.
        The worker is stopped via the quit() signal for a graceful exit.
        """
        while True:
            img = self.grabFrame()
            (self.liveDeque.append(img) if img is not None else None)
            yield
    
    def _handleLive(self, isLive: bool) -> None:
        """Private slot to start/stop live acquisition. Signals start() and quit() are called
        when the thread needs to be started or stopped. When the thread is stopped, the live queue
        is cleared.

        Args:
            isLive (bool): True if live acquisition is started, otherwise False.
        """
        self.isLive = isLive
        if isLive:
            self.liveWorker.start()
        else:
            self.liveWorker.quit()
            self.liveDeque.clear()
    
    @thread_worker(start_thread=True)
    def _acquireRecording(self, length: int) -> np.array:
        """Private thread worker for recording acquisitions.
        Captured images are stacked, stored on disk and then 
        """
        return np.stack([self.grabFrame() for _ in range(0, length)])
