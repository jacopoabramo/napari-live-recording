from napari_live_recording import NapariLiveRecording
from napari_live_recording.common import ROI

def test_mmcore_settings_change(recording_widget):
    widget : NapariLiveRecording = recording_widget

    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(1) # MicroManager
    widget.anchor.selectionWidget.adapterComboBox.combobox.setCurrentIndex(8) # DemoCamera
    widget.anchor.selectionWidget.deviceComboBox.combobox.setCurrentIndex(0) # DCam

    assert widget.anchor.selectionWidget.adapterComboBox.value == ("DemoCamera", 8)
    assert widget.anchor.selectionWidget.deviceComboBox.value == ("DCam", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    widget.anchor.selectionWidget.addButton.click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 1
    assert len(list(widget.mainController.deviceControllers.keys())) == 1
    assert "MyCamera:MicroManager:DemoCamera DCam" in list(widget.anchor.cameraWidgetGroups.keys())

    # parameters settings are handled by the pymmcore-plus widgets,
    # and are not part of the plugin source code; we will test only the ROI settings;
    # default DCam ROI is 512x512 pixels;
    # ROI control is nested as follows:
    # .layout() -> returns the QVBoxLayout of the cameraWidgetGroup tab;
    # .itemAt(1) -> returns the element of the layout;
    # .widget() -> returns the QGroupBox;
    # .layout() -> returns the QFormLayout of the QGroupBox;
    # .itemAt(1) -> returns the second element of the layout (the ROI widget);
    # .widget() -> returns the widget;
    # .click() -> clicks the button
    widget.anchor.cameraWidgetGroups["MyCamera:MicroManager:DemoCamera DCam"].layout().itemAt(1).widget().layout().itemAt(1).widget().heightSpinBox.setValue(256)
    widget.anchor.cameraWidgetGroups["MyCamera:MicroManager:DemoCamera DCam"].layout().itemAt(1).widget().layout().itemAt(1).widget().widthSpinBox.setValue(256)
    widget.anchor.cameraWidgetGroups["MyCamera:MicroManager:DemoCamera DCam"].layout().itemAt(1).widget().layout().itemAt(1).widget().offsetXSpinBox.setValue(128)
    widget.anchor.cameraWidgetGroups["MyCamera:MicroManager:DemoCamera DCam"].layout().itemAt(1).widget().layout().itemAt(1).widget().offsetYSpinBox.setValue(128)
    widget.anchor.cameraWidgetGroups["MyCamera:MicroManager:DemoCamera DCam"].layout().itemAt(1).widget().layout().itemAt(1).widget().changeROIButton.click()

    target_roi = ROI(128, 128, 256, 256)
    new_roi = widget.mainController.deviceControllers["MyCamera:MicroManager:DemoCamera DCam"].device.roiShape

    assert target_roi == new_roi
    assert target_roi.pixelSizes == new_roi.pixelSizes

def test_microscope_settings_change(recording_widget):
    widget : NapariLiveRecording = recording_widget

    # add microscope device
    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(3) # Microscope
    widget.anchor.selectionWidget.microscopeModuleComboBox.combobox.setCurrentIndex(4) # simulators
    widget.anchor.selectionWidget.microscopeDeviceComboBox.combobox.setCurrentIndex(0) # SimulatedCamera

    widget.anchor.selectionWidget.addButton.click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 1
    assert len(list(widget.mainController.deviceControllers.keys())) == 1
    assert "MyCamera:Microscope:simulators SimulatedCamera" in list(widget.anchor.cameraWidgetGroups.keys())

    # microscope default ROI is 512x512 pixels;
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout().itemAt(1).widget().layout().itemAt(1).widget().heightSpinBox.setValue(256)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout().itemAt(1).widget().layout().itemAt(1).widget().widthSpinBox.setValue(256)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout().itemAt(1).widget().layout().itemAt(1).widget().offsetXSpinBox.setValue(128)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout().itemAt(1).widget().layout().itemAt(1).widget().offsetYSpinBox.setValue(128)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout().itemAt(1).widget().layout().itemAt(1).widget().changeROIButton.click()

    target_roi = ROI(128, 128, 256, 256)
    new_roi = widget.mainController.deviceControllers["MyCamera:Microscope:simulators SimulatedCamera"].device.roiShape

    assert target_roi == new_roi
    assert target_roi.pixelSizes == new_roi.pixelSizes

    # microscope has two special parameters: "Exposure time" and "transform" which are handled separately;
    # widgets nested as follows:
    # .layout() -> returns the QVBoxLayout of the cameraWidgetGroup tab;
    # .itemAt(0) -> returns the element of the layout;
    # .widget() -> returns the QScrollArea;
    # .widget() -> returns the widget containing the parameters;
    # .layout() -> returns the QFormLayout of the widget;
    # .itemAt(0, 1) -> returns the first widget element of the layout (the "transform" widget; (0, 0) would return the label);
    # .widget() -> returns the QComboBox;
    # .setCurrentIndex(1) -> changes the value of the ComboBox to 1 "(False, False, True)"

    # transform parameter (index: 0)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout() \
                                                                                    .itemAt(0) \
                                                                                    .widget().widget() \
                                                                                    .layout() \
                                                                                    .itemAt(0, 1) \
                                                                                    .widget() \
                                                                                    .setCurrentIndex(1)


    assert widget.mainController.deviceControllers["MyCamera:Microscope:simulators SimulatedCamera"].device.parameters["transform"].value == "(False, False, True)"

    # exposure time parameter (index: 7)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout() \
                                                                                    .itemAt(0) \
                                                                                    .widget().widget() \
                                                                                    .layout() \
                                                                                    .itemAt(7, 1) \
                                                                                    .widget() \
                                                                                    .setValue(0.03)

    assert widget.mainController.deviceControllers["MyCamera:Microscope:simulators SimulatedCamera"].device.parameters["Exposure time"].value == 0.03

    # image pattern (generic parameter) (index: 2)
    widget.anchor.cameraWidgetGroups["MyCamera:Microscope:simulators SimulatedCamera"].layout() \
                                                                                .itemAt(0) \
                                                                                .widget().widget() \
                                                                                .layout() \
                                                                                .itemAt(2, 1) \
                                                                                .widget() \
                                                                                .setCurrentIndex(1)
    
    assert widget.mainController.deviceControllers["MyCamera:Microscope:simulators SimulatedCamera"].device.parameters["image pattern"].value == "gradient"




