from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QLineEdit

from cfg import cnf
from styles import Names, Themes
from utils.main_utils import MainUtils

from .context import ContextMenuBase


class CustomContext(ContextMenuBase):
    def __init__(self, parent: QLineEdit, event):
        super().__init__(event=event)
        self.my_parent = parent
        self.setFixedWidth(120)

        sel = QAction(text=cnf.lng.cut, parent=self)
        sel.triggered.connect(self.cut_selection)
        self.addAction(sel)

        sel_all = QAction(text=cnf.lng.copy, parent=self)
        sel_all.triggered.connect(self.copy_selection)
        self.addAction(sel_all)

        sel_all = QAction(text=cnf.lng.paste, parent=self)
        sel_all.triggered.connect(self.paste_text)
        self.addAction(sel_all)

    def copy_selection(self):
        text = self.my_parent.selectedText()
        MainUtils.copy_text(text)

    def cut_selection(self):
        text = self.my_parent.selectedText()
        MainUtils.copy_text(text)
        self.my_parent.clear()

    def paste_text(self):
        text = MainUtils.paste_text()
        self.my_parent.insert(text)


class InputBase(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(28)
        self.setObjectName(Names.base_input)
        self.setStyleSheet(Themes.current)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.context_menu = CustomContext(parent=self, event=a0)
        self.context_menu.show_menu()
        return
        return super().contextMenuEvent(a0)
