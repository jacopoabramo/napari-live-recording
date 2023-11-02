import logging
from napari_live_recording import NapariLiveRecording


logger = logging.getLogger(__name__)

def test_widget_startup_and_cleanup(recording_widget):
    widget : NapariLiveRecording = recording_widget

    assert widget.anchor.selectionWidget.camerasComboBox.value == ("Select device", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    # always close for each test
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

    # always close for each test
    widget.on_close_callback()

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

def test_widget_add_mmcore_microscope_devices(recording_widget):
    widget : NapariLiveRecording = recording_widget

    # add microscope device
    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(3) # Microscope
    widget.anchor.selectionWidget.microscopeModuleComboBox.combobox.setCurrentIndex(4) # simulators
    widget.anchor.selectionWidget.microscopeDeviceComboBox.combobox.setCurrentIndex(0) # SimulatedCamera

    widget.anchor.selectionWidget.addButton.click()

    # add mmcore device
    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(1) # MicroManager
    widget.anchor.selectionWidget.adapterComboBox.combobox.setCurrentIndex(8) # DemoCamera
    widget.anchor.selectionWidget.deviceComboBox.combobox.setCurrentIndex(0) # DCam

    widget.anchor.selectionWidget.addButton.click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 2
    assert len(list(widget.mainController.deviceControllers.keys())) == 2
    assert "MyCamera:Microscope:simulators SimulatedCamera" in list(widget.anchor.cameraWidgetGroups.keys())
    assert "MyCamera:MicroManager:DemoCamera DCam" in list(widget.anchor.cameraWidgetGroups.keys())

    # delete each camera; the delete button is nested a bit deep;
    # .layout() -> returns the QVBoxLayout of the cameraWidgetGroup tab;
    # .itemAt(1) -> returns the element of the layout;
    # .widget() -> returns the QGroupBox;
    # .layout() -> returns the QFormLayout of the QGroupBox;
    # .itemAt(0) -> returns the first element of the layout (the delete button);
    # .widget() -> returns the QPushButton;
    # .click() -> clicks the button
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout().itemAt(1).widget().layout().itemAt(0).widget().click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 1
    assert len(list(widget.mainController.deviceControllers.keys())) == 1

    widget.anchor.cameraWidgetGroups["MyCamera:MicroManager:DemoCamera DCam"].layout().itemAt(1).widget().layout().itemAt(0).widget().click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 0
    assert len(list(widget.mainController.deviceControllers.keys())) == 0
    