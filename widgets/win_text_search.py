import re

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static
from system.lang import Lng

from ._base_widgets import (ActiveButton, GrayTextLabel, TitleTextLabel,
                            TransparentFrame, TransparentWidget, UGroupBox,
                            UMainWidget, UPushButton, USep, UTextEdit)


class WinTextSearchTitleRow(TransparentFrame):
    svg_path = Static.COMMON_ICONS / "text_edit.svg"
    svg_size = (25, 25)

    def __init__(self):
        super().__init__()
        self.h_lay = QHBoxLayout(self)
        self.h_lay.setContentsMargins(0, 0, 0, 0)
        self.h_lay.setSpacing(10)
        self.h_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(str(self.svg_path))
        self.svg_widget.setFixedSize(*self.svg_size)
        self.h_lay.addWidget(self.svg_widget)

        self.title_label = TitleTextLabel(Lng.text_editor[JsonData.lng_index])
        self.h_lay.addWidget(self.title_label)


class WinTextSearch(UMainWidget):
    ok_clicked = pyqtSignal(str)
    size_ = (380, 330)  # Немного увеличил высоту, чтобы поместилось описание
    svg_magnifier = Static.COMMON_ICONS / "magnifier.svg"
    svg_wand = Static.COMMON_ICONS / "wand.svg"
    icon_size = QSize(10, 10)

    def __init__(self, text: str):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedSize(*self.size_)
        # self.insert_sep()

        self.magnifier_icon = QIcon(str(self.svg_magnifier))
        self.wand_icon = QIcon(str(self.svg_wand))

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 0, 10, 10)

        group_container = UGroupBox()
        self.central_layout.addWidget(group_container)
        group_layout = QVBoxLayout(group_container)
        group_layout.setContentsMargins(5, 5, 5, 5)
        group_layout.setSpacing(7)

        self.title_row = WinTextSearchTitleRow()
        group_layout.addWidget(self.title_row)

        group_layout.addWidget(USep())

        # 1. Текст описания форматов (RU / EN)
        self.description_label = GrayTextLabel(Lng.text_search_descr[JsonData.lng_index])
        self.description_label.setWordWrap(True) 
        group_layout.addWidget(self.description_label)

        self.text_edit = UTextEdit()
        self.central_layout.addWidget(self.text_edit)
        self.text_edit.setPlainText(text)
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

        self.btns_container = TransparentWidget()
        self.central_layout.addWidget(self.btns_container)

        btns_layout = QHBoxLayout(self.btns_container)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(10)

        btns_layout.addStretch(1)

        self.format_button = UPushButton(Lng.enhance_text[JsonData.lng_index])
        self.format_button.clicked.connect(self.format_input_text)
        self.format_button.setIconSize(self.icon_size)
        self.format_button.setIcon(self.wand_icon)
        self.title_row.h_lay.addStretch()
        self.title_row.h_lay.addWidget(self.format_button)
        # btns_layout.addWidget(self.format_button)

        close_btn = UPushButton(Lng.close[JsonData.lng_index])
        close_btn.clicked.connect(self.deleteLater)
        btns_layout.addWidget(close_btn)

        self.ok_btn = ActiveButton(Lng.search[JsonData.lng_index])
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
