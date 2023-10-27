import logging
from napari_live_recording import NapariLiveRecording

logger = logging.getLogger(__name__)

def test_mmcore_settings_change(recording_widget):
    widget : NapariLiveRecording = recording_widget

    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(1) # MicroManager
    widget.anchor.selectionWidget.adapterComboBox.combobox.setCurrentIndex(8) # DemoCamera
    widget.anchor.selectionWidget.deviceComboBox.combobox.setCurrentIndex(0) # DCam

    assert widget.anchor.selectionWidget.adapterComboBox.value == ("DemoCamera", 8)
    assert widget.anchor.selectionWidget.deviceComboBox.value == ("DCam", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    widget.anchor.selectionWidget.addButton.click()

    assert "MyCamera:MicroManager:DemoCamera DCam" in list(widget.anchor.cameraWidgetGroups.keys())

    # always close for each test
    widget.on_close_callback()