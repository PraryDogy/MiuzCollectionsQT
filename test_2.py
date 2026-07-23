import sys

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
                             QMenu, QVBoxLayout, QWidget)

from widgets._base_widgets import RowArrowWidget, UMainWidget, UPushButton
from PyQt6.QtCore import Qt

class Lng:
    app_lang = (
        "Язык приложения",
        "Application language"
    )
    lang = (
        "Язык",
        "Language"
    )
    rus = (
        "Русский",
        "Russian"
    )
    eng = (
        "Английский",
        "English"
    )


class FirstLoadWin(UMainWidget):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lng_index = 0

        self.init_ui()

    def remove_ui(self):
        for i in self.findChildren(QWidget):
            i.deleteLater()

    def init_ui(self):
        self.init_lang_widget()
        # self.central_layout.addStretch()

    def lng_action(self, value: int):
        self.lng_index = value
        self.remove_ui()
        self.init_ui()

        print(self.lng_index)

    def init_lang_widget(self):
        lng_label_text = f"{Lng.app_lang[0]} ({Lng.app_lang[1]})"
        rus_text = f"{Lng.rus[0]} ({Lng.rus[1]})"
        eng_text = f"{Lng.eng[0]} ({Lng.eng[1]})"
        lng_btn_text = f"{Lng.lang[0]} ({Lng.lang[1]})"

        lng_containter = QGroupBox()
        self.central_layout.addWidget(lng_containter)
        lng_layout = QHBoxLayout(lng_containter)
        lng_layout.setContentsMargins(2, 5, 2, 5)
        lng_layout.setSpacing(0)

        lng_label = QLabel(lng_label_text)
        lng_layout.addWidget(lng_label)
        lng_layout.addStretch()

        lng_btn = UPushButton(lng_btn_text)
        lng_btn.setFixedWidth(125)
        lng_layout.addWidget(lng_btn)

        lng_menu = QMenu(lng_btn)
        lng_btn.setMenu(lng_menu)

        rus_action = QAction(rus_text, lng_menu)
        rus_action.triggered.connect(lambda: self.lng_action(0))
        lng_menu.addAction(rus_action)

        eng_action = QAction(eng_text, lng_menu)
        eng_action.triggered.connect(lambda: self.lng_action(1))
        lng_menu.addAction(eng_action)


app = QApplication(sys.argv)
win = FirstLoadWin()
win.show()
app.exec()