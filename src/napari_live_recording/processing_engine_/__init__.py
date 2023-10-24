from napari_live_recording.processing_engine_.image_filters import *
from napari_live_recording.processing_engine_ import image_filters
import functools
import importlib
import pkgutil


# funktioniert nur für module die über programm reingeladen wurden

moduleList = []
for importer, modname, ispkg in pkgutil.iter_modules(image_filters.__path__):
    moduleList.append(
        "napari_live_recording.processing_engine_.image_filters." + modname
    )

print(moduleList)
#

filtersDict = {}
i = 0
for module in map(importlib.import_module, moduleList):
    print("Module", module)
    i += 1
    for func in filter(callable, module.__dict__.values()):
        print(func)
        filtersDict[func.__name__] = Filter(func)
