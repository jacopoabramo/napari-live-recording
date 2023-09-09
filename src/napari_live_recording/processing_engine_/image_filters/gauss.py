import numpy as np
from scipy import ndimage


parametersDict = {"shape": (3, 3), "sigma": 0.5}

parametersHints = {"shape": "tuple,uneven numbers", "sigma": "float"}


def matlab_style_gauss2D(image, shape, sigma):
    """
    2D gaussian mask - should give the same result as MATLAB's
    fspecial('gaussian',[shape],[sigma])
    """
    m, n = [(ss - 1.0) / 2.0 for ss in shape]
    y, x = np.ogrid[-m : m + 1, -n : n + 1]
    h = np.exp(-(x * x + y * y) / (2.0 * sigma * sigma))
    h[h < np.finfo(h.dtype).eps * h.max()] = 0
    sumh = h.sum()
    if sumh != 0:
        h /= sumh

    image = ndimage.correlate(image, h, mode="constant", origin=-1)
    return image
