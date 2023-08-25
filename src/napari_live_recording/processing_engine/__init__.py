from image_filters import *
import functools
import image_filters
import importlib
import pkgutil


# funktioniert nur für module die über programm reingeladen wurden

moduleList = []
for importer, modname, ispkg in pkgutil.iter_modules(image_filters.__path__):
    moduleList.append("image_filters." + modname)

print(moduleList)
#

filtersDict = {}
i = 0
# for module in [(__import__(modulename, level=-1) for modulename in moduleList)]:
for module in map(importlib.import_module, moduleList):
    print("Module", module)
    i += 1
    for func in filter(callable, module.__dict__.values()):
        print(func)
        filtersDict[func.__name__] = Filter(func)


print(filtersDict)
