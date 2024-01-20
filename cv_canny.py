import cv2 as cv
import numpy as np

# list kwargs of the filter function here like parametersDict = {"sigma" : 1.0, "gamma": 2.0 }
parametersDict = {"threshold1": 30, "threshold2": 70}

parametersHints = {"threshold1": "lower threshold", "threshold2": "Upper threshold"}

functionDescription = "Finds edges in an image using the Canny algorithm."


# filter function


def cv_canny(image, threshold1, threshold2):
    output = cv.Canny(image, threshold1, threshold2)
    return output
