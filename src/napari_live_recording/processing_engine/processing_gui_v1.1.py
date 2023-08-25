import sys
import os
import glob
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
    QListView,
    QAbstractItemView,
    QHBoxLayout,
    QVBoxLayout,
)
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QStandardItemModel, QIcon, QStandardItem, QKeyEvent


class ListView_Left(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFlow(QListView.TopToBottom)
        self.m_model = QStandardItemModel(self)
        self.setModel(self.m_model)
        self.setAcceptDrops(True)
        self.setIconSize(QSize(50, 150))
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setDropIndicatorShown(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setViewMode(QListView.ViewMode.IconMode)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.parent.listViewRight.model().removeRow(
            self.parent.listViewRight.currentIndex().row()
        )


class ListView_Right(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setFlow(QListView.TopToBottom)
        self.m_model = QStandardItemModel(self)
        self.setModel(self.m_model)
        self.setAcceptDrops(True)
        self.setIconSize(QSize(150, 150))
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QKeyEvent.Type.KeyPress and event.key() == Qt.Key.Key_Delete:
            if source == self:
                row_indx = self.currentIndex().row()
                self.model().remove().removeRow(row_indx)
        return super().eventFilter(source, event)

    # def dropEvent(self, event):
    #     super().dropEvent(event)
    #     self.parent.listViewLeft.model().removeRow(
    #         self.parent.listViewLeft.currentIndex().row()
    #     )


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.window_width, self.window_height = 1400, 500
        self.resize(self.window_width, self.window_height)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.listViewLeft = ListView_Left(self)
        layout.addWidget(self.listViewLeft)

        self.listViewRight = ListView_Right(self)
        layout.addWidget(self.listViewRight)

        self.loadItems()

    def loadIcons(self):
        icon_folder = os.path.join(os.getcwd(), "icons")
        for icon in glob.glob(os.path.join(icon_folder, "*.ico")):
            item = QStandardItem()
            item.setIcon(QIcon(icon))
            self.listViewLeft.m_model.appendRow(item)

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
            item = QStandardItem()
            item.setText(name)
            self.listViewLeft.m_model.appendRow(item)


if __name__ == "__main__":
    # don't auto scale when drag app to a different monitor.
    # QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget {
            font-size: 17px;
        }
    """
    )

    myApp = MyApp()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing Window...")
