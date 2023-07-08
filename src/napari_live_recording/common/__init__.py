from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from functools import total_ordering
import pymmcore_plus as mmc

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
