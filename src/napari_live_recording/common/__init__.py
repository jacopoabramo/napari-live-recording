from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from functools import total_ordering
import pymmcore_plus as mmc
import os
from qtpy.QtCore import QSettings, Qt
import functools, pims


settingsFilePath = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "./settings.ini"
)
settings = QSettings(settingsFilePath, QSettings.IniFormat)

class Settings:
    def __init__(self) -> None:
        self.settings = settings

    def setSetting(self, key, newValue):
        self.settings.setValue(key, newValue)

    def getSetting(self, key):
        if self.settings.contains(key):
            return self.settings.value(key)
        else:
            return None

    def getFilterGroupsDict(self):
        if self.settings.contains("availableFilterGroups"):
            return self.settings.value("availableFilterGroups")
        else:
            self.settings.setValue(
                "availableFilterGroups", {"No Filter": {"1.No Filter": None}}
            )
            return self.settings.value("availableFilterGroups")

    def setFilterGroupsDict(self, newDict):
        newDict["No Filter"] = {"1.No Filter": None}
        self.settings.setValue("availableFilterGroups", newDict)


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

MMC_DEVICE_MAP = {
    'ABSCamera': ['ABSCam'],
    'AmScope': ['AmScope'],
    'Andor': ['Andor'],
    'ArduinoCounter': ['ArduinoCounterCamera'],
    'AtikCamera': ['Universal Atik Cameras Device Adapter'],
    'AxioCam': ['Zeiss AxioCam'],
    'BaumerOptronic': ['BaumerOptronic'],
    'DECamera': ['Direct Electron Camera'],
    'DemoCamera': ['DCam'],
    'FLICamera': ['FLICamera'],
    'FakeCamera': ['FakeCamera'],
    'HamamatsuHam': ['HamamatsuHam_DCAM'],
    'HoribaEPIX': ['Horiba EFIS Camera',
                'Horiba EFIS Camera',
                'Horiba EFIS Camera',
                'Horiba EFIS Camera',
                'Horiba EFIS Camera'],
    'JAI': ['JAICamera'],
    'Mightex_C_Cam': ['Mightex_BUF_USBCCDCamera'],
    'OpenCVgrabber': ['OpenCVgrabber'],
    'PCO_Camera': ['pco_camera'],
    'PVCAM': ['Camera-1', 'Camera-1', 'Camera-1', 'Camera-1'],
    'RaptorEPIX': ['Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera',
                'Raptor Falcon Camera'],
    'TIScam': ['TIS_DCAM'],
    'TSI': ['TSICam'],
    'TwainCamera': ['TwainCam'],
    'Utilities': ['Multi Camera']
}

microscopeDeviceDict = {
    "andorsdk3": "AndorSDK3",  # microscope.cameras.andorsdk3.AndorSDK3
    "atmcd": "AndorAtmcd",  # microscope.cameras.atmcd.AndotAtmcd
    "pvcam": "PVCamera",  # microscope.cameras.pvcam.PVCamera
    "ximea": "XimeaCamera",  # microscope.cameras.ximea.XimeaCamera
    "hamamatsu": "HamamtsuCamera",
    "picamera": "PiCamera",
    "simulators": "SimulatedCamera",
}
