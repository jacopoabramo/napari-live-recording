import pytest
from napari_live_recording import NapariLiveRecording

@pytest.fixture
def recording_widget(make_napari_viewer):
    return NapariLiveRecording(make_napari_viewer())

@pytest.fixture(autouse=True)
def cleanup(recording_widget):
    """ Performs exit cleanup for the test suite."""
    # we yield control immediatly to the test;
    yield

    # after the test is done, we perform cleanup
    widget : NapariLiveRecording = recording_widget
    widget.on_close_callback()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 0
    assert len(list(widget.mainController.deviceControllers.keys())) == 0
