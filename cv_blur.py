import cv2 as cv
import numpy as np

# list kwargs of the filter function here like parametersDict = {"sigma" : 1.0, "gamma": 2.0 }
parametersDict = {"ksize": (10, 10)}

parametersHints = {"ksize": "ituple represnting the kernel size"}

functionDescription = "Blurs an image using the normalized box filter."


# filter function


def cv_blur(image, ksize):
    output = cv.blur(image, ksize)
    return output
