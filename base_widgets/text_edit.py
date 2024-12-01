from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QTextEdit

from lang import Lang
from utils.utils import Utils

from .context import ContextCustom


class CustomTextEdit(QTextEdit):
    def __init__(self):
        """
        custom copy paste context
        """
        super().__init__()

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
        new_text = self.toPlainText() + text
        self.setPlainText(new_text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        menu_ = ContextCustom(event=a0)
        menu_.setFixedWidth(120)

        sel = QAction(text=Lang.cut, parent=menu_)
        sel.triggered.connect(self.cut_selection)
        menu_.addAction(sel)

        sel_all = QAction(text=Lang.copy, parent=menu_)
        sel_all.triggered.connect(self.copy_selection)
        menu_.addAction(sel_all)

        sel_all = QAction(text=Lang.paste, parent=menu_)
        sel_all.triggered.connect(self.paste_text)
        menu_.addAction(sel_all)

        menu_.show_menu()