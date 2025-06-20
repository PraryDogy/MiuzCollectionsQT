import os

from PyQt5.QtCore import QObject, Qt, pyqtSignal, QTimer
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
            lambda: Utils.reveal_files([full_text])
        )
        menu_.addAction(reveal)

        if not is_path:
            reveal.setDisabled(True)

        menu_.show_menu()

        # self.setSelection(0, 0)


class WorkerSignals(QObject):
    finished_ = pyqtSignal(dict)
    delayed_info = pyqtSignal(str)


class Tools:
    @classmethod
    def get_img_resol(cls, img_path: str):
        img_ = Utils.read_image(img_path)
        if img_ is not None and len(img_.shape) > 1:
            h, w = img_.shape[0], img_.shape[1]
            return f"{w}x{h}"
        else:
            return ""

    @classmethod
    def lined_text(cls, text: str):
        if len(text) > MAX_ROW:
            text = [
                text[i:i + MAX_ROW]
                for i in range(0, len(text), MAX_ROW)
                ]
            return "\n".join(text)
        else:
            return text

class SingleImgInfo(URunnable):
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals_ = WorkerSignals()

    def task(self):
        mail_folder_path = MainFolder.current.is_available()
        try:
            name = os.path.basename(self.url)
            _, type_ = os.path.splitext(name)
            stats = os.stat(self.url)
            size = Utils.get_f_size(stats.st_size)
            mod = Utils.get_f_date(stats.st_mtime)
            coll = Utils.get_coll_name(mail_folder_path, self.url)
            thumb_path = Utils.create_thumb_path(self.url)

            res = {
                Lang.file_name: Tools.lined_text(name),
                Lang.type_: type_,
                Lang.file_size: size,
                Lang.place: Tools.lined_text(self.url),
                Lang.thumb_path: Tools.lined_text(thumb_path),
                Lang.changed: mod,
                Lang.collection: Tools.lined_text(coll),
                Lang.resol: Lang.calculating,
                }
            
            self.signals_.finished_.emit(res)

            res = Tools.get_img_resol(self.url)
            if res:
                self.signals_.delayed_info.emit(res)
        
        except Exception as e:
            Utils.print_error(e)
            res = {
                Lang.file_name: Tools.lined_text(os.path.basename(self.url)),
                Lang.place: Tools.lined_text(self.url),
                Lang.type_: Tools.lined_text(os.path.splitext(self.url)[0])
                }
            self.signals_.finished_.emit(res)
        

class MultipleImgInfo(URunnable):
    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.img_path_list = img_path_list
        self.signals_ = WorkerSignals()
    
    def task(self):
        names = [
            os.path.basename(i)
            for i in self.img_path_list
        ]
        names = names[:10]
        names = ", ".join(names)
        names = Tools.lined_text(names)
        if len(self.img_path_list) > 10:
            names = names + ", ..."

        res = {
            Lang.file_name: names,
            Lang.total: str(len(self.img_path_list)),
            Lang.file_size: self.get_total_size()
        }
        self.signals_.finished_.emit(res)

    def get_total_size(self):
        total = 0
        for i in self.img_path_list:
            stats = os.stat(i)
            size_ = stats.st_size
            total += size_

        return Utils.get_f_size(total)


class WinInfo(WinSystem):
    finished_ = pyqtSignal()

    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.setWindowTitle(Lang.info)
        self.img_path_list = img_path_list

        wid = QWidget()
        self.central_layout.addWidget(wid)

        self.grid_lay = QGridLayout()
        self.grid_lay.setSpacing(5)
        self.grid_lay.setContentsMargins(0, 0, 0, 0)
        wid.setLayout(self.grid_lay)

        if len(self.img_path_list) == 1:
            if os.path.isfile(self.img_path_list[0]):
                self.single_img()
            else:
                print("info dir")
        else:
            self.multiple_img()

    def single_img(self):
        self.task_ = SingleImgInfo(self.img_path_list[0])
        self.task_.signals_.finished_.connect(lambda data: self.single_img_fin(data))
        UThreadPool.start(self.task_)

    def multiple_img(self):
        self.task_ = MultipleImgInfo(self.img_path_list)
        self.task_.signals_.finished_.connect(lambda data: self.multiple_img_fin(data))
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
        self.task_.signals_.delayed_info.connect(cmd)
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
        self.task_.signals_.delayed_info.connect(cmd)
        self.finished_.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_(a0)
        return super().keyPressEvent(a0)
  
    def close_(self, *args):
        self.deleteLater()
