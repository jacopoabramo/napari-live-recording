# add neccesarry imports here
import cv2 as cv
import numpy as np

# list kwargs of the filter function here like parametersDict = {"sigma" : 1.0, "gamma": 2.0 }
parametersDict = {"threshold1": 20, "threshold2": 70}

parametersHints = {"threshold1": "int, larger zero", "threshold2": "int, larger zero"}


# filter function


def canny(image, threshold1, threshold2):
    output = cv.Canny(image, threshold1, threshold2)
    return output
