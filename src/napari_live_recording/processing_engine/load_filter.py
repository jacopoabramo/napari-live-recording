from image_filters import *

import image_filters

import pkgutil


class Filter:
    def __init__(self, filterFunction: "function") -> None:
        self.filterFunction = filterFunction


# funktioniert nur für module die über programm reingeladen wurden

moduleList = []
for importer, modname, ispkg in pkgutil.iter_modules(image_filters.__path__):
    moduleList.append(modname)

#

filtersDict = {}

for module in map(__import__(level=-1), moduleList):
    print(module)
    for func in filter(callable, module.__dict__.values()):
        print(func)
        filtersDict[func.__name__] = Filter(func)


print(filtersDict)


# print(self.parameters)


# filter = Filter(gauss.matlab_style_gauss2D)
