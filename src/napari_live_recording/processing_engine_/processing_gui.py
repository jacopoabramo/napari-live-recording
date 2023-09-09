from qtpy.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QWidget,
    QDialog,
    QLabel,
    QMainWindow,
    QVBoxLayout,
)
import numpy as np
import matplotlib.pyplot as plt
from ast import literal_eval
import pims, math
from pims_testing import image
from image_filters import *
import functools
import image_filters
import importlib
import pkgutil
from qtpy.QtCore import Qt
import shutil
import sys, os, glob
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
    QAbstractItemView,
)


class LeftList(QListWidget):
    """Left list widget with functions available for image processing."""

    def __init__(self, parent=None):
        super(LeftList, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSortingEnabled(True)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSelectionRectVisible(True)
        self.setAcceptDrops(False)


class RightList(QListWidget):
    """Right list widget with functions to be used for image processing. Individual items are sortable, to delete individual items, the items can simply be dragged into the left list. It is possible to have the same function multiple times"""

    def __init__(self, parent=None):
        super(RightList, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionRectVisible(True)
        self.setSortingEnabled(True)


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


class MainWindow(QMainWindow):
    """Main Window containing two lists, one Right List and one Left List. Drag items from the left to the right list to add them to the processing pipeline. The left listed can be searched for items. New items can be loaded from files.The right list can be cleared. By applying the right list, the functions (associated eith the items in the right list) will be put in to a processing pipeline."""

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.filters_folder = r"C:\Users\felix\PycharmProjects\Testing\image_filters"

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
                moduleList.append("image_filters." + modname)
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

    def applyFilters(self):
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
        image_now = image

        for filter in filters.values():
            print(filter)
            functionList.append(
                pims.pipeline(functools.partial(filter[0], **filter[1]))
            )
            print(filter[0], filter[1])
            print("CurrentFilter", filter[0])
            image_now = filter[0](image_now, **filter[1])
        self.showImage(image_now)
        print("Final filters", filters)
        print("FunctionList", functionList)
        composedFunction = composeFunctions(list(reversed(functionList)))

        image_composed = composedFunction(image)
        self.showImage(image_composed)

        return composedFunction

    def applyFunction(self, function, input):
        return function(input)

    def showImage(self, image2):
        fig, axs = plt.subplots(1, 2)

        axs[0].imshow(image, cmap="gray")

        axs[1].imshow(image2, cmap="gray")

        plt.show()

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
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setAcceptDrops(True)
        self.leftContainer = QGroupBox()
        self.leftContainerLayout = QGridLayout()
        self.leftContainer.setLayout(self.leftContainerLayout)

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)
        self.searchbar.setClearButtonEnabled(True)

        self.load_btn = QPushButton("Add new Filter")
        self.load_btn.clicked.connect(self.addFiles)
        self.le = QLabel("Hello")
        self.leftList = LeftList()

        self.leftContainerLayout.addWidget(self.searchbar, 0, 0, 1, 2)
        self.leftContainerLayout.addWidget(self.leftList, 1, 0, 1, 2)
        self.leftContainerLayout.addWidget(self.load_btn, 2, 0, 1, 2)

        self.rightContainer = QGroupBox()
        self.rightContainerLayout = QGridLayout()
        self.rightContainer.setLayout(self.rightContainerLayout)

        self.rightList = RightList()
        self.clear_btn = QPushButton("Clear")
        self.apply_btn = QPushButton("Apply")
        self.clear_btn.clicked.connect(self.clearListWidget)
        self.apply_btn.clicked.connect(self.applyFilters)
        self.rightList.itemDoubleClicked.connect(self.openParameterDialogWindow)

        self.rightContainerLayout.addWidget(self.rightList, 0, 0, 1, 2)
        self.rightContainerLayout.addWidget(self.clear_btn, 1, 0)
        self.rightContainerLayout.addWidget(self.apply_btn, 1, 1)
        layout = QHBoxLayout(self.centralWidget)

        layout.addWidget(self.leftContainer)
        layout.addWidget(self.rightContainer)


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

    myApp = MainWindow()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
