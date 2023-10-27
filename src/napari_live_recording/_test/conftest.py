import pytest
from napari_live_recording import NapariLiveRecording

@pytest.fixture
def recording_widget(make_napari_viewer):
    return NapariLiveRecording(make_napari_viewer())
