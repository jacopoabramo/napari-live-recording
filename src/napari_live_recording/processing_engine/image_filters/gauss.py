import numpy as np
from scipy import ndimage


dc = {"shape": (3, 3), "sigma": 0.5}

# def blur(a):
#     kernel = np.array([[1.0, 2.0, 1.0], [2.0, 4.0, 2.0], [1.0, 2.0, 1.0]])
#     kernel = kernel / np.sum(kernel)
#     arraylist = []
#     for y in range(3):
#         temparray = np.copy(a)
#         temparray = np.roll(temparray, y - 1, axis=0)
#         for x in range(3):
#             temparray_X = np.copy(temparray)
#             temparray_X = np.roll(temparray_X, x - 1, axis=1) * kernel[y, x]
#             arraylist.append(temparray_X)

#     arraylist = np.array(arraylist)
#     arraylist_sum = np.sum(arraylist, axis=0)
#     return arraylist_sum


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
