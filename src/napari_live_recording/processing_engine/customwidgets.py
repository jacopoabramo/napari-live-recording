from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout


class OnOffWidget(QWidget):
    def __init__(self, name):
        super(OnOffWidget, self).__init__()

        self.name = name
        self.is_on = False

        self.lbl = QLabel(self.name)
        self.btn_on = QPushButton("On")
        self.btn_off = QPushButton("Off")

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.lbl)
        self.hbox.addWidget(self.btn_on)
        self.hbox.addWidget(self.btn_off)

        self.btn_on.clicked.connect(self.on)
        self.btn_off.clicked.connect(self.off)

        self.setLayout(self.hbox)

        self.update_button_state()

    def show(self):
        """
        Show this widget, and all child widgets.
        """
        for w in [self, self.lbl, self.btn_on, self.btn_off]:
            w.setVisible(True)

    def hide(self):
        """
        Hide this widget, and all child widgets.
        """
        for w in [self, self.lbl, self.btn_on, self.btn_off]:
            w.setVisible(False)

    def off(self):
        self.is_on = False
        self.update_button_state()

    def on(self):
        self.is_on = True
        self.update_button_state()

    def update_button_state(self):
        """
        Update the appearance of the control buttons (On/Off)
        depending on the current state.
        """
        if self.is_on == True:
            self.btn_on.setStyleSheet("background-color: #4CAF50; color: #fff;")
            self.btn_off.setStyleSheet("background-color: none; color: none;")
        else:
            self.btn_on.setStyleSheet("background-color: none; color: none;")
            self.btn_off.setStyleSheet("background-color: #D32F2F; color: #fff;")
