from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QSpacerItem, QWidget

from base_widgets import InputBase, LayoutH
from cfg import cnf
from signals import signals_app


class SearchBarBase(InputBase):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)
        self.setFixedHeight(25)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(cnf.lng.search)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.delayed_search)

        signals_app.clear_search.connect(self.clear_search)
        signals_app.set_focus_search.connect(self.setFocus)
        signals_app.reload_search_wid.connect(self.reload_search)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)

    def create_search(self, new_text):
        if len(new_text) > 0:
            cnf.search_widget_text = new_text
        else:
            cnf.search_widget_text = None

        self.timer.stop()
        self.timer.start()

    def delayed_search(self):
        signals_app.reload_thumbnails.emit()

    def clear_search(self):
        self.clear()
        cnf.search_widget_text = None

    def reload_search(self):
        self.setPlaceholderText(cnf.lng.search)


class WidSearch(QWidget):
    def __init__(self):
        super().__init__()

        h_layout = LayoutH()
        self.setLayout(h_layout)

        search = SearchBarBase()
        h_layout.addWidget(search)
        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.setFixedWidth(search.width() + 5)