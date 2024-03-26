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

        gui_signals_app.progressbar_value.connect(self.progressbar_value)
        gui_signals_app.progressbar_show.connect(self.progressbar_show)
        gui_signals_app.progressbar_hide.connect(self.progressbar_hide)
        gui_signals_app.progressbar_search_photos.connect(self.search_photos)
        gui_signals_app.progressbar_add_photos.connect(self.add_photos)
        gui_signals_app.progressbar_del_photos.connect(self.del_photos)

        self.temp_value = 0
        self.current_value = 0

    def progressbar_value(self, value):
        self.temp_value += value

        if self.temp_value > 1:
            self.current_value += round(self.temp_value)
            self.temp_value = 0

        self.progress_bar.setValue(self.current_value)

        print(value)
        print(self.current_value)

    def search_photos(self):
        self.title.setText(cnf.lng.searching_photos)

    def add_photos(self):
        self.title.setText(cnf.lng.adding_photos)

    def del_photos(self):
        self.title.setText(cnf.lng.deleting_photos)

    def progressbar_show(self):
        self.current_value = 0
        self.progress_bar.setValue(self.current_value)
        self.show()

    def progressbar_hide(self):
        self.hide()