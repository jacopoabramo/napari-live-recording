import cv2 as cv

# list args of the filter function and their desired default values in the parameterDict
default_value1 = 20
default_value2 = 70
parametersDict = {"parameter1": default_value1, "parameter2": default_value2}

# give parameter hints for every parameter in paametersDict. This should contain a description as well as a hint which values (like:possible range, even/uneven numbers, parameter1 has to be larger than parameter2 ...) are allowed and which data-type is required.
parametersHints = {
    "parameter1": "First threshold for the hysteresis procedure., needs to be smaller than parameter2, integer values",
    "parameter2": "Second threshold for the hysteresis procedure, integer values",
}

# give a description of the function
functionDescription = "Finds edges in an image using the Canny algorithm. The function finds edges in the input image and marks them in the output map edges using the Canny algorithm. The smallest value between threshold1 and threshold2 is used for edge linking. The largest value is used to find initial segments of strong edges. See http://en.wikipedia.org/wiki/Canny_edge_detector"


# use your desired function here. First input of the function is always the input-image.
# Followed by positional parameters. The output-image is returned.


def cv_canny(input, threshold1, threshold2):
    output = cv.Canny(input, threshold1, threshold2)
    return output
