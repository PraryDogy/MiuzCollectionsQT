import os
import subprocess

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from base_widgets.svg_btn import SvgBtn
from base_widgets.wins import WinSystem
from cfg import Static
from lang import Lang
from main_folders import MainFolder
from utils.scaner import DbUpdater, FileUpdater
from utils.tasks import URunnable, UThreadPool
from utils.utils import Err, Utils

WARNING_SVG = os.path.join(Static.images_dir, "warning.svg")
SCRIPTS = "scripts"
REMOVE_FILES_SCPT = os.path.join(SCRIPTS, "remove_files.scpt")

class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class RemoveFilesTask(URunnable):
    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.img_path_list = img_path_list

    def task(self):
        try:
            self.remove_thumbs()
            command = ["osascript", REMOVE_FILES_SCPT] + self.img_path_list
            subprocess.run(command)
        except Exception as e:
            Err.print_error(e)
        try:
            self.signals_.finished_.emit()
        except RuntimeError as e:
            Err.print_error(e)

    def remove_thumbs(self):      
        thumb_path_list = [
            Utils.create_thumb_path(img_path)
            for img_path in self.img_path_list
        ]
        rel_thumb_path_list = [
            Utils.get_rel_thumb_path(thumb_path)
            for thumb_path in thumb_path_list
        ]

        main_folder = MainFolder.current
        
        # new_items пустой так как мы только удаляем thumbs из hashdir
        file_updater = FileUpdater(rel_thumb_path_list, [], main_folder)
        del_items, new_items = file_updater.run()
        
        # new_items пустой так как мы только удаляем thumbs из бд
        db_updater = DbUpdater(del_items, [], main_folder)
        db_updater.run()
        

class RemoveFilesWin(WinSystem):
    finished_ = pyqtSignal(list)
    svg_size = 50

    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.setWindowTitle(Lang.attention)
        self.img_path_list = img_path_list

        first_row_wid = QWidget()
        self.central_layout.addWidget(first_row_wid)
        first_row_lay = QHBoxLayout()
        first_row_lay.setContentsMargins(0, 0, 0, 0)
        first_row_wid.setLayout(first_row_lay)

        warn = SvgBtn(WARNING_SVG, RemoveFilesWin.svg_size)
        first_row_lay.addWidget(warn)

        t = f"{Lang.move_to_trash} ({len(img_path_list)})?"
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
        self.task_ = RemoveFilesTask(self.img_path_list)
        self.task_.signals_.finished_.connect(self.finalize)
        UThreadPool.start(self.task_)

    def finalize(self, *args):
        self.finished_.emit(self.img_path_list)
        del self.task_
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()

        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.cmd_()
        return super().keyPressEvent(a0)
    