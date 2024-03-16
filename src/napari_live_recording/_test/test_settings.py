from napari_live_recording.common import ROI
from typing import TYPE_CHECKING
from typing import Union
from qtpy.QtWidgets import QScrollArea
from qtpy.QtWidgets import QComboBox, QSlider
from superqt import QLabeledDoubleSlider

if TYPE_CHECKING:
    from napari_live_recording import NapariLiveRecording

def set_roi(widget: "NapariLiveRecording", height: int, width: int, offset_x: int, offset_y: int, cam_name: str):
    """Helper function to set the ROI of a widget."""
    
    roi_widget = widget.anchor.cameraWidgetGroups[cam_name].roiWidget
    roi_widget.heightSpinBox.setValue(height)
    roi_widget.widthSpinBox.setValue(width)
    roi_widget.offsetXSpinBox.setValue(offset_x)
    roi_widget.offsetYSpinBox.setValue(offset_y)
    roi_widget.changeROIButton.click()

def change_parameter(widget: "NapariLiveRecording", cam_name: str, param_index: int, value: Union[float, int, str, bool]):
    """Helper function to change a parameter of a widget."""
    
    camera_widget_group = widget.anchor.cameraWidgetGroups[cam_name]
    scrollArea : QScrollArea = camera_widget_group.layout.itemAt(1).widget()
    layout = scrollArea.widget().layout()
    widget = layout.itemAt(param_index, 1).widget()
    if type(widget) == QComboBox:
        widget.setCurrentIndex(value)
    elif type(widget) == QSlider or type(widget) == QLabeledDoubleSlider:
        widget.setValue(value)
    
    # item = layout.itemAt(param_index)
    # widget = item.widget()
    # widget_layout = widget.layout()
    # target_widget = widget_layout.itemAt(param_index, 1).widget()
    # target_widget.setValue(value)

def test_mmcore_settings_change(recording_widget):
    full_cam_name = "MyCamera:MicroManager:DemoCamera DCam"
    
    widget : "NapariLiveRecording" = recording_widget

    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(1) # MicroManager
    widget.anchor.selectionWidget.adapterComboBox.combobox.setCurrentIndex(8) # DemoCamera
    widget.anchor.selectionWidget.deviceComboBox.combobox.setCurrentIndex(0) # DCam

    assert widget.anchor.selectionWidget.adapterComboBox.value == ("DemoCamera", 8)
    assert widget.anchor.selectionWidget.deviceComboBox.value == ("DCam", 0)
    assert widget.anchor.selectionWidget.nameLineEdit.value == "MyCamera"

    widget.anchor.selectionWidget.addButton.click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 1
    assert len(list(widget.mainController.deviceControllers.keys())) == 1
    assert full_cam_name in list(widget.anchor.cameraWidgetGroups.keys())
        
    # Set the ROI using the helper function
    set_roi(widget, height=256, width=256, offset_x=128, offset_y=128, cam_name=full_cam_name)

    target_roi = ROI(128, 128, 256, 256)
    new_roi = widget.mainController.deviceControllers[full_cam_name].device.roiShape

    assert target_roi == new_roi
    assert target_roi.pixelSizes == new_roi.pixelSizes

def test_microscope_settings_change(recording_widget):
    full_cam_name = "MyCamera:Microscope:simulators SimulatedCamera"
    
    widget : "NapariLiveRecording" = recording_widget

    # add microscope device
    widget.anchor.selectionWidget.camerasComboBox.combobox.setCurrentIndex(3) # Microscope
    widget.anchor.selectionWidget.microscopeModuleComboBox.combobox.setCurrentIndex(6) # simulators
    widget.anchor.selectionWidget.microscopeDeviceComboBox.combobox.setCurrentIndex(0) # SimulatedCamera

    widget.anchor.selectionWidget.addButton.click()

    assert len(list(widget.anchor.cameraWidgetGroups.keys())) == 1
    assert len(list(widget.mainController.deviceControllers.keys())) == 1
    assert full_cam_name in list(widget.anchor.cameraWidgetGroups.keys())
    
    # Set the ROI using the helper function
    set_roi(widget, height=256, width=256, offset_x=128, offset_y=128, cam_name=full_cam_name)

    target_roi = ROI(128, 128, 256, 256)
    new_roi = widget.mainController.deviceControllers[full_cam_name].device.roiShape

    assert target_roi == new_roi
    assert target_roi.pixelSizes == new_roi.pixelSizes

    # image pattern (generic parameter) (index: 0)
    change_parameter(widget, full_cam_name, 0, 1)
    
    assert widget.mainController.deviceControllers[full_cam_name].device.parameters["image pattern"].value == "gradient"
    
    # exposure time parameter (index: 5)
    change_parameter(widget, full_cam_name, 5, 0.03)

    assert widget.mainController.deviceControllers[full_cam_name].device.parameters["Exposure time"].value == 0.03




