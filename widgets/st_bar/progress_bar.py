from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QProgressBar, QSpacerItem, QWidget

from cfg import cnf
from signals import gui_signals_app

from base_widgets import LayoutH


class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()

        layout = LayoutH(self)

        self.title = QLabel()
        layout.addWidget(self.title)

        spacer = QSpacerItem(10, 0)
        layout.addItem(spacer)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        gui_signals_app.scan_progress_value.connect(self.progress_bar_set)
        gui_signals_app.progress_search_photos.connect(self.search_photos)
        gui_signals_app.progress_add_photos.connect(self.add_photos)
        gui_signals_app.progress_del_photos.connect(self.del_photos)

    def progress_bar_set(self, value):
        if self.isHidden():
            if value != 0 or value != 100:
                self.show()

        elif value == 0 or value == 100:
            self.hide()

        else:
            self.progress_bar.setValue(value)

    def search_photos(self):
        self.title.setText(cnf.lng.searching_photos)

    def add_photos(self):
        self.title.setText(cnf.lng.adding_photos)

    def del_photos(self):
        self.title.setText(cnf.lng.deleting_photos)