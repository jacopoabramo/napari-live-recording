from .Functions import *

special_functions = {
    "Stack average" : average_image_stack
}

__all__ = [
    "acquire",
    "average_image_stack",
    "special_functions"
]