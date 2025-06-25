from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QLineEdit

from lang import Lang
from system.utils import MainUtils

from .context import ContextCustom

INPUT_H = 28
LEFT_PADDING = 2
RIGHT_PADDING = 28


class ULineEdit(QLineEdit):
    def __init__(self):
        f"""
        custom context menu
        height 28
        padding left 2
        padding right 28
        """
        super().__init__()
        self.setFixedHeight(INPUT_H)
        self.setStyleSheet(
            f"""
            padding-left: {LEFT_PADDING};
            padding-right: {RIGHT_PADDING};
            """
        )

    def cut_selection(self, *args):
        text = self.selectedText()
        MainUtils.copy_text(text)

        new_text = self.text().replace(text, "")
        self.setText(new_text)

    def paste_text(self, *args):
        text = MainUtils.paste_text()
        self.insert(text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.menu_ = ContextCustom(event=a0)
        self.menu_.setFixedWidth(120)

        sel = QAction(text=Lang.cut, parent=self.menu_)
        sel.triggered.connect(self.cut_selection)
        self.menu_.addAction(sel)

        sel_all = QAction(text=Lang.copy, parent=self.menu_)
        sel_all.triggered.connect(
            lambda: MainUtils.copy_text(self.selectedText())
        )
        self.menu_.addAction(sel_all)

        sel_all = QAction(text=Lang.paste, parent=self.menu_)
        sel_all.triggered.connect(self.paste_text)
        self.menu_.addAction(sel_all)

        self.menu_.show_menu()