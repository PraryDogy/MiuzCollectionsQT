import os

import sqlalchemy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtWidgets import QAction, QGridLayout, QLabel, QWidget

from base_widgets import ContextCustom
from base_widgets.wins import WinChild
from cfg import Dynamic, JsonData
from database import THUMBS, Dbase
from utils.utils import Utils


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


        label_text = Dynamic.lng.copy
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(cmd_)
        menu_.addAction(sel)

        menu_.show_menu()


class InfoTask:
    def __init__(self, src: str):
        self.src = src

    def get(self) -> dict[str, str]:
        """имя тип размер место изменен разрешение коллекция"""
        conn = Dbase.engine.connect()

        short_src = self.src.replace(JsonData.coll_folder, "")
        cols = (THUMBS.c.size, THUMBS.c.mod, THUMBS.c.resol,THUMBS.c.coll)
        q = sqlalchemy.select(*cols).where(THUMBS.c.src==short_src)

        res = conn.execute(q).first()
        conn.close()

        if res:
            return self.get_db_info(*res)
        else:
            return {}
   
    def get_db_info(self, size, mod, resol, coll):

        name = os.path.basename(self.src)
        _, type_ = os.path.splitext(name)

        res = {
            Dynamic.lng.file_name: self.lined_text(name),
            Dynamic.lng.type_: type_,
            Dynamic.lng.file_size: Utils.get_f_size(size),
            Dynamic.lng.place: self.lined_text(self.src),
            Dynamic.lng.changed: Utils.get_f_date(mod),
            Dynamic.lng.resol: resol,
            Dynamic.lng.collection: coll
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


class WinInfo(WinChild):
    def __init__(self, src: str):
        super().__init__()
        self.close_btn_cmd(self.close_)
        self.min_btn_disable()
        self.max_btn_disable()
        self.set_titlebar_title(Dynamic.lng.info)

        self.src = src
        self.l_ww = 100
        self.init_ui()

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

    def init_ui(self):
        wid = QWidget()
        self.content_lay_v.addWidget(wid)

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setContentsMargins(0, 0, 0, 0)
        wid.setLayout(grid)

        data = InfoTask(self.src)
        data = data.get()

        row = 0
        l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        r_fl = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

        for left_t, right_t in data.items():
            left_lbl = QLabel(text=left_t)
            right_lbl = RightLabel(text=right_t)

            grid.addWidget(left_lbl, row, 0, alignment=l_fl)
            grid.addWidget(right_lbl, row, 1, alignment=r_fl)

            row += 1

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.close()
