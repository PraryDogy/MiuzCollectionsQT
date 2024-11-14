import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtWidgets import QAction, QGridLayout, QLabel, QWidget

from base_widgets import ContextCustom
from base_widgets.wins import WinChild
from cfg import Dynamic
from utils.image_size import get_image_size
from utils.utils import Utils

SPLIT_ = "***"


class RightLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)

        fl = Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(fl)

        self.setCursor(Qt.CursorShape.IBeamCursor)

    def copy_all(self):
        Utils.copy_text(self.text().replace("\n", ""))

    def copy_selected(self, text: str):
        Utils.copy_text(text)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        self.menu_ = ContextCustom(event=ev)

        self.setSelection(0, len(self.text()))
        text = self.text().replace("\n", "")

        label_text = Dynamic.lng.copy
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: self.copy_selected(text=text))
        self.menu_.addAction(sel)

        self.menu_.show_menu()


class InfoText:
    def __init__(self, src: str):
        self.src = src

    def get(self) -> list[str]:

        data: list[str] = []

        name = self.src.split(os.sep)[-1]
        name = Dynamic.lng.file_name + SPLIT_ + name

        src = Dynamic.lng.file_path + SPLIT_ + self.src

        coll = Utils.get_coll_name(self.src)
        coll = Dynamic.lng.collection + SPLIT_ + coll

        for i in (name, src, coll):
            data.append(i)

        try:
            filemod = datetime.fromtimestamp(os.path.getmtime(filename=self.src))
            filemod = filemod.strftime("%d-%m-%Y, %H:%M:%S")
            filemod = Dynamic.lng.date_changed + SPLIT_ + filemod

            data.append(filemod)

        except Exception as e:
            Utils.print_err(parent=self, error=e)

        try:
            w, h = get_image_size(self.src)
            resol = f"{w}x{h}"
            resol = Dynamic.lng.resolution + SPLIT_ + resol

            data.append(resol)

        except Exception as e:
            Utils.print_err(parent=self, error=e)

        try:
            size_ = os.path.getsize(filename=self.src)
            size_ = round(size_ / (1024*1024), 2)

            if size_ < 1000:
                f_size = f"{size_}{Dynamic.lng.mb}"
            else:
                size_ = os.path.getsize(filename=self.src)
                size_ = round(self.size / (1024**3), 2)
                f_size = f"{size_}{Dynamic.lng.gb}"

            f_size = Dynamic.lng.file_size + SPLIT_ + f_size

            data.append(f_size)

        except Exception as e:
            Utils.print_err(parent=self, error=e)

        except Exception as e:
            Utils.print_err(parent=self, error=e)

        return data


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

        data = InfoText(self.src)
        data = data.get()

        row = 0
        l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        r_fl = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

        for i in data:
            left, right = i.split(SPLIT_)
            right = self.rowed_text(right)

            left_lbl = QLabel(text=left)
            right_lbl = RightLabel(text=right)

            grid.addWidget(left_lbl, row, 0, alignment=l_fl)
            grid.addWidget(right_lbl, row, 1, alignment=r_fl)

            row += 1

    def rowed_text(self, text: str):
        max_row = 38

        if len(text) > max_row:
            text = [
                text[i:i + max_row]
                for i in range(0, len(text), max_row)
                ]
            text = "\n".join(text)

        return text

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.close()
