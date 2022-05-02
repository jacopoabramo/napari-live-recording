# Plugin device interface

<!-- TOC -->

- [Plugin device interface](#plugin-device-interface)
    - [Signals](#signals)
    - [Abstract methods](#abstract-methods)
    - [How to create a new interface](#how-to-create-a-new-interface)
        - [Class constructor](#class-constructor)
        - [Parameters initialization.](#parameters-initialization)
            - [ROI](#roi)
            - [Parameters](#parameters)
            - [ICamera constructor and other objects](#icamera-constructor-and-other-objects)
        - [Abstract methods implementation](#abstract-methods-implementation)
        - [Updating parameters](#updating-parameters)
        - [Optional: close method](#optional-close-method)
        - [Locally installed packages](#locally-installed-packages)

<!-- /TOC -->

This document provides insight on the device interface of napari-live-recording plugin. It will also present a guide on how to integrate a new device based on the existing `OpenCV` interface.

Each new interface is automatically recognized by the plugin after software restart.

## Signals
---
Each interface provides the following signals:

    live = Signal(np.ndarray)
    snap = Signal(np.ndarray)
    album = Signal(np.ndarray)
    record = Signal(np.ndarray)
    deleted = Signal(str)

- `live`: emitted when a new frame is popped from the internal live frame buffer (triggered every 30 Hz by a local timer);
- `snap`: emitted when a new image snap is requested;
- `album`: emitted when a new image is to be added to the album buffer;
- `record`: emitted when a new video has been recorded;
- `deleted`: emitted when the user has requested device deletion from the GUI.

More signals can be defined within the device sub-class if necessary.

## Abstract methods
---
Each interface must define the following methods:

```python
    def setupWidgetsForStartup(self) -> None:
    def connectSignals(self) -> None:
    def grabFrame(self) -> np.ndarray:
    def changeROI(self, newROI: ROI) -> None:
    def cameraInfo(self) -> list[str]
```

- `setupWidgetsForStartup`: initializes the device widgets associated with the defined parameters of the device (i.e. sets the value of a ComboBox, or wether a widget is editable or not);
  - refer to `opencv.py` for some examples.
- `connectSignals`: provides the user a way to connect the defined widgets within the interface to private methods or other objects methods.
- `grabFrame`: method which retrieves the **latest** acquired frame from the camera.
- `changeROI`: method provided to change the Region of Interest (ROI) of the selected device.

## How to create a new interface
---
This section will provide a step-by-step tutorial to implement a device interface to integrate new cameras into the plugin. We will refer to the `OpenCV`interface described in `opencv.py`

### Class constructor
---
Each new interface must inherit from the `ICamera` abstract class, defined in the `interface` module, which provides all the signals and the methods to define the behavior of each device.

```python
from napari_live_recording.devices.interface import ICamera
```

The constructor must provide the following parameters: `name` (a `str` object) and `deviceID` (a `Union[str, int]`). The `name` is how the user has called the device in the device selection widget in the main GUI, while the `deviceID` represents an identifier, which can either be an integer or a string. This is also taken from the widget in the main GUI. This is used by the class constructor to create the specific camera object. Here an example as follows:

```python
class OpenCV(ICamera):
    def __init__(self, name: str, deviceID: Union[str, int]) -> None:
        """OpenCV VideoCapture wrapper.

        Args:
            name (str): user-defined camera name.
            deviceID (Union[str, int]): camera identifier.
        """
        self.__capture = cv2.VideoCapture(int(deviceID))
```

The `cv2.videoCapture` is initialized using the `deviceID` as an integer. Depending on the APIs, the `deviceID` can also be interpreted as a `str` object.

### Parameters initialization.

#### ROI
---

Each device must provide to the parent class' constructor a `ROI` object which defines the shape of the camera sensor, the initial X and Y offsets and the minimum changing steps. Here an example as follows:

```python
        # read OpenCV parameters
        width = int(self.__capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.__capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # initialize region of interest
        # steps for height, width and offsets
        # are by default 1. We leave them as such
        self.__ROI = ROI(offset_x=0, offset_y=0, height=height, width=width)
```

#### Parameters
---

For this interface we will define the following parameters which we will be able to control and/or show:

- Exposure time;
- Pixel format;
- Frame rate.

To define a new parameter, you must use the method `addParameter` defined in the parent class `ICamera`:

```python
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
```

`WidgetEnum` is an enumerator defined in the `widgets` module. These are the currently supported widgets:

```python
class WidgetEnum(Enum):
    ComboBox = 0,
    SpinBox = 1,
    DoubleSpinBox = 2,
    LabeledSlider = 3,
    LineEdit = 4
```

To add the parameters you have to define a settings dictionary in which they will be stored, then call `addParameters` for each one as follows:

```python
        self.parameters = {}
        self.addParameter(WidgetEnum.ComboBox, "Exposure time", "", list(self.OpenCVExposure.data.keys()), self.parameters)
        self.addParameter(WidgetEnum.ComboBox, "Pixel format", "", list(self.OpenCVPixelFormats.data.keys()), self.parameters)
        self.addParameter(WidgetEnum.LineEdit, "Frame rate", "FPS", "", self.parameters)
```

In this case, `OpenCVExposure` and `OpenCVPixelFormats` are dataclasses defined within the `OpenCV` class to divide what to show on the GUI and what is the actual value to set for each parameter.

#### ICamera constructor and other objects
---

After that the `ROI` object is defined parameter dictionary is set, you need to call the `ICamera` constructor as follows:

```python
        # call ICamera.__init__ after initializing all parameters in the parameters dictionary
        super().__init__(name, deviceID, self.parameters, self.__ROI)
```

After calling the parent constructor, you can also define other objects required for your interface to work properly. In our example, we define a timer object (which you can import from the `widgets` module) to keep track of the frame rate of our camera acquisition.

```python
        self.__fpsTimer = Timer()
        self.__fpsTimer.setInterval(ONE_SECOND_IN_MS)
        self.__fpsTimer.timeout.connect(self._updateFPS)
        self.__prevFrameTime = 0
        self.__newFrameTime = 0
```

### Abstract methods implementation
---

After the class constructor is defined, we need to define an implementation for the abstract methods described [here](#abstract-methods). Here is the example of our OpenCV class:

```python
    def setupWidgetsForStartup(self) -> None:
        exposure = self.OpenCVExposure.data["7.8 ms"]
        self.__capture.set(cv2.CAP_PROP_EXPOSURE, exposure)
        self.parameters["Exposure time"].value = abs(exposure)
        self.parameters["Frame rate"].isEnabled = False
        self.__format = self.OpenCVPixelFormats.data["RGB"]
        self.__FPS = 0
    
    def connectSignals(self) -> None:
        self.parameters["Exposure time"].signals["currentTextChanged"].connect(self._updateExposure)
        self.parameters["Pixel format"].signals["currentTextChanged"].connect(self._updateFormat)
        self.recordHandling.signals["liveRequested"].connect(lambda enabled: (self.__fpsTimer.start() if enabled else self.__fpsTimer.stop()))

    def grabFrame(self) -> np.ndarray:
        _, img = self.__capture.read()
        y, h = self.__ROI.offset_y, self.__ROI.offset_y + self.__ROI.height
        x, w = self.__ROI.offset_x, self.__ROI.offset_x + self.__ROI.width
        img = img[y:h, x:w]
        img = (cv2.cvtColor(img, self.__format) if self.__format is not None else img)

        # updating FPS counter
        self.__newFrameTime = time.time()
        self.__FPS = round(1/(self.__newFrameTime-self.__prevFrameTime))
        self.__prevFrameTime = self.__newFrameTime
        return img
    
    def changeROI(self, newROI: ROI):
        self.__ROI = copy(newROI)
    
    def cameraInfo(self) -> list[str]:
        # this is left empty purpously
        # the camera information control is still
        # under work
        return []
```

### Updating parameters
---

The user has the freedom to choose how to update the local parameters; in our `OpenCV` example we define a series of private methods to update each parameter:

- `_updateExposure` changes the exposure time based on the user input;
- `_updateFormat` changes the pixel format based on the user input;
- `_updateFPS` changes the frame rate calculated by the live acquisition, triggered every second by the local timer `__fpsTimer`.

```python
    def _updateExposure(self, exposure: str) -> None:
        self.__capture.set(cv2.CAP_PROP_EXPOSURE, self.OpenCVExposure.data[exposure])
    
    def _updateFormat(self, format: str) -> None:
        self.__format = self.OpenCVPixelFormats.data[format]

    def _updateFPS(self) -> None:
        self.parameters["Frame rate"].value = str(self.__FPS)
```

### Optional: close() method
---

A `close` method is also provided as a non-abstract method of the `ICamera` class, which allows the user to override to perform a specific close operation related to the camera device. In our example it is implemented as follows:

```python
    def close(self) -> None:
        self.__capture.release()
```

### Locally installed packages
---

Some cameras may be provided with external packages and/or external DLLs for control. It is important that the class definition of these devices is wrapped in a try-except condition in order for the plugin to make sure that they are not wrongfully imported when the proper external software is not installed. An example is provided in the `Ximea` camera interface.