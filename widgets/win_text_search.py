import re

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QIcon
from cfg import JsonData, Static
from system.lang import Lng

from ._base_widgets import (TransparentLabel, TransparentWidget, UMainWidget,
                            UPushButton, UTextEditLight, TransparentFrame, UTextEditDark)


class WinTextSearchTitle(TransparentLabel):
    def __init__(self):
        super().__init__("Поиск")


class WinTextSearchTitleRow(TransparentFrame):
    svg_path = Static.COMMON_ICONS / "magnifier.svg"
    svg_size = (28, 28)

    def __init__(self):
        super().__init__()
        self.h_lay = QHBoxLayout(self)
        self.h_lay.setContentsMargins(0, 0, 0, 0)
        self.h_lay.setSpacing(10)
        self.h_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(str(self.svg_path))
        self.svg_widget.setFixedSize(*self.svg_size)
        # self.h_lay.addWidget(self.svg_widget)

        self.title_label = WinTextSearchTitle()
        self.h_lay.addWidget(self.title_label)


class WinTextSearchBtn(UPushButton):
    size_ = (90, 23)

    def __init__(self, text):
        super().__init__(text)
        self.setFixedSize(*self.size_)


class WinTextSearch(UMainWidget):
    ok_clicked = pyqtSignal(str)
    size_ = (350, 330)  # Немного увеличил высоту, чтобы поместилось описание
    svg_magnifier = Static.COMMON_ICONS / "magnifier.svg"
    svg_wand = Static.COMMON_ICONS / "wand.svg"
    icon_size = QSize(10, 10)

    def __init__(self, text: str):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedSize(*self.size_)

        self.magnifier_icon = QIcon(str(self.svg_magnifier))
        self.wand_icon = QIcon(str(self.svg_wand))

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 5, 10, 10)

        self.title_row = WinTextSearchTitleRow()
        self.central_layout.addWidget(self.title_row)

        # 1. Текст описания форматов (RU / EN)
        if JsonData.lng_index == 0:
            description_text = (
                "Для поиска нескольких слов введите их через запятую или с новой строки."
            )
        else:
            description_text = (
                "Для поиска нескольких слов введите их через запятую или с новой строки."
            )
        self.description_label = TransparentLabel(description_text)
        self.description_label.setWordWrap(True) 
        self.central_layout.addWidget(self.description_label)

        self.text_edit = UTextEditDark()
        self.central_layout.addWidget(self.text_edit)
        self.text_edit.setPlainText(text)

        self.btns_container = TransparentWidget()
        self.central_layout.addWidget(self.btns_container)

        btns_layout = QHBoxLayout(self.btns_container)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(10)

        btns_layout.addStretch(1)

        self.format_button = WinTextSearchBtn(
            "Улучшить" if JsonData.lng_index == 0 else "Улучшить"
        )
        self.format_button.clicked.connect(self.format_input_text)
        self.format_button.setIconSize(self.icon_size)
        self.format_button.setIcon(self.wand_icon)
        btns_layout.addWidget(self.format_button)

        self.ok_btn = WinTextSearchBtn("Поиск")
        self.ok_btn.setIcon(self.magnifier_icon)
        self.ok_btn.setIconSize(self.icon_size)
        self.ok_btn.clicked.connect(self.search)
        btns_layout.addWidget(self.ok_btn)

    def format_input_text(self):
        text = self.text_edit.toPlainText()
        words = re.split(r"[,\n]+", text)
        words = [word.strip() for word in words if word.strip()]
        words = list(dict.fromkeys(words))
        self.text_edit.setPlainText(", ".join(words))

    def search(self):
        self.format_input_text()
        self.ok_clicked.emit(self.text_edit.toPlainText())
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
