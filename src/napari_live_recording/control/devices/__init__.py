from inspect import isclass, getmembers
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
from .interface import ICamera

package_dir = Path(__file__).resolve().parent
devicesDict = {}

# iterate through the modules of the devices module
# in order to find all submodules containing the class definitions
# of all cameras
for (_, module_name, _) in iter_modules([str(package_dir)]):
    # import the modulte and iterate through the attributes
    try:
        # we skip the interface module
        if module_name != "interface":
            module = import_module(f"{__name__}.{module_name}")
            for attr in getmembers(module, isclass):
                # attr[0]: class name as string
                # attr[1]: class object
                if attr[1] != ICamera and issubclass(attr[1], ICamera):
                    devicesDict[attr[0]] = attr[1]
    except ImportError:
        # This check is added to make sure that modules from cameras
        # which must be added manually (i.e. Ximea's APIs) do not 
        # cause issues when loading the plugin.
        # The camera won't be visibile in the supported camera list
        # but the plugin will still be working as expected.
        # In case there are cameras which require external components,
        # remember to wrap them in a try-except snippet and raise an
        # ImportError exception if there is any missing package.
        raise TypeError(f"Importing of {module_name} failed. Check napari's traceback for more informations.")