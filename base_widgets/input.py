from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QLineEdit

from lang import Lang
from utils.utils import Utils

from .context import ContextCustom


class CustomContext(ContextCustom):
    def __init__(self, parent: QLineEdit, event):
        ...




class ULineEdit(QLineEdit):
    def __init__(self):
        """
        custom copy paste context menu, height 28
        padding left 2, padding right 2px
        close btn onTextChanged
        """
        super().__init__()
        self.setFixedHeight(28)
        self.setStyleSheet("padding-left: 2px; padding-right: 2px;")

    def cut_selection(self, *args):
        text = self.selectedText()
        Utils.copy_text(text)

        new_text = self.text().replace(text, "")
        self.setText(new_text)

    def paste_text(self, *args):
        text = Utils.paste_text()
        self.insert(text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.menu_ = ContextCustom(event=a0)
        self.setFixedWidth(120)

        sel = QAction(text=Lang.cut, parent=self.menu_)
        sel.triggered.connect(self.cut_selection)
        self.menu_.addAction(sel)

        sel_all = QAction(text=Lang.copy, parent=self.menu_)
        sel_all.triggered.connect(
            lambda: Utils.copy_text(self.selectedText())
        )
        self.menu_.addAction(sel_all)

        sel_all = QAction(text=Lang.paste, parent=self.menu_)
        sel_all.triggered.connect(self.paste_text)
        self.menu_.addAction(sel_all)

        self.menu_.show_menu()