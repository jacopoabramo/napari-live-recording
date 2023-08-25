from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from qtpy.QtCore import Qt, QSize


class LListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(LListView, self).__init__(parent)
        self.model = QtGui.QStandardItemModel(self)
        self.setModel(self.model)
        self.setFlow(QtWidgets.QListView.TopToBottom)
        self.setAcceptDrops(False)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setMovement(QtWidgets.QListView.Snap)


class RListView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(RListView, self).__init__(parent)
        self.model = QtGui.QStandardItemModel(self)
        self.setModel(self.model)
        self.setFlow(QtWidgets.QListView.TopToBottom)
        self.setAcceptDrops(True)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMovement(QtWidgets.QListView.Snap)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        central_widget = QtWidgets.QWidget()
        self.l_view = LListView()
        self.r_view = RListView()
        self.leftContainer = QtWidgets.QGroupBox()
        self.leftContainerLayout = QtWidgets.QVBoxLayout()
        self.leftContainer.setLayout(self.leftContainerLayout)
        self.lineEdit = QtWidgets.QLineEdit()
        self.filter = QtWidgets.QPushButton("filter")
        self.leftContainerLayout.addWidget(self.filter)
        self.leftContainerLayout.addWidget(self.lineEdit)
        self.leftContainerLayout.addWidget(self.l_view)
        self.setCentralWidget(central_widget)
        lay = QtWidgets.QHBoxLayout(central_widget)
        lay.addWidget(self.leftContainer)
        lay.addWidget(self.r_view)
        self.loadItems()

    def loadItems(self):
        widget_names = [
            "Gauss",
            "Gauss 2",
            "Gauss 3",
            "Canny Edge",
            "Hough Lines",
            "Gauss",
            "Gauss 2",
            "Gauss 3",
            "Canny Edge",
            "Hough Lines",
        ]
        for name in widget_names:
            item = QtGui.QStandardItem()
            item.setText(name)
            self.l_view.model.appendRow(item)


if __name__ == "__main__":
    # don't auto scale when drag app to a different monitor.
    # QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QtWidgets.QApplication(sys.argv)
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
