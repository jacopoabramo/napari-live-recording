from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from functools import total_ordering

# equivalent number of milliseconds
# for 30 Hz and 60 Hz refresh rates
THIRTY_FPS = 33
SIXTY_FPS  = 16

class FileFormat(IntEnum):
    TIFF = 0
    # todo: add support for HDF5 storage
    # in the recording
    # HDF5 = auto()

@total_ordering
@dataclass
class ROI:
    """Dataclass for ROI settings.
    """
    offset_x: int = 0
    offset_y: int = 0
    height: int = 0
    width: int = 0
    ofs_x_step: int = 1
    ofs_y_step: int = 1
    width_step: int = 1
    height_step: int = 1

    def __le__(self, other: ROI) -> bool:
        return ((self.offset_x + self.width <= other.offset_x + other.width) and
                (self.offset_y + self.height <= other.offset_y + other.height))

    @property
    def pixelSizes(self) -> tuple:
        """Returns the number of pixels along width and height of the current ROI."""
        return (self.height - self.offset_y, self.width - self.offset_x)