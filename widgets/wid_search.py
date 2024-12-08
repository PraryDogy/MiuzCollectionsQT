from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QSpacerItem, QWidget

from base_widgets import LayoutHor
from base_widgets.input import ULineEdit
from cfg import Dynamic
from lang import Lang
from signals import SignalsApp


class SearchBarBase(ULineEdit):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(Lang.search)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.delayed_search)

        SignalsApp.all_.wid_search_cmd.connect(self.wid_search_cmd)

    def wid_search_cmd(self, flag: str):
        if flag == "focus":
            self.setFocus()
        elif flag == "clear":
            self.clear_search()
        else:
            raise Exception("widgets > wid search > wrong flag", flag)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)

    def create_search(self, new_text):
        if len(new_text) > 0:
            Dynamic.search_widget_text = new_text
        else:
            Dynamic.search_widget_text = None

        self.timer.stop()
        self.timer.start()

    def delayed_search(self):
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")

    def clear_search(self):
        self.clear()
        Dynamic.search_widget_text = None


class WidSearch(QWidget):
    def __init__(self):
        super().__init__()

        h_layout = LayoutHor()
        self.setLayout(h_layout)

        search = SearchBarBase()
        h_layout.addWidget(search)
        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.setFixedWidth(search.width() + 5)