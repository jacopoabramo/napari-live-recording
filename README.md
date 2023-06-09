# napari-live-recording

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/jacopoabramo/napari-live-recording/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-live-recording.svg?color=green)](https://pypi.org/project/napari-live-recording)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-live-recording.svg?color=green)](https://python.org)
[![tests](https://github.com/jethro33/napari-live-recording/workflows/tests/badge.svg)](https://github.com/jacopoabramo/napari-live-recording/actions)
[![codecov](https://codecov.io/gh/jethro33/napari-live-recording/branch/master/graph/badge.svg)](https://codecov.io/gh/jacopoabramo/napari-live-recording)

A napari plugin for live video recording with a generic camera device and generate a stack of TIFF images from said device.

The plugin provides a common interface for a generic camera device to be directly controlled from the napari GUI. The plugin can

- acquire continously in live view;
- record a stack of images and store them as ImageJ-compatible TIFF, OME-TIFF or HDF5 files.

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using with [@napari]'s [cookiecutter-napari-plugin] template.

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/cookiecutter-napari-plugin#getting-started

and review the napari docs for plugin developers:
https://napari.org/docs/plugins/index.html
-->

## Installation

You can install `napari-live-recording` via [pip]:

    pip install napari-live-recording

If you want to install the plugin using the source code, you can do so by cloning the project and installing locally:

    git clone https://github.com/jacopoabramo/napari-live-recording
    cd napari-live-recording
    pip install .

## Documentation

You can review the documentation of this plugin [here](./docs/README.md)

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [MIT] license,
"napari-live-recording" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/jacopoabramo/napari-live-recording/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
