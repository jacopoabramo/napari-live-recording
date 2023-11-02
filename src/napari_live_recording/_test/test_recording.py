import logging
from napari import Viewer
from napari_live_recording import NapariLiveRecording

logger = logging.getLogger(__name__)

def test_mmcore_live_recording(recording_widget):
    widget : NapariLiveRecording = recording_widget

    viewer : Viewer = widget.anchor.viewer

    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(1) # MicroManager
    widget.anchor.selectionWidget.adapterComboBox.combobox.setCurrentIndex(8) # DemoCamera
    widget.anchor.selectionWidget.deviceComboBox.combobox.setCurrentIndex(0) # DCam

    widget.anchor.selectionWidget.addButton.click()

    widget.anchor.recordingWidget.live.toggle()

    assert widget.mainController.isLive == True

    widget.anchor.recordingWidget.live.toggle()

    assert widget.mainController.isLive == False

    # the plugin when acquiring live produces a layer with the ID of the camera;
    # we can check if the layer is present or not

    # TODO: apparently the layer is not created in the test environment;
    # investigate why
    # layer = viewer.layers["Live MyCamera:MicroManager:DemoCamera DCam"]
    # logger.info(f"Layer: {layer.name}")