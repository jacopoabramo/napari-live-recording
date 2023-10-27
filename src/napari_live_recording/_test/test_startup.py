import logging
import pytest
from napari_live_recording import NapariLiveRecording

logger = logging.getLogger(__name__)
    

@pytest.fixture
def recording_widget(make_napari_viewer):
    return NapariLiveRecording(make_napari_viewer())

def test_widget_startup_and_cleanup(recording_widget):
    widget : NapariLiveRecording = recording_widget

    assert widget.anchor.selectionWidget.camerasComboBox.value == ("Select device", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    widget.on_close_callback()


def test_widget_add_mmcore_test_device(recording_widget):
    widget : NapariLiveRecording = recording_widget

    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(1) # MicroManager
    widget.anchor.selectionWidget.adapterComboBox.combobox.setCurrentIndex(8) # DemoCamera
    widget.anchor.selectionWidget.deviceComboBox.combobox.setCurrentIndex(0) # DCam

    assert widget.anchor.selectionWidget.adapterComboBox.value == ("DemoCamera", 8)
    assert widget.anchor.selectionWidget.deviceComboBox.value == ("DCam", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    widget.anchor.selectionWidget.addButton.click()

    assert "MyCamera:MicroManager:DemoCamera DCam" in list(widget.anchor.cameraWidgetGroups.keys())

def test_widget_add_microscope_test_device(recording_widget):
    widget : NapariLiveRecording = recording_widget

    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(3) # Microscope
    widget.anchor.selectionWidget.microscopeModuleComboBox.combobox.setCurrentIndex(4) # simulators
    widget.anchor.selectionWidget.microscopeDeviceComboBox.combobox.setCurrentIndex(0) # SimulatedCamera

    assert widget.anchor.selectionWidget.microscopeModuleComboBox.value == ("simulators", 4)
    assert widget.anchor.selectionWidget.microscopeDeviceComboBox.value == ("SimulatedCamera", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    widget.anchor.selectionWidget.addButton.click()

    assert "MyCamera:Microscope:simulators SimulatedCamera" in list(widget.anchor.cameraWidgetGroups.keys())
    
    