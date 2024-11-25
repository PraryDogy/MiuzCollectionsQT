from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QTextEdit

from lang import Lang
from utils.utils import Utils

from .context import ContextCustom


class CustomContext(ContextCustom):
    def __init__(self, parent_: QTextEdit, event: QContextMenuEvent):
        super().__init__(event=event)
        self.parent_ = parent_
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
        cur = self.parent_.textCursor()
        text = cur.selectedText().strip()
        Utils.copy_text(text)

    def cut_selection(self):
        cur = self.parent_.textCursor()
        text = cur.selectedText().strip()
        Utils.copy_text(text)
        cur.removeSelectedText()

    def paste_text(self):
        text = Utils.paste_text()
        self.parent_.setPlainText(text)


class CustomTextEdit(QTextEdit):
    def __init__(self):
        """
        custom copy paste context
        """
        super().__init__()

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.context_menu = CustomContext(parent_=self, event=a0)
        self.context_menu.show_menu()