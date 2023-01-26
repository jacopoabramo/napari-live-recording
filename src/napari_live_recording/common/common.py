from dataclasses import dataclass
from functools import total_ordering

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

    def __le__(self, other) -> bool:
        if type(other) != self.__class__:
            raise NotImplementedError()
        return (self.offset_x + self.width  <= other.offset_x + other.width and
                self.offset_y + self.height <= other.offset_y + other.height)