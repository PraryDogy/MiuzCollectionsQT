from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QLineEdit

from lang import Lang
from utils.utils import Utils

from .context import ContextCustom


class CustomContext(ContextCustom):
    def __init__(self, parent: QLineEdit, event):
        super().__init__(event=event)
        self.my_parent = parent
        self.setFixedWidth(120)

        sel = QAction(text=Lang.cut, parent=self)
        sel.triggered.connect(self.cut_selection)
        self.addAction(sel)

        sel_all = QAction(text=Lang.copy, parent=self)
        sel_all.triggered.connect(self.copy_selection)
        self.addAction(sel_all)

        sel_all = QAction(text=Lang.paste, parent=self)
        sel_all.triggered.connect(self.paste_text)
        self.addAction(sel_all)

    def copy_selection(self):
        text = self.my_parent.selectedText()
        Utils.copy_text(text)

    def cut_selection(self):
        text = self.my_parent.selectedText()
        Utils.copy_text(text)
        self.my_parent.clear()

    def paste_text(self):
        text = Utils.paste_text()
        self.my_parent.insert(text)


class CustomInput(QLineEdit):
    def __init__(self):
        """
        custom copy paste context menu

        height 28

        padding left right 2px
        """
        super().__init__()
        self.setFixedHeight(28)
        self.setStyleSheet("padding-left: 2px; padding-right: 2px;")

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.context_menu = CustomContext(parent=self, event=a0)
        self.context_menu.show_menu()
