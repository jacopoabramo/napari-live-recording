# add neccesarry imports here


# list kwargs of the filter function here like parametersDict = {"sigma" : 1.0, "gamma": 2.0 }
parametersDict = {}
parametersHints = {}

functionDescription = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin at molestie tortor, tempus suscipit felis. Maecenas imperdiet ultricies urna, aliquet mollis lorem varius vitae. Nulla a nisi neque. Ut at turpis feugiat, tincidunt est sit amet, imperdiet magna. Pellentesque et viverra eros. Phasellus tempor turpis vulputate lacus lobortis mattis. Donec."


# filter function


def pixelate(input):
    # do something
    output = input[::30, ::30]
    return output
