import typing
from PyQt5 import QtGui
from qtpy.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QWidget,
    QDialog,
    QLabel,
    QMessageBox,
    QMainWindow,
    QVBoxLayout,
)
from pyqtgraph import ImageView
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from ast import literal_eval
import pims, math
from napari_live_recording.processing_engine_.image_filters import *
from napari_live_recording.common import filtersDict, createPipelineFilter, Settings
import functools
from napari_live_recording.processing_engine_ import image_filters
import importlib
import pkgutil
from qtpy.QtCore import Qt, Signal
import shutil
import sys, os, glob
from qtpy.QtGui import QPixmap, QImage, QDropEvent
from qtpy.QtWidgets import (
    QWidget,
    QComboBox,
    QLineEdit,
    QLabel,
    QFormLayout,
    QGridLayout,
    QPushButton,
    QFileDialog,
    QScrollArea,
    QMainWindow,
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QListWidgetItem,
    QDialogButtonBox,
    QSizePolicy,
    QCompleter,
    QListWidget,
    QTableWidget,
    QAbstractItemView,
)


class LeftList(QListWidget):
    """Left list widget with functions available for image processing."""

    DragDropSignalLeft = Signal()

    def __init__(self, parent=None):
        super(LeftList, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSortingEnabled(True)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSelectionRectVisible(True)
        self.setAcceptDrops(False)

    def convertFunctionsDictToItemList(self, functionsDict: dict):
        # itemList = []
        if functionsDict == None:
            pass
        else:
            for key in functionsDict.keys():
                function = functionsDict[key][0]
                parametersDict = functionsDict[key][1]
                parametersHints = functionsDict[key][2]
                functionDescription = functionsDict[key][3]
                item = QListWidgetItem()
                item.setText(key[2:])
                item.setToolTip(functionDescription)
                item.setData(Qt.UserRole, [function, parametersDict, parametersHints])
                self.addItem(item)

    def convertItemListToDict(self):
        functionsDict = {}
        for i in range(self.count()):
            item = self.item(i)
            functionsDict[f"{i+1}." + item.text()] = [
                item.data(Qt.UserRole)[0],
                item.data(Qt.UserRole)[1],
                item.data(Qt.UserRole)[2],
                item.toolTip(),
            ]
        return functionsDict

    # def dragEvent(self, event: QDropEvent) -> None:
    #     self.DragDropSignalLeft.emit()
    #     return super().dropEvent(event)


class RightList(QListWidget):
    """Right list widget with functions to be used for image processing. Individual items are sortable, to delete individual items, the items can simply be dragged into the left list. It is possible to have the same function multiple times"""

    DragDropSignalRight = Signal()

    def __init__(self, parent=None):
        super(RightList, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionRectVisible(True)
        self.setSortingEnabled(True)

    def convertFunctionsDictToItemList(self, functionsDict: dict):
        # itemList = []
        if functionsDict == None:
            pass
        else:
            for key in functionsDict.keys():
                function = functionsDict[key][0]
                parametersDict = functionsDict[key][1]
                parametersHints = functionsDict[key][2]
                functionDescription = functionsDict[key][3]
                item = QListWidgetItem()
                item.setText(key[2:])
                item.setToolTip(functionDescription)
                item.setData(Qt.UserRole, [function, parametersDict, parametersHints])
                self.addItem(item)

    def convertItemListToDict(self):
        functionsDict = {}
        for i in range(self.count()):
            item = self.item(i)
            functionsDict[f"{i+1}." + item.text()] = [
                item.data(Qt.UserRole)[0],
                item.data(Qt.UserRole)[1],
                item.data(Qt.UserRole)[2],
                item.toolTip(),
            ]
        return functionsDict

    # def dropEvent(self, event: QDropEvent) -> None:
    #     self.DragDropSignalRight.emit()
    #     return super().dropEvent(event)


class ParameterDialog(QDialog):
    """Dialog Window to change parameters of function that are inside the right list."""

    def __init__(self, parameters, parameterHints, parent=None):
        super(ParameterDialog, self).__init__(parent)

        self.setWindowTitle("Change Parameters")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.parameters = parameters
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.parameterDialogLayout = QFormLayout()
        self.setLayout(self.parameterDialogLayout)
        self.lineEdits = {}
        for parameter, value in self.parameters.items():
            lineEdit = QLineEdit(f"{value}")
            lineEdit.setToolTip(parameterHints[parameter])
            self.lineEdits[parameter] = lineEdit
            self.parameterDialogLayout.addRow(parameter, self.lineEdits[parameter])
        self.parameterDialogLayout.addWidget(self.buttonBox)

    def getValues(self):
        """Get the values from the linedits and interpret the strings as values for the parameters. '(1,2)' will be interpreted as tuple(1,2)

        Returns
        -------
        dict
            dictionary containing the entered values
        """
        for linedit in self.lineEdits.keys():
            self.lineEdits[linedit] = literal_eval(self.lineEdits[linedit].text())
        return self.lineEdits


class ShowFiltersDialog(QDialog):
    """Dialog Window to change parameters of function that are inside the right list."""

    filterDeleted = Signal()

    def __init__(self, parent=None):
        super(ShowFiltersDialog, self).__init__(parent)

        self.setWindowTitle("Exisiting Filters")
        self.buttonBox = QDialogButtonBox()
        self.settings = Settings()
        self.filtersDict = self.settings.getFiltersDict()
        self.buttonBox.addButton(QDialogButtonBox.Ok)
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Load Filter")
        self.buttonBox.button(QDialogButtonBox.Cancel).setText("Delete Filter")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.deleteFilter)
        # self.buttonBox.addButton("Delete Filter", QDialogButtonBox.ActionRole)
        self.parameterDialogLayout = QVBoxLayout()
        self.listWidget = QListWidget()
        for filter in self.filtersDict.keys():
            item = QListWidgetItem()
            item.setText(filter)
            self.listWidget.addItem(item)
        self.setLayout(self.parameterDialogLayout)
        self.parameterDialogLayout.addWidget(self.listWidget)
        self.parameterDialogLayout.addWidget(self.buttonBox)

        # self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.deleteFilter)

    def deleteFilter(self):
        selectedItems = self.listWidget.selectedItems()
        if not selectedItems:
            return
        for item in selectedItems:
            self.listWidget.takeItem(self.listWidget.row(item))
            text = item.text()
            print(text)
            _ = self.filtersDict.pop(text)
            self.settings.setFiltersDict(self.filtersDict)
            print("filterDeleted")
        self.filterDeleted.emit()


class FilterSelectionWidget(QWidget):
    """Main Window containing two lists, one Right List and one Left List. Drag items from the left to the right list to add them to the processing pipeline. The left listed can be searched for items. New items can be loaded from files.The right list can be cleared. By applying the right list, the functions (associated eith the items in the right list) will be put in to a processing pipeline."""

    filterAdded = Signal()

    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.settings = Settings()
        self.filtersDict = self.settings.getFiltersDict()
        self.filters_folder = (
            r"src\napari_live_recording\processing_engine_\image_filters"
        )
        self.initializeMainWindow()

        self.loadFiles()

    def dragEnterEvent(self, e):
        e.accept()

    def openParameterDialogWindow(self, item: QListWidgetItem):
        """Dialog Window that gets opened when a item in the right list is double clicked.

        Parameters
        ----------
        item : QListWidgetItem
            _description_
        """
        dialog = ParameterDialog(item.data(Qt.UserRole)[1], item.data(Qt.UserRole)[2])
        answer = dialog.exec_()

        # if the user presses accept, then change the parameters of the corresponding function

        if answer:
            data = item.data(Qt.UserRole)
            values = dialog.getValues()
            data[1] = values
            item.setData(Qt.UserRole, data)
            data = item.data(Qt.UserRole)

        dialog.show()

    def dropEvent(self, e):
        e.accept()

    def loadFiles(self):
        """load the files from the folder 'image filters' and and load the functions from each file. The functions and parameters are stored as data associated with each item."""
        # ERROR:funktioniert nur für module die über programm reingeladen wurden
        self.leftList.clear()
        moduleList = []
        for importer, modname, ispkg in pkgutil.iter_modules(image_filters.__path__):
            if not modname == "__init__":
                moduleList.append(
                    "napari_live_recording.processing_engine_.image_filters." + modname
                )
        for module in map(importlib.import_module, moduleList):
            for func in filter(callable, module.__dict__.values()):
                loadedInformation = [
                    func,
                    module.parametersDict,
                    module.parametersHints,
                ]
                item = QListWidgetItem()
                item.setText(func.__name__)
                item.setToolTip(module.functionDescription)
                item.setData(Qt.UserRole, loadedInformation)
                self.leftList.addItem(item)

    def clearListWidget(self):
        """Clearing the right list."""
        self.rightList.clear()
        self.filterNameLineEdit.clear()

    def returnRightListContent(self, isPreview: bool = False):
        """Use the items in the right list in their current order and create a nested function from them. For creating the nested function 'pims' used to achieve lazy evaluation."""
        functionsDict = self.rightList.convertItemListToDict()
        filterName = self.filterNameLineEdit.text()

        if isPreview:
            composedFunction = createPipelineFilter(functionsDict)
            return composedFunction
        else:
            if filterName == "":
                self.alertWindow("Please Name your Filter-Group.")
            else:
                self.filtersDict = self.settings.getFiltersDict()
                self.filtersDict[filterName] = functionsDict
                self.settings.setFiltersDict(self.filtersDict)
                print("Filter Added")
                self.filterAdded.emit()

    def updatePreviewImage(self):
        try:
            currentFilterGroup = self.returnRightListContent(True)
            newImage = currentFilterGroup(self.image)
            self.imageView.setImage(newImage)
        except Exception as e:
            self.alertWindow(str(e))
            print("Error", e)

    def alertWindow(self, text):
        dialog = QMessageBox()
        dialog.setText("Current Filters not applicable:  " + text)
        dialog.exec()

    def update_display(self, text: str):
        """Update the left list, i.e. hide items in the left list. Is used when text in the searchbar is changed.

        Parameters
        ----------
        text : str
            Input from the searchbar
        """
        for i in range(self.leftList.count()):
            item = self.leftList.item(i)
            item.setHidden(True)
        items = self.leftList.findItems(text, Qt.MatchContains)
        for item in items:
            item.setHidden(False)

    def addFiles(self):
        """Adds selected files from QFiledialog to the 'image_filters'folder. After that the 'image_filters' folders is loaded again."""
        filepaths, _ = QFileDialog.getOpenFileNames(
            self, caption="Load files", filter="Python Files (*.py)"
        )
        for filepath in filepaths:
            if filepath != "":
                shutil.copy(filepath, self.filters_folder)
        self.loadFiles()

    def showExistingFilters(self):
        global emitFilterAdded

        def emitFilterAdded():
            print("filter added emit")

        existingFiltersDialog = ShowFiltersDialog()
        accept = existingFiltersDialog.exec()
        # existingFiltersDialog.filterDeleted.connect(emitFilterAdded)

        if accept:
            self.clearListWidget()
            item = existingFiltersDialog.listWidget.currentItem()
            text = item.text()
            functionsDict = self.filterDict[text]
            self.rightList.convertFunctionsDictToItemList(functionsDict)
        else:
            self.filterAdded.emit()
        existingFiltersDialog.show()

    def loadPreviewImage(self, isDefault=False):
        if isDefault:
            if self.settings.settings.contains("Preview Image"):
                self.image = self.settings.getSetting("Preview Image")
            else:
                image_ = cv.imread(
                    r"C:\git\napari-live-recording\src\napari_live_recording\processing_engine_\testImage.jpg"
                )
                aspectRatio = image_.shape[0] / image_.shape[1]
                self.image = cv.resize(
                    image_,
                    dsize=(int(280 * aspectRatio), 400),
                    interpolation=cv.INTER_CUBIC,
                )
            self.imageView.setImage(self.image)
            # return image
        else:
            try:
                filepath, _ = QFileDialog.getOpenFileName(
                    self,
                    caption="Load new preview image",
                    filter="Image Files (*.png *.jpg *jpeg)",
                )
                image_ = cv.imread(filepath)
                aspectRatio = image_.shape[0] / image_.shape[1]
                self.image = image_
                # cv.resize(
                #     image_,
                #     dsize=(int(280 * aspectRatio), 400),
                #     interpolation=cv.INTER_CUBIC,
                # )
                self.settings.setSetting("Preview Image", self.image)
                self.imageView.setImage(self.image)
            except:
                pass

    def initializeMainWindow(self):
        """Creates the widgets and the layouts of the MainWindow"""
        self.setAcceptDrops(True)
        self.leftContainer = QGroupBox()
        self.leftContainerLayout = QGridLayout()
        self.leftContainer.setLayout(self.leftContainerLayout)

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)
        self.searchbar.setClearButtonEnabled(True)

        self.load_btn = QPushButton("Add new Function")
        self.load_btn.clicked.connect(self.addFiles)
        self.leftList = LeftList()

        self.leftContainerLayout.addWidget(self.searchbar, 0, 0, 1, 2)
        self.leftContainerLayout.addWidget(self.leftList, 1, 0, 1, 2)
        self.leftContainerLayout.addWidget(self.load_btn, 2, 0, 1, 2)

        self.rightContainer = QGroupBox()
        self.rightContainerLayout = QGridLayout()
        self.rightContainer.setLayout(self.rightContainerLayout)

        self.rightList = RightList()
        self.rightList.count
        self.rightList.setMouseTracking(True)
        # self.rightList.itemChanged.connect(self.updatePreviewImage)
        # self.rightList.DragDropSignalRight.connect(self.updatePreviewImage)
        # self.leftList.DragDropSignalLeft.connect(self.updatePreviewImage)
        # self.rightList.model().rowsRemoved.connect(self.updatePreviewImage)
        # self.rightList.model().rowsInserted.connect(self.updatePreviewImage)
        # self.rightList.model().rowsMoved.connect(self.updatePreviewImage)
        # self.rightList.itemEntered.connect(self.updatePreviewImage)
        # self.rightList.itemSelectionChanged.connect(self.updatePreviewImage)
        # self.rightList.currentItemChanged.connect(self.updatePreviewImage)
        # # self.rightList.currentRowChanged.connect(self.updatePreviewImage)
        # self.rightList.itemDoubleClicked.connect(self.updatePreviewImage)
        self.clear_btn = QPushButton("Clear")
        self.createFilter_btn = QPushButton("Create Filter-Group")
        self.filterNameLineEdit = QLineEdit()
        self.filterNameLabel = QLabel("Filter Name")
        self.loadExistingFilter_btn = QPushButton("Show Exisiting Filters")
        self.loadExistingFilter_btn.clicked.connect(self.showExistingFilters)
        # self.filterNameLineEdit.textChanged.connect(self.handleApply_btn)

        self.clear_btn.clicked.connect(self.clearListWidget)
        self.createFilter_btn.clicked.connect(self.returnRightListContent)
        self.rightList.itemDoubleClicked.connect(self.openParameterDialogWindow)
        # self.apply_btn.setDisabled(True)
        self.rightContainerLayout.addWidget(self.loadExistingFilter_btn, 0, 0, 1, 2)
        self.rightContainerLayout.addWidget(self.rightList, 1, 0, 1, 2)
        self.rightContainerLayout.addWidget(self.clear_btn, 3, 0)
        self.rightContainerLayout.addWidget(self.createFilter_btn, 3, 1)
        self.rightContainerLayout.addWidget(self.filterNameLabel, 2, 0)
        self.rightContainerLayout.addWidget(self.filterNameLineEdit, 2, 1)

        self.previewContainer = QGroupBox()
        self.previewContainerLayout = QGridLayout()
        self.previewContainer.setLayout(self.previewContainerLayout)
        self.refresh_btn = QPushButton("Refresh")
        self.loadNewPreviewImage_btn = QPushButton("Load new Image")

        self.refresh_btn.clicked.connect(self.updatePreviewImage)
        self.loadNewPreviewImage_btn.clicked.connect(self.loadPreviewImage)
        # self.image_ = cv.imread(
        #     r"C:\git\napari-live-recording\src\napari_live_recording\processing_engine_\testImage.jpg"
        # )
        # aspectRatio = self.image_.shape[0] / self.image_.shape[1]
        # self.image = cv.resize(
        #     self.image_,
        #     dsize=(int(280 * aspectRatio), 400),
        #     interpolation=cv.INTER_CUBIC,
        # )

        self.imageView = ImageView()
        # self.imageView.ui.histogram.hide()
        self.imageView.ui.roiBtn.hide()
        self.imageView.ui.menuBtn.hide()
        self.loadPreviewImage(True)
        #        self.imageView.setImage(self.loadPreviewImage(True))
        self.previewContainerLayout.addWidget(self.imageView, 0, 0, 1, 2)
        self.previewContainerLayout.addWidget(self.refresh_btn, 1, 0, 1, 1)
        self.previewContainerLayout.addWidget(self.loadNewPreviewImage_btn, 1, 1, 1, 1)

        layout = QHBoxLayout(self)
        layout.addWidget(self.leftContainer)
        layout.addWidget(self.rightContainer)
        layout.addWidget(self.previewContainer)


if __name__ == "__main__":
    # don't auto scale when drag app to a different monitor.
    # QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget {
            font-size: 15px;
        }
    """
    )

    myApp = FilterSelectionWidget()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
