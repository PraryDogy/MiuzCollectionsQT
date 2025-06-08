import os

import sqlalchemy
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtWidgets import QAction, QGridLayout, QLabel, QMainWindow, QWidget

from base_widgets import ContextCustom
from base_widgets.wins import WinSystem
from cfg import Static
from database import THUMBS, Dbase
from lang import Lang
from main_folders import MainFolder
from utils.utils import Utils

from ._runnable import URunnable, UThreadPool

MAX_ROW = 50


class Selectable(QLabel):
    def __init__(self, text: str):
        super().__init__(text)

        fl = Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(fl)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        text = self.selectedText()
        text = text.replace(Static.PARAGRAPH_SEP, "")
        text = text.replace(Static.LINE_FEED, "")

        full_text = self.text().replace(Static.PARAGRAPH_SEP, "").replace(Static.LINE_FEED, "")

        is_path = bool(
            os.path.isdir(full_text)
            or
            os.path.isfile(full_text)
        )

        menu_ = ContextCustom(event=ev)

        label_text = Lang.copy
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: Utils.copy_text(text))
        menu_.addAction(sel)

        reveal = QAction(parent=menu_, text=Lang.reveal_in_finder)
        reveal.triggered.connect(
            lambda: Utils.reveal_files(files_list=[full_text])
        )
        menu_.addAction(reveal)

        if not is_path:
            reveal.setDisabled(True)

        menu_.show_menu()

        # self.setSelection(0, 0)


class WorkerSignals(QObject):
    finished_ = pyqtSignal(dict)
    finished_resol = pyqtSignal(str)


class SingleImgInfo(URunnable):
    def __init__(self, full_src: str):
        super().__init__()
        self.full_src = full_src
        self.signals_ = WorkerSignals()

    def task(self):
        coll_folder = MainFolder.current.current_path
        try:
            name = os.path.basename(self.full_src)
            _, type_ = os.path.splitext(name)
            stats = os.stat(self.full_src)
            size = Utils.get_f_size(stats.st_size)
            mod = Utils.get_f_date(stats.st_mtime)
            coll = Utils.get_coll_name(coll_folder, self.full_src)
            full_hash = Utils.create_full_hash(self.full_src)

            res = {
                Lang.file_name: self.lined_text(name),
                Lang.type_: type_,
                Lang.file_size: size,
                Lang.place: self.lined_text(self.full_src),
                Lang.hash_path: self.lined_text(full_hash),
                Lang.changed: mod,
                Lang.resol: Lang.calculating,
                Lang.collection: self.lined_text(coll)
                }
            
            self.signals_.finished_.emit(res)
        
        except Exception as e:
            Utils.print_error(e)
            self.signals_.finished_.emit({})
   
    def get_img_resol(self, src: str):
        img_ = Utils.read_image(src)
        if img_ is not None and len(img_.shape) > 1:
            h, w = img_.shape[0], img_.shape[1]
            return f"{w}x{h}"
        else:
            return "-"

    def lined_text(self, text: str):
        if len(text) > MAX_ROW:
            text = [
                text[i:i + MAX_ROW]
                for i in range(0, len(text), MAX_ROW)
                ]
            return "\n".join(text)
        else:
            return text


class WinInfo(WinSystem):
    finished_ = pyqtSignal()

    def __init__(self, full_src: str):
        super().__init__()
        self.setWindowTitle(Lang.info)
        self.full_src = full_src
        self.init_ui()

    def init_ui(self):
        self.task_ = SingleImgInfo(self.full_src)
        self.task_.signals_.finished_.connect(self.load_info_fin)
        UThreadPool.start(self.task_)

    def load_info_fin(self, data: dict[str, str]):
        wid = QWidget()
        self.central_layout.addWidget(wid)

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        wid.setLayout(grid)

        row = 0
        l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        r_fl = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

        for left_t, right_t in data.items():
            left_lbl = QLabel(text=left_t)
            right_lbl = Selectable(text=right_t)

            grid.addWidget(left_lbl, row, 0, alignment=l_fl)
            grid.addWidget(right_lbl, row, 1, alignment=r_fl)

            row += 1

        r_labels = [i for i in self.findChildren(Selectable)]
        resol_label = r_labels[6]
        full_src_label = r_labels[3]
        full_src = full_src_label.text().strip().replace("\n", "")
        
        resol_task = SingleImgInfo(self.full_src)
        resol_task.signals_.finished_resol.connect(
            lambda resol: self.finished_resol_task(wid=resol_label, resol=resol)
        )
        UThreadPool.start(resol_task)

        self.finished_.emit()

    def finished_resol_task(self, wid: Selectable, resol: str):
        wid.setText(resol)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.close()
