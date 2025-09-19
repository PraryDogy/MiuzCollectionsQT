import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtWidgets import QAction, QGridLayout, QLabel, QWidget

from cfg import Cfg, Static
from system.lang import Lng
from system.tasks import MultiFileInfo, OneFileInfo, UThreadPool
from system.utils import Utils

from ._base_widgets import UMenu, SingleActionWindow


class Selectable(QLabel):
    sym_line_feed = "\u000a"
    sym_paragraph_sep = "\u2029"

    def __init__(self, text: str):
        super().__init__(text)

        fl = Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(fl)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        text = self.selectedText()
        text = text.replace(self.sym_paragraph_sep, "")
        text = text.replace(self.sym_line_feed, "")

        full_text = self.text().replace(self.sym_paragraph_sep, "")
        full_text = full_text.replace(self.sym_line_feed, "")

        is_path = bool(
            os.path.isdir(full_text)
            or
            os.path.isfile(full_text)
        )

        menu_ = UMenu(event=ev)

        label_text = Lng.copy[Cfg.lng]
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: Utils.copy_text(text))
        menu_.addAction(sel)

        reveal = QAction(parent=menu_, text=Lng.reveal_in_finder[Cfg.lng])
        reveal.triggered.connect(
            lambda: Utils.reveal_files([full_text])
        )
        menu_.addAction(reveal)

        if not is_path:
            reveal.setDisabled(True)

        menu_.show_umenu()


class WinInfo(SingleActionWindow):
    finished_ = pyqtSignal()

    def __init__(self, paths: list[str]):
        super().__init__()
        self.setWindowTitle(Lng.info[Cfg.lng])
        self.paths = paths

        wid = QWidget()
        self.central_layout.addWidget(wid)

        self.grid_lay = QGridLayout()
        self.grid_lay.setSpacing(5)
        self.grid_lay.setContentsMargins(0, 0, 0, 0)
        wid.setLayout(self.grid_lay)

        if len(self.paths) == 1:
            if os.path.isfile(self.paths[0]):
                self.single_img()
            else:
                print("info dir")
        else:
            self.multiple_img()

    def single_img(self):
        self.task_ = OneFileInfo(self.paths[0])
        self.task_.sigs.finished_.connect(lambda data: self.single_img_fin(data))
        UThreadPool.start(self.task_)

    def multiple_img(self):
        self.task_ = MultiFileInfo(self.paths)
        self.task_.sigs.finished_.connect(lambda data: self.multiple_img_fin(data))
        UThreadPool.start(self.task_)

    def multiple_img_fin(self, data: dict[str, str]):
        row = 0
        l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        r_fl = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        for left_t, right_t in data.items():
            left_lbl = QLabel(left_t)
            right_lbl = Selectable(right_t)
            self.grid_lay.addWidget(left_lbl, row, 0, alignment=l_fl)
            self.grid_lay.addWidget(right_lbl, row, 1, alignment=r_fl)
            row += 1

        self.grid_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.last_label = self.findChildren(QLabel)[-1]
        cmd = lambda text: self.last_label.setText(text)
        self.task_.sigs.delayed_info.connect(cmd)
        self.finished_.emit()

    def single_img_fin(self, data: dict[str, str]):
        row = 0
        l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        r_fl = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        for left_t, right_t in data.items():
            left_lbl = QLabel(left_t)
            right_lbl = Selectable(right_t)
            self.grid_lay.addWidget(left_lbl, row, 0, alignment=l_fl)
            self.grid_lay.addWidget(right_lbl, row, 1, alignment=r_fl)
            row += 1

        self.last_label = self.findChildren(QLabel)[-1]
        cmd = lambda text: self.last_label.setText(text)
        self.task_.sigs.delayed_info.connect(cmd)
        self.finished_.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.deleteLater()
