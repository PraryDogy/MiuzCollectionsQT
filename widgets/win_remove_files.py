import os
import subprocess

import sqlalchemy
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from base_widgets.svg_btn import SvgBtn
from base_widgets.wins import WinSystem
from cfg import Static
from database import THUMBS, Dbase
from lang import Lang
from main_folders import MainFolder
from utils.utils import Err, Utils

from ._runnable import URunnable, UThreadPool

WARNING_SVG = os.path.join(Static.IMAGES, "warning.svg")
SCRIPTS = "scripts"
REMOVE_FILES_SCPT = os.path.join(SCRIPTS, "remove_files.scpt")

class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class RemoveFilesTask(URunnable):
    def __init__(self, urls: list[str]):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.urls = urls

    def task(self):
        try:
            self.remove_from_db()
            command = ["osascript", REMOVE_FILES_SCPT] + self.urls
            subprocess.run(command)
        except Exception as e:
            Err.print_error(e)
        try:
            self.signals_.finished_.emit()
        except RuntimeError as e:
            Err.print_error(e)

    def remove_from_db(self):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()

        if coll_folder:
            Dbase.create_engine()
            conn = Dbase.engine.connect()
            for i in self.urls:
                short_src = Utils.get_short_src(coll_folder, i)
                q = sqlalchemy.delete(THUMBS)
                q = q.where(THUMBS.c.short_src == short_src)
                q = q.where(THUMBS.c.brand == MainFolder.current.name)

                try:
                    conn.execute(q)
                except Exception as e:
                    Utils.print_error(e)
                    conn.rollback()
                    continue
        
            try:
                conn.commit()
            except Exception as e:
                Utils.print_error(e)
                conn.rollback()

        conn.close()



class RemoveFilesWin(WinSystem):
    finished_ = pyqtSignal(list)
    svg_size = 50

    def __init__(self, urls: list[str]):
        super().__init__()
        self.setWindowTitle(Lang.attention)
        self.urls = urls

        first_row_wid = QWidget()
        self.central_layout.addWidget(first_row_wid)
        first_row_lay = QHBoxLayout()
        first_row_lay.setContentsMargins(0, 0, 0, 0)
        first_row_wid.setLayout(first_row_lay)

        warn = SvgBtn(WARNING_SVG, RemoveFilesWin.svg_size)
        first_row_lay.addWidget(warn)

        t = f"{Lang.move_to_trash} ({len(urls)})?"
        question = QLabel(text=t)
        first_row_lay.addWidget(question)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_wid.setLayout(h_lay)

        ok_btn = QPushButton(Lang.ok)
        ok_btn.clicked.connect(self.cmd_)
        ok_btn.setFixedWidth(90)
        h_lay.addWidget(ok_btn)

        can_btn = QPushButton(Lang.cancel)
        can_btn.clicked.connect(self.deleteLater)
        can_btn.setFixedWidth(90)
        h_lay.addWidget(can_btn)

        self.adjustSize()

    def cmd_(self, *args):
        self.task_ = RemoveFilesTask(self.urls)
        self.task_.signals_.finished_.connect(self.finalize)
        UThreadPool.start(self.task_)

    def finalize(self, *args):
        self.finished_.emit(self.urls)
        del self.task_
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()

        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.cmd_()
        return super().keyPressEvent(a0)
    