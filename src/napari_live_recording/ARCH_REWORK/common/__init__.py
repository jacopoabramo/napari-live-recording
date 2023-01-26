from enum import IntEnum, auto
from dataclasses import dataclass

class WidgetEnum(IntEnum):
    ComboBox = 0,
    SpinBox = auto(),
    DoubleSpinBox = auto(),
    LabeledSlider = auto(),
    LineEdit = auto()

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