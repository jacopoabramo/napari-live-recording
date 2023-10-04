# Changelog

## 0.3.2

Removed reference of tifffile enumerator `PHOTOMETRIC` (see #22)

## 0.3.1

- Added missing reference to `pymmcore-widgets` from `setup.cfg`
- Added exception print when initializing list of available camera interfaces

## 0.3.0

- Full rework of the plugin architecture ad user interface (hopefully for the last time)
- Removed old device interface documentation
- Fixed issues #16, #17
- Added MicroManager interface (@felixwanitschke)

## 0.2.1

- Added documentation of new architecture

## 0.2.0

- Full architecture rework
- Deleted old documentation
- Adapted plugin to be compatible with `npe2`

## 0.1.7

- Added better support for OpenCV ROI handling
- Added support for multiple pixel formats for OpenCV

## 0.1.6

- Minor fixes

## 0.1.5

- Added live frame per second count (still imprecise)
- Added Album mode (each manually acquired image showed on same layer)
- Fixed ROI handling with more meaningful syntax
- Fixed some problems with Ximea camera
- Changed special function interface

## 0.1.4

- Added ROI handling

## 0.1.3

- Added ReadTheDocs documentation.

## 0.1.2

- Fixed Ximea package import causing plugin to crash
- Added list of cameras in documentation
- Changed abstract methods of ICameras by removing unnecessary exceptions

## 0.1.1

- Added documentation
- Generic fixes

## 0.1.0

- First release