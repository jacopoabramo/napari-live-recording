Adding support for a new camera
===============================

To add a new camera to be supported, clone the git repository:

.. code-block::

    git clone https://github.com/jacopoabramo/napari-live-recording

These are the steps required to integrate in the plugin new devices.

- Create a new Python class in ``napari_live_recording/Cameras`` with the name of your device, for example ``MyCamera.py``;

  - The class must be inherited from the ``ICamera`` interface;
- Implement all the abstract methods of ``ICamera``;
- Define a name for your device by adding a constant string outside the class definition, i.e. ``CAM_MYCAMERA = "My test camera"``;
- In ``napari_live_recording/Cameras/__init__.py``, add your camera to the ``supported_cameras`` dictionary:
  
  - the name of your camera as key,
  - the class of your camera as value (don't forget to include the class in ``__init__.py``);

- Finally, append the name of your class as a string object in the ``__all__`` list.

To test the newly added camera, install the plugin by navigating inside the ``napari_live_recording``:

.. code-block::

    pip install .

If everything went well, when choosing a new camera, yours will appear in the combobox list.
