from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from functools import total_ordering
import pymmcore_plus as mmc
import os
from qtpy.QtCore import QSettings, Qt
import functools, pims

settings = QSettings("IPHT", "Napari-Live-Recording")
filtersDict = {}


class Settings:
    def __init__(self) -> None:
        self.settings = settings

    def setSetting(self, key, newValue):
        self.settings.setValue(key, newValue)

    def getSetting(self, key):
        return self.settings.value(key)

    def getFiltersDict(self):
        if self.settings.contains("availableFilters"):
            print("contained")
            return self.settings.value("availableFilters")
        else:
            print("Not Contained")
            self.settings.setValue(
                "availableFilters", {"No Filter": {"1.No Filter": None}}
            )
            return self.settings.value("availableFilters")

    def setFiltersDict(self, newDict):
        newDict["No Filter"] = {"1.No Filter": None}
        self.settings.setValue("availableFilters", newDict)


def createPipelineFilter(filters):
    def composeFunctions(functionList):
        return functools.reduce(
            lambda f, g: lambda x: f(g(x)), functionList, lambda x: x
        )

    functionList = []

    for filter in filters.values():
        filterPartial = functools.partial(filter[0], **filter[1])
        functionList.append(pims.pipeline(filterPartial))
    composedFunction = composeFunctions(list(reversed(functionList)))
    return composedFunction


# equivalent number of milliseconds
# for 30 Hz and 60 Hz refresh rates
THIRTY_FPS = 33
SIXTY_FPS = 16
FileFormat = IntEnum(
    value="FileFormat", names=[("ImageJ TIFF", 1), ("OME-TIFF", 2), ("HDF5", 3)]
)

RecordType = IntEnum(
    value="RecordType",
    names=[("Number of frames", 1), ("Time (seconds)", 2), ("Toggled", 3)],
)


class ColorType(IntEnum):
    GRAYLEVEL = 0
    RGB = 1


TIFF_PHOTOMETRIC_MAP = {
    # ColorType -> photometric, number of channels
    ColorType.GRAYLEVEL: ("minisblack", 1),
    ColorType.RGB: ("rgb", 3),
}


@dataclass(frozen=True)
class WriterInfo:
    folder: str
    filename: str
    fileFormat: FileFormat
    recordType: RecordType
    stackSize: int = 0
    acquisitionTime: float = 0


@total_ordering
@dataclass
class ROI:
    """Dataclass for ROI settings."""

    offset_x: int = 0
    offset_y: int = 0
    height: int = 0
    width: int = 0
    ofs_x_step: int = 1
    ofs_y_step: int = 1
    width_step: int = 1
    height_step: int = 1

    def __le__(self, other: ROI) -> bool:
        return (self.offset_x + self.width <= other.offset_x + other.width) and (
            self.offset_y + self.height <= other.offset_y + other.height
        )

    @property
    def pixelSizes(self) -> tuple:
        """Returns the number of pixels along width and height of the current ROI."""
        return (self.height - self.offset_y, self.width - self.offset_x)


def getDocumentsFolder():
    """Returns the user's documents folder if they are using a Windows system,
    or their home folder if they are using another operating system."""

    if os.name == "nt":  # Windows system, try to return documents directory
        try:
            import ctypes.wintypes

            CSIDL_PERSONAL = 5  # Documents
            SHGFP_TYPE_CURRENT = 0  # Current value

            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(
                0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf
            )

            return buf.value
        except ImportError:
            pass
    return os.path.expanduser("~")  # Non-Windows system, return home directory


baseRecordingFolder = os.path.join(getDocumentsFolder(), "napari-live-recording")


# at startup initialize the base recording folder
if not os.path.exists(baseRecordingFolder):
    os.mkdir(baseRecordingFolder)

MMC_DEVICE_MAP = {}
core = mmc.CMMCorePlus.instance()
adapters = core.getDeviceAdapterNames()

for adapter in adapters:
    try:
        devices = []
        types = [mmc.DeviceType(type) for type in core.getAvailableDeviceTypes(adapter)]
        names = core.getAvailableDevices(adapter)
        for t in types:
            if t == mmc.DeviceType.Camera:
                devices.append(names[types.index(t)])
        if len(devices) > 0:
            MMC_DEVICE_MAP[adapter] = devices

    except:
        pass

microscopeDeviceDict = {
    "andorsdk3": "AndorSDK3",  # microscope.cameras.andorsdk3.AndorSDK3
    "atmcd": "AndorAtmcd",  # microscope.cameras.atmcd.AndotAtmcd
    "pvcam": "PVCamera",  # microscope.cameras.pvcam.PVCamera
    "ximea": "XimeaCamera",  # microscope.cameras.ximea.XimeaCamera
    "hamamatsu": "HamamtsuCamera",
    "picamera": "PiCamera",
    "simulators": "SimulatedCamera",
}
