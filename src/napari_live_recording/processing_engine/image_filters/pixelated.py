# add neccesarry imports here


# list kwargs of the filter function here like parametersDict = {"sigma" : 1.0, "gamma": 2.0 }
parametersDict = {}
parametersHints = {}


functionDescription = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

# filter function


def pixelate(input):
    # do something
    output = input[::30, ::30]
    return output
