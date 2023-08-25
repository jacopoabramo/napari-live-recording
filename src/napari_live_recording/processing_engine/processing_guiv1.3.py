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
import matplotlib.pyplot as plt
from ast import literal_eval

from pims_testing import image
from image_filters import *
import functools
import image_filters
import importlib
import pkgutil
from qtpy.QtCore import Qt, QMimeData, Signal, QRect, QFileInfo, QUrl
from qtpy.QtGui import QDrag, QPixmap
from os.path import dirname, basename, isfile, join
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
    def __init__(self, parent=None):
        super(LeftList, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSortingEnabled(True)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSelectionRectVisible(True)
        self.setAcceptDrops(False)


class RightList(QListWidget):
    def __init__(self, parent=None):
        super(RightList, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionRectVisible(True)
        self.setSortingEnabled(True)


class ParameterDialog(QDialog):
    def __init__(self, parameters, parent=None):
        super(ParameterDialog, self).__init__(parent)

        self.setWindowTitle("Change Parameters")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.parameters = parameters
        print(self.parameters)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.parameterDialogLayout = QFormLayout()
        self.setLayout(self.parameterDialogLayout)
        self.lineEdits = {}
        for parameter, value in self.parameters.items():
            lineEdit = QLineEdit(f"{value}")
            self.lineEdits[parameter] = lineEdit
            self.parameterDialogLayout.addRow(parameter, self.lineEdits[parameter])
        self.parameterDialogLayout.addWidget(self.buttonBox)

    def getValues(self):
        for linedit in self.lineEdits.keys():
            self.lineEdits[linedit] = literal_eval(self.lineEdits[linedit].text())
        return self.lineEdits


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # funktioniert nur für module die über programm reingeladen wurden

        self.filters_folder = r"C:\Users\felix\PycharmProjects\Testing\image_filters"
        self.widget_names = [
            "Gauss",
            "Gauss 2",
            "Gauss 3",
            "Canny Edge",
            "Hough Lines",
        ]
        self.initializeMainWindow()

        self.loadFiles()

    def dragEnterEvent(self, e):
        e.accept()

    def openParameterDialogWindow(self, item: QListWidgetItem):
        dialog = ParameterDialog(item.data(Qt.UserRole)[1])
        answer = dialog.exec_()
        if answer:
            # print(self.filtersDict)
            data = item.data(Qt.UserRole)
            print(data)
            values = dialog.getValues()
            data[1] = values
            item.setData(Qt.UserRole, data)
            data = item.data(Qt.UserRole)
            print("DAta after", data)
            # print(values)
            self.filtersDict[item.text()][1] = values

            print(self.filtersDict)
        dialog.show()

    def dropEvent(self, e):
        e.accept()

    def loadFiles(self):
        self.leftList.clear()
        moduleList = []
        for importer, modname, ispkg in pkgutil.iter_modules(image_filters.__path__):
            moduleList.append("image_filters." + modname)

        self.filtersDict = {}
        for module in map(importlib.import_module, moduleList):
            print("Module", module)
            for func in filter(callable, module.__dict__.values()):
                print(func)
                print(module.dc)
                tpl = [func, module.dc]
                self.filtersDict[func.__name__] = tpl
                item = QListWidgetItem()
                item.setText(func.__name__)
                item.setToolTip(module.__file__)
                item.setData(Qt.UserRole, tpl)
                self.leftList.addItem(item)

        print(self.filtersDict)

        # modules = glob.glob(join(self.filters_folder, "*.py"))
        # for f in modules:
        #     if isfile(f) and not f.endswith("__init__.py"):
        #         file = basename(f)[:-3]
        #         item = QListWidgetItem()
        #         item.setText(file)
        #         item.setData(Qt.UserRole, f)
        #         item.setToolTip(f)

    def clearListWidget(self):
        self.rightList.clear()

    def applyFilters(self):
        filters = {}
        for i in range(self.rightList.count()):
            item = self.rightList.item(i)
            filters[item.text()] = item.data(Qt.UserRole)
        print(filters)
        for filter in filters.values():
            image2 = filter[0](image, **filter[1])

            fig, axs = plt.subplots(1, 2)

            axs[0].imshow(image, cmap="gray")

            axs[1].imshow(image2, cmap="gray")

            plt.show()
        return filters

    def update_display(self, text):
        for i in range(self.leftList.count()):
            item = self.leftList.item(i)
            item.setHidden(True)
        items = self.leftList.findItems(text, Qt.MatchContains)
        for item in items:
            item.setHidden(False)

    def addFiles(self):
        filepaths, _ = QFileDialog.getOpenFileNames(
            self, caption="Load files", filter="Python Files (*.py)"
        )
        for filepath in filepaths:
            if filepath != "":
                shutil.copy(filepath, self.filters_folder)
        self.loadFiles()

    def initializeMainWindow(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setAcceptDrops(True)
        self.leftContainer = QGroupBox()
        self.leftContainerLayout = QGridLayout()
        self.leftContainer.setLayout(self.leftContainerLayout)

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)
        self.searchbar.setClearButtonEnabled(True)

        # self.completer = QCompleter(self.widget_names)
        # self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        # self.searchbar.setCompleter(self.completer)

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
