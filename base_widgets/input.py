from PyQt5.QtWidgets import QAction, QLineEdit

from cfg import cnf
from styles import Names, default_theme
from utils import MainUtils

from .context import ContextMenuBase


class CustomContext(ContextMenuBase):
    def __init__(self, parent: QLineEdit, event):
        super().__init__(event=event)
        self.root = parent
        self.setFixedWidth(120)

        sel = QAction(cnf.lng.cut, self)
        sel.triggered.connect(self.cut_selection)
        self.addAction(sel)

        sel_all = QAction(cnf.lng.copy, self)
        sel_all.triggered.connect(self.copy_selection)
        self.addAction(sel_all)

        sel_all = QAction(cnf.lng.paste, self)
        sel_all.triggered.connect(self.paste_text)
        self.addAction(sel_all)

        self.show_menu()

    def copy_selection(self):
        text = self.root.selectedText()
        MainUtils.copy_text(text)

    def cut_selection(self):
        text = self.root.selectedText()
        MainUtils.copy_text(text)
        self.root.clear()

    def paste_text(self):
        text = MainUtils.paste_text()
        self.root.insert(text)


class InputBase(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(28)
        self.setObjectName(Names.base_input)
        self.setStyleSheet(default_theme)

    def contextMenuEvent(self, event):
        CustomContext(parent=self, event=event)
