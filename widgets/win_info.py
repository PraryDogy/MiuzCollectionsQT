import os

import sqlalchemy
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtWidgets import QAction, QGridLayout, QLabel, QMainWindow, QWidget

from base_widgets import ContextCustom
from base_widgets.wins import WinSystem
from database import THUMBS, Dbase
from lang import Lang
from utils.utils import URunnable, UThreadPool, Utils


class RightLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)

        fl = Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(fl)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        self.setSelection(0, len(self.text()))
        text = self.text().replace("\n", "")
        cmd_ = lambda: Utils.copy_text(text)

        menu_ = ContextCustom(event=ev)


        label_text = Lang.copy
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(cmd_)
        menu_.addAction(sel)

        menu_.show_menu()


class WorkerSignals(QObject):
    finished_ = pyqtSignal(dict)


class InfoTask(URunnable):
    def __init__(self, short_src: str, coll_folder: str):
        super().__init__()
        self.short_src = short_src
        self.coll_folder = coll_folder
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):
        """имя тип размер место изменен разрешение коллекция"""
        conn = Dbase.engine.connect()

        cols = (THUMBS.c.size, THUMBS.c.mod, THUMBS.c.resol,THUMBS.c.coll)
        q = sqlalchemy.select(*cols).where(THUMBS.c.src==self.short_src)

        res = conn.execute(q).first()
        conn.close()

        if res:
            self.signals_.finished_.emit(self.get_db_info(*res))
        else:
            self.signals_.finished_.emit({})
   
    def get_db_info(self, size, mod, resol, coll) -> dict[str, str]:

        name = self.lined_text(
            os.path.basename(self.short_src)
        )

        full_src = self.lined_text(
            Utils.get_full_src(self.coll_folder,self.short_src)
        )

        _, type_ = os.path.splitext(name)
        size = Utils.get_f_size(size)
        mod = Utils.get_f_date(mod)

        res = {
            Lang.file_name: name,
            Lang.type_: type_,
            Lang.file_size: size,
            Lang.place:full_src,
            Lang.changed: mod,
            Lang.resol: resol,
            Lang.collection: coll
            }

        return res

    def lined_text(self, text: str):
        max_row = 38

        if len(text) > max_row:
            text = [
                text[i:i + max_row]
                for i in range(0, len(text), max_row)
                ]
            return "\n".join(text)
        else:
            return text


class WinInfo(WinSystem):
    def __init__(self, parent: QMainWindow, short_src: str, coll_folder: str):
        super().__init__()

        if not isinstance(parent, QMainWindow):
            raise TypeError

        self.setWindowTitle(Lang.info)
        self.parent_ = parent
        self.short_src = short_src
        self.coll_folder = coll_folder

        self.init_ui()

    def init_ui(self):
        self.task_ = InfoTask(
            short_src=self.short_src,
            coll_folder=self.coll_folder
        )
        self.task_.signals_.finished_.connect(self.load_info_fin)
        UThreadPool.pool.start(self.task_)

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
            right_lbl = RightLabel(text=right_t)

            grid.addWidget(left_lbl, row, 0, alignment=l_fl)
            grid.addWidget(right_lbl, row, 1, alignment=r_fl)

            row += 1

        self.adjustSize()
        self.setFixedSize(self.sizeHint().width(), self.sizeHint().height())

        self.center_relative_parent(self.parent_)
        self.show()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.close()
