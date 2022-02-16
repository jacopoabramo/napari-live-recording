from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module

# iterate through the modules
package_dir = Path(__file__).resolve().parent
devicesDict = {}

for (_, module_name, _) in iter_modules([package_dir]):
    
    # import the modulte and iterate through the attributes
    try:
        module = import_module(f"{__name__}.{module_name}")
    except ImportError:
            pass
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if isclass(attribute):
            devicesDict[attribute_name] = attribute