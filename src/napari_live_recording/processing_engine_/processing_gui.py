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


class FilterSelectionWidget(QWidget):
    """Main Window containing two lists, one Right List and one Left List. Drag items from the left to the right list to add them to the processing pipeline. The left listed can be searched for items. New items can be loaded from files.The right list can be cleared. By applying the right list, the functions (associated eith the items in the right list) will be put in to a processing pipeline."""

    filtersReturned = Signal(tuple)

    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)

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
                tpl = [func, module.parametersDict, module.parametersHints]
                item = QListWidgetItem()
                item.setText(func.__name__)
                item.setToolTip(module.__file__)
                item.setData(Qt.UserRole, tpl)
                self.leftList.addItem(item)

    def clearListWidget(self):
        """Clearing the right list."""
        self.rightList.clear()
        self.filterNameLineEdit.clear()

    def createComposedFunction(self, isPreview: bool = False):
        """Use the items in the right list in their current order and create a nested function from them. For creating the nested function 'pims' used to achieve lazy evaluation."""

        def composeFunctions(functionList):
            return functools.reduce(
                lambda f, g: lambda x: f(g(x)), functionList, lambda x: x
            )

        filters = {}
        functionList = []
        for i in range(self.rightList.count()):
            item = self.rightList.item(i)
            filters[f"{i+1}." + item.text()] = item.data(Qt.UserRole)

        for filter in filters.values():
            functionList.append(
                pims.pipeline(functools.partial(filter[0], **filter[1]))
            )

        composedFunction = composeFunctions(list(reversed(functionList)))
        filterName = self.filterNameLineEdit.text()
        if filterName == "" and not isPreview:
            self.alertWindow("Please Name your filter.")
        else:
            self.filtersReturned.emit((composedFunction, filters, filterName))
            return composedFunction, filters, filterName

    def updatePreviewImage(self):
        try:
            currentFilters = self.createComposedFunction(True)[0]
            newImage = currentFilters(self.image)
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

    def initializeMainWindow(self):
        """Creates the widgets and the layouts of the MainWindow"""
        # self.centralWidget = QWidget()
        # self.setCentralWidget(self.centralWidget)
        self.setAcceptDrops(True)
        self.leftContainer = QGroupBox()
        self.leftContainerLayout = QGridLayout()
        self.leftContainer.setLayout(self.leftContainerLayout)

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)
        self.searchbar.setClearButtonEnabled(True)

        self.load_btn = QPushButton("Add new Filter")
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
        self.createFilter_btn = QPushButton("Create Filter")
        self.filterNameLineEdit = QLineEdit()
        # self.filterNameLineEdit.textChanged.connect(self.handleApply_btn)

        self.clear_btn.clicked.connect(self.clearListWidget)
        self.createFilter_btn.clicked.connect(self.createComposedFunction)
        self.rightList.itemDoubleClicked.connect(self.openParameterDialogWindow)
        # self.apply_btn.setDisabled(True)

        self.rightContainerLayout.addWidget(self.rightList, 0, 0, 1, 2)
        self.rightContainerLayout.addWidget(self.clear_btn, 2, 0)
        self.rightContainerLayout.addWidget(self.createFilter_btn, 2, 1)
        self.rightContainerLayout.addWidget(self.filterNameLineEdit, 1, 0, 1, 2)

        self.previewContainer = QGroupBox()
        self.previewContainerLayout = QGridLayout()
        self.previewContainer.setLayout(self.previewContainerLayout)
        self.refresh_btn = QPushButton("Refresh")

        self.refresh_btn.clicked.connect(self.updatePreviewImage)
        self.image_ = cv.imread(
            r"C:\git\napari-live-recording\src\napari_live_recording\processing_engine_\testImage.jpg"
        )
        aspectRatio = self.image_.shape[0] / self.image_.shape[1]
        self.image = cv.resize(
            self.image_,
            dsize=(int(280 * aspectRatio), 400),
            interpolation=cv.INTER_CUBIC,
        )

        self.imageView = ImageView()
        self.imageView.ui.histogram.hide()
        self.imageView.ui.roiBtn.hide()
        self.imageView.ui.menuBtn.hide()
        self.imageView.setImage(self.image)
        self.previewContainerLayout.addWidget(self.imageView)
        self.previewContainerLayout.addWidget(self.refresh_btn)

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
