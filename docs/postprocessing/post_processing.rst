Implementing new functions
=============================

To implement new functions, clone the git repository:

.. code-block::

    git clone https://github.com/jacopoabramo/napari-live-recording

These are the steps required to integrate a new post-processing function.

- In ``napari_live_recording/Functions/Functions.py``, define your function. An example already is provided:

.. code-block:: python

    def average_image_stack(stack : list) -> np.array:
    """Calculates the average of a stack of images

    :param stack: input image stack
    :type stack: list
    :return: image representing the average of the stack
    :rtype: numpy.array
    """
    # sum all averaged images into an accumulator
    accumulator = np.zeros(stack[0].shape, np.float)
    for image in stack:
        accumulator += np.array(image, np.float)
    accumulator /= len(stack)

    # return rounded accumulator
    return np.array(np.round(accumulator), "uint8")

- Post-processing functions accept a list of numpy 2D arrays as input;
- They can return either a list or a single numpy array.

After defining your function, in ``napari_live_recording/Functions/__init__.py``:

- in ``napari_live_recording/Functions/__init__.py``, add to the ``special_functions`` dictionary:
  
  - a string which identifies your function as key,
  - the function name as value;

- Finally, add the name of your function as a string in the ``__all__`` list.

If everything went well, when applying post-processing, your function will appear in the combobox list.
