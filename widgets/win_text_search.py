from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from ._base_widgets import TransparentLabel, UMainWidget, UTextEditLight, UPushButton


class WinTextSearch(UMainWidget):
    ok_clicked = pyqtSignal(str)
    size_ = (300, 300)

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedSize(*self.size_)

        self.description_label = TransparentLabel("")
        self.central_layout.addWidget(self.description_label)

        text = (
            ""
        )


        self.text_edit = UTextEditLight()
        self.central_layout.addWidget(self.text_edit)

        self.format_button = UPushButton("Форматировать текст")
        self.central_layout