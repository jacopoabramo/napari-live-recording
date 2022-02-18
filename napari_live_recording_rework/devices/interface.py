import numpy as np
from abc import abstractmethod
from typing import Union
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QPushButton, QGroupBox, QFormLayout
from napari.qt.threading import thread_worker
from collections import deque
from napari_live_recording_rework.common import ROI
from napari_live_recording_rework.widgets import (
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

class ICamera(QObject):
    availableWidgets = {
        WidgetEnum.ComboBox : ComboBox,
        WidgetEnum.SpinBox : SpinBox,
        WidgetEnum.DoubleSpinBox : DoubleSpinBox,
        WidgetEnum.LabeledSlider : LabeledSlider,
        WidgetEnum.LineEdit : LineEdit
    }
    recorded = pyqtSignal(np.ndarray)
    deleted = pyqtSignal(str)

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
        self.group = QGroupBox(f"{self.name}:{self.deviceID}")
        self.layout = QFormLayout()
        self.delete = QPushButton("Delete camera")
        self.ROIHandling = ROIHandling(sensorShape)
        self.recordHandling = RecordHandling()

        # layout order
        # 1) record handling widgets
        # 2) custom widgets
        # 3) roi handling widgets
        # 4) delete device button

        parametersLayout = QFormLayout()
        parametersGroup = QGroupBox()
        for widget in paramDict.values():
            parametersLayout.addRow(widget.label, widget.widget)
        parametersGroup.setLayout(parametersLayout)


        self.layout.addRow(self.recordHandling.group)
        self.layout.addRow(parametersGroup)
        self.layout.addRow(self.ROIHandling.group)
        self.layout.addRow(self.delete)

        self.group.setLayout(self.layout)
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
        try:
            data = self.liveDeque.pop()
            return data
        except IndexError:
            return None
    
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
    def grabFrame(self) -> np.array:
        """Returns the latest captured frame as a numpy array.
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
            - param (ParameterType): actual parameter items
            - paramDict (dict[str, ParameterType]): dictionary to store all parameters.
            - orientation (str, optional): orientation of the label for the parameter (can either be "left" or "right"). Default is "left".
        """
        if not name in paramDict:
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
