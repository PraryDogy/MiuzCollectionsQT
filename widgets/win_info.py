import os

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtWidgets import QAction, QGridLayout, QLabel, QSpacerItem, QWidget

from cfg import Static, cfg
from system.lang import Lng
from system.multiprocess import OneFileInfo, ProcessWorker
from system.tasks import MultiFileInfo, UThreadPool
from system.utils import Utils

from ._base_widgets import SingleActionWindow, UMenu


class ULabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text=text)

        self.setStyleSheet("font-size: 11px;")



class Selectable(ULabel):
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

        is_path = any((os.path.isdir(full_text), os.path.isfile(full_text)))

        menu_ = UMenu(event=ev)

        label_text = Lng.copy[cfg.lng]
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: Utils.copy_text(text))
        menu_.addAction(sel)

        reveal = QAction(parent=menu_, text=Lng.reveal_in_finder[cfg.lng])
        reveal.triggered.connect(
            lambda: Utils.reveal_files([full_text])
        )
        
        if is_path:
            menu_.addAction(reveal)

        menu_.show_umenu()


class WinInfo(SingleActionWindow):
    finished_ = pyqtSignal()

    def __init__(self, paths: list[str]):
        super().__init__()
        self.setWindowTitle(Lng.info[cfg.lng])
        self.paths = paths

        wid = QWidget()
        self.central_layout.addWidget(wid)

        self.grid_lay = QGridLayout()
        self.grid_lay.setSpacing(5)
        self.grid_lay.setContentsMargins(0, 0, 0, 0)
        wid.setLayout(self.grid_lay)

        self.single_img()

    def single_img(self):

        def poll():
            self.task_timer.stop()
            q = self.task_.proc_q
            if not q.empty():
                res = q.get()
                self.single_img_fin(res)

            if not self.task_.is_alive():
                self.task_.terminate()
            else:
                self.task_timer.start(500)

        self.task_ = ProcessWorker(target=OneFileInfo.start, args=(self.paths[0], ))
        self.task_timer = QTimer(self)
        self.task_timer.setSingleShot(True)
        self.task_timer.timeout.connect(poll)

        self.task_timer.start(500)
        self.task_.start()

    def single_img_fin(self, data: dict | str):

        if isinstance(data, str):
            self.last_label = self.findChildren(ULabel)[-1]
            self.last_label.setText(data)
            return

        row = 0
        l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        r_fl = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        for left_t, right_t in data.items():
            left_lbl = ULabel(left_t + ":")
            right_lbl = Selectable(right_t)
            self.grid_lay.addWidget(left_lbl, row, 0, alignment=l_fl)
            self.grid_lay.addItem(QSpacerItem(15, 0), row, 1)
            self.grid_lay.addWidget(right_lbl, row, 2, alignment=r_fl)
            row += 1
        self.finished_.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.deleteLater()
