# napari-live-recording

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/jacopoabramo/napari-live-recording/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-live-recording.svg?color=green)](https://pypi.org/project/napari-live-recording)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-live-recording.svg?color=green)](https://python.org)
![tests](https://github.com/jacopoabramo/napari-live-recording/actions/workflows/test_and_deploy.yaml/badge.svg)
[![codecov](https://codecov.io/github/jacopoabramo/napari-live-recording/graph/badge.svg?token=WhI2MO452Z)](https://codecov.io/github/jacopoabramo/napari-live-recording) \
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-live-recording)](https://napari-hub.org/plugins/napari-live-recording)
[![Chan-Zuckerberg Initiative](https://custom-icon-badges.demolab.com/badge/Chan--Zuckerberg_Initiative-red?logo=czi)](https://chanzuckerberg.com/)

This [napari] plugin was generated with [Cookiecutter] using with [@napari]'s [cookiecutter-napari-plugin] template.

## Description

`napari-live-recording` (or `nlr`, if you like acronyms) is a <a href="#why-medium-weight">medium-weight</a> plugin part of the napari ecosystem that provides an easy 
access point for controlling area detector devices (most commonly reffered to as cameras) with a common interface.
Other than that, the plugin also allows to create computation pipelines that can be executed real-time in a flow starting directly from the camera stream.

> [!NOTE]
> 
> ### Why medium weight?
> `napari-live-recording` relies on multithreading to handle camera control,
> image processing and data storage via a common pipelined infrastructure.
> More details are provided in the documentation.

The plugin allows the following operations:

- snapping: capture a single image
- live view: continously acquiring from the currently active camera and show the collected data on the napari viewer;
- recording: stream data to disk from the currently active cameras

When recording, the plugin allows to store images according to the following formats:

- ImageJ TIFF
- OME-TIFF

> [!NOTE]
> Future releases will also add further file formats to the recording options, specifically:
> - HDF5
> - MP4
>
> We will also provide a method to add custom metadata to the recorded image files.

## Supported cameras

`napari-live-recording` aims to maintain itself agnostic for the type of cameras it controls. Via a common API (Application Programming Interface),
it possible to define a controller for a specific camera. Instructions
on how to do so are provided in the documentation.

By default, the plugin is shipped with the following interfaces:

- an [OpenCV](./src/napari_live_recording/control/devices/opencv.py) camera grabber;
- a [Micro-Manager](./src/napari_live_recording/control/devices/micro_manager.py) interface via the package [`pymmcore-plus`](https://pypi.org/project/pymmcore-plus/);
- an interface to the [microscope](./src/napari_live_recording/control/devices/pymicroscope.py) python package.

## Documentation

To install and use the plugin you can review the documentation [here](./docs/documentation.md).

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## Acknowledgments

The developers would like to thank the [Chan-Zuckerberg Initiative (CZI)](https://chanzuckerberg.com/) for providing funding
for this project via the [napari Ecosystem Grants](https://chanzuckerberg.com/science/programs-resources/imaging/napari/napari-live-recording-camera-control-through-napari/).

<p align="center">
  <img src="https://images.squarespace-cdn.com/content/v1/63a48a2d279afe2a328b2823/5830fddc-a02b-451a-827b-3d4446dcf57b/Chan_Zuckerberg_Initiative.png" width="150">
</p>

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
