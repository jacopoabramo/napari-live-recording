# Processing Engine

The general idea of the processing engine is that you can create custom filters that can be applied to acquired frames in the plugin. This enables the direct recording of alredy processed images, which might be convenient for everyday work. Those custom filters can actually consist of several single filter functions that are arranged in a certain order in which they wil work on the frames. So each of the single filters will be applied one after another resulting in a total effect on the frame. A user interface enables the convenient creation of those custom filters which will be referred to as **filter-groups**.

## 1. Filter Creation

A filter creation window opens when the **"Create Filter"** button in the recording widget is pressed.

<p align="center">
  <img src="./create-filter.png.png">
</p>

The filter creation window is displayed in the following image and is operated from left to right.

<p align="center">
  <img src="./filter-creation-window.png">
</p>

The left list contains all the filters that are currently available to the plugin. Each filter (basically a function that takes an array-like image as an input, does some calculations and outputs the new image) needs to be definded in a python file following a certain pattern (which will be described in the next chapter). A new filter can be added by loading a file containing such a funcion into the plugin. This is done by simply clicking the "Add new Function" button in the lower left corner. A file dialog window will open und you can select the desired python file. The new filter should then be displayed in the left list. All filters in the left list can be searched for via the search bar above the left list.

The list in the centers serves for the purpose of creating new filter-groups. You can arrange certain filter functions in your desired order to create your custom filter. For this, just **drag and drop a filter from the left list to the right list** to add this filter to the filter-group. If you have added all functions needed, you can **arrange** them in a specific order, again **by drag and drop inside the right list**. A single filter-function can also be added twice to a custom filter by dragging it into the right list a second time. Filters from the right list can be **deleted by dragging them outside the right list**. You can delete all filters at once by clicking the "Clear" button. When an **item (a filter) in the right list is double clicked**, it's corresponding parameters are shown in a separate window, you can also **change certain parameters** here. It is for instance possible to apply the same filter function twice but with different parameters. You can test the action of your current filter group on a sample image by clicking the "Refresh" button in the left collumn. When changes are applied to the filter-group in the list you need to press the "Refresh" button again to see the result. You can also load your own sample image by clicking the "Load new Image" Button in the right collumn. When you are happy with the result of your filter-group, you **need to name your custom filter** (in the line with the label "Filter Name") and then **press the "Create Filter-Group"** Button in the central collumn. Your filter is now saved. When you try to create a filter with the same **name** as one that **already exists**, the old filter will be **overwritten**.

<p align="center">
  <img src="./existing-filters.png">
</p>

By clicking the **"Show Existing Filters" button you can display the already existing filter-groups** (i.e. custom filters) referenced by their name. In the window you can delete a selected filter. You can also **load an already existing filter** by pressing the "Load" button. the filter will be loaded to the central list of the filter-creation window. Note, filter-functions that might be in this list at that state are deleted when an old filter is loaded. Loading of an old filter can serve for ammending this filter or can serve as a basis for a new filter. Remember to name your filter accordingly.
The filter "No Filter" is always there. 
After you are done, your custom filters will be available for recording (How this is done will be discussed in one of the follwing chapters). 

## 2. Creating new filter functions

To create new filter functions you need to create a python file that contains this function anywhere on your PC. This file can later be loaded into the plugin. This file has to follow a certain pattern to work properly.
A template filter function is shown below:

```py
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
```







