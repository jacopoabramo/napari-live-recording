# add neccesarry imports here
import cv2 as cv
import numpy as np

# list kwargs of the filter function here like parametersDict = {"sigma" : 1.0, "gamma": 2.0 }
parametersDict = {"threshold1": 20, "threshold2": 70}

parametersHints = {"threshold1": "int, larger zero", "threshold2": "int, larger zero"}

functionDescription = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin at molestie tortor, tempus suscipit felis. Maecenas imperdiet ultricies urna, aliquet mollis lorem varius vitae. Nulla a nisi neque. Ut at turpis feugiat, tincidunt est sit amet, imperdiet magna. Pellentesque et viverra eros. Phasellus tempor turpis vulputate lacus lobortis mattis. Donec."


# filter function


def canny(image, threshold1, threshold2):
    output = cv.Canny(image, threshold1, threshold2)
    return output
