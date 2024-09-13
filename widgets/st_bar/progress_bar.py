from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSpacerItem, QWidget

from base_widgets import CustomProgressBar, LayoutH
from cfg import cnf
from signals import gui_signals_app


class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()

        layout = LayoutH(self)

        self.title = QLabel()
        layout.addWidget(self.title)

        spacer = QSpacerItem(10, 0)
        layout.addItem(spacer)

        self.progress_bar = CustomProgressBar()
        layout.addWidget(self.progress_bar)

        gui_signals_app.progressbar_value.connect(self.progressbar_value)
        gui_signals_app.progressbar_show.connect(self.progressbar_show)
        gui_signals_app.progressbar_hide.connect(self.progressbar_hide)

        self.temp_value = 0
        self.current_value = 0

    def progressbar_value(self, value):
        self.temp_value += value

        if self.temp_value > 1:
            self.current_value += round(self.temp_value)
            self.temp_value = 0

        self.progress_bar.setValue(self.current_value)

    def progressbar_show(self):
        self.current_value = 0
        self.progress_bar.setValue(self.current_value)
        self.show()

    def progressbar_hide(self):
        self.hide()

        