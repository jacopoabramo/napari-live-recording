from qtpy.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QWidget,
    QLabel,
    QMainWindow,
    QVBoxLayout,
)
from qtpy.QtCore import Qt, QMimeData, Signal, QRect
from qtpy.QtGui import QDrag, QPixmap


import sys
from qtpy.QtWidgets import (
    QWidget,
    QComboBox,
    QLineEdit,
    QLabel,
    QFormLayout,
    QPushButton,
    QScrollArea,
    QMainWindow,
    QApplication,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QCompleter,
    QListWidget,
)
from qtpy.QtCore import Qt


class DragItem(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(25, 5, 25, 5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid black;")
        # self.setGeometry(QRect(70, 80, 1000, 1))
        # Store data separately from display label, but use label for default.
        self.data = self.text()
        self.name = self.text()

    def set_data(self, data):
        self.data = data

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)


class DragWidget(QWidget):
    """
    Generic list sorting handler.
    """

    orderChanged = Signal(list)

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()
        if self.blayout.count() == 0:
            self.blayout.addWidget(widget)
        else:
            for n in range(self.blayout.count()):
                # Get the widget at each index in turn.
                w = self.blayout.itemAt(n).widget()
                if self.orientation == Qt.Orientation.Vertical:
                    # Drag drop vertically.
                    drop_here = pos.y() < w.y() + w.size().height() // 2
                else:
                    # Drag drop horizontally.
                    drop_here = pos.x() < w.x() + w.size().width() // 2

                if drop_here:
                    # We didn't drag past this widget.
                    # insert to the left of it.
                    self.blayout.insertWidget(n - 1, widget)
                    # self.orderChanged.emit(self.get_item_data())
                    break
                else:
                    self.remove_item(widget)

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def remove_item(self, item):
        self.blayout.removeWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data


class ScrollWidget(QWidget):
    """
    List Widget containing Functions to choose from
    """

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.mainWidget = QGroupBox()  # Controls container widget.
        self.layout = QVBoxLayout()  # Controls container layout.

        # List of names, widgets are stored in a dictionary by these keys.
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
        self.widgets = []

        # Iterate the names, creating a new OnOffWidget for
        # each one, adding it to the layout and
        # and storing a reference in the self.widgets dict
        for name in widget_names:
            item = DragItem(name)
            item.setText(name)
            self.layout.addWidget(item)
            self.widgets.append(item)

        self.mainWidget.setLayout(self.layout)

        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.mainWidget)

        # Search bar.
        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)

        # Adding Completer.
        self.completer = QCompleter(widget_names)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.searchbar.setCompleter(self.completer)

        # Add the items to VBoxLayout (applied to container widget)
        # which encompasses the whole window.
        container = QWidget()
        containerLayout = QVBoxLayout()
        containerLayout.addWidget(self.searchbar)
        # containerLayout.addWidget(self.scroll)

        container.setLayout(containerLayout)

    def update_display(self, text):
        for widget in self.widgets:
            if text.lower() in widget.name.lower():
                widget.show()
            else:
                widget.hide()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processDragWidget = DragWidget(orientation=Qt.Orientation.Vertical)
        self.processingContainer = QGroupBox("Processing Procedure")
        self.processingContainerLayout = QVBoxLayout()
        self.applyPushButton = QPushButton("Apply!")
        self.processingContainer.setLayout(self.processingContainerLayout)
        self.processingContainerLayout.addWidget(self.processDragWidget)
        self.processingContainerLayout.addWidget(self.applyPushButton)
        self.scrollContainer = QGroupBox("Available Filters")
        self.scrollContainerLayout = QVBoxLayout()
        self.scrollContainer.setLayout(self.scrollContainerLayout)
        self.scrollContentWidget = (
            QListWidget()
        )  # DragWidget(orientation=Qt.Orientation.Vertical)
        self.scrollContentWidgetLayout = QVBoxLayout()
        self.scrollContentWidget.setLayout(self.scrollContentWidgetLayout)

        # List of names, widgets are stored in a dictionary by these keys.
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
        self.widgets = {}

        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scrollContentWidget)

        # Iterate the names, creating a new OnOffWidget for
        # each one, adding it to the layout and
        # and storing a reference in the self.widgets dict
        for name in widget_names:
            item = DragItem(name)
            item.setText(name)
            self.scrollContentWidgetLayout.addWidget(item)
            # self.scrollContentWidget.add(item)
            self.widgets[name] = item

        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display)

        # Adding Completer.
        self.completer = QCompleter(widget_names)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.searchbar.setCompleter(self.completer)

        # self.scrollWidget = ScrollWidget()

        # Print out the changed order.

        container = QWidget()
        layout = QHBoxLayout()
        self.scrollContainerLayout.addWidget(self.searchbar)
        self.scrollContainerLayout.addWidget(self.scroll)
        # layout.addWidget(self.dragWidget)

        container.setLayout(layout)
        layout.addWidget(self.scrollContainer)
        layout.addWidget(self.processingContainer)
        self.setCentralWidget(container)

    def update_display(self, text):
        for widget in self.widgets.values():
            if text.lower() in widget.name.lower():
                widget.show()
            else:
                widget.hide()


app = QApplication([])
w = MainWindow()
w.show()

app.exec_()
