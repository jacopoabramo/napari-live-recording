from os.path import dirname, basename, isfile, join
import glob


class FilterFunction:
    def __init__(self, parameters) -> None:
        self.parameters = parameters
        pass


class Filter:
    def __init__(self, filter: "function") -> None:
        self.filter = filter

    def executeFilter(self, image, parameterDict):
        self.filter(image, **parameterDict)


# __all__ = []
# modules = glob.glob(join(dirname(__file__), "*.py"))
# for f in modules:
#     if isfile(f) and not f.endswith("__init__.py"):
#         file = basename(f)[:-3]
#         __all__.append(f"{file}")


# #
# __all__ = ["gauss", "other_gauss"]
