import os

import sqlalchemy
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                             QSizePolicy, QVBoxLayout, QWidget)

from cfg import Cfg
from system.database import Dbase, Dirs
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker, SmbChecker
from system.utils import Utils

from ._base_widgets import SelectableLabel
from .win_warn import WarningWindow


class PathWidget(QGroupBox):
    mf_path_avaiable = pyqtSignal()
    magnifier = "images/magnifier.svg"
    green_checkmark = "images/green_checkmark.svg"
    hh = 70
    icon_size = 35

    def __init__(self, mf: Mf):
        super().__init__()
        self.mf = mf
        self.setAcceptDrops(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
    
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(6, 2, 6, 2)
        self.main_lay.setSpacing(0)

        self.main_wid = QWidget()
        self.main_lay.addWidget(self.main_wid)

        self.mf_temp_path = mf.get_avaiable_mf_path()
        if self.mf_temp_path:
            self.ok_path_widget()
        else:
            self.start_checker()
            self.no_path_widget()

    def no_path_widget(self):
        self.main_wid.deleteLater()
        self.main_wid = QWidget()
        self.main_lay.addWidget(self.main_wid)

        h_lay = QHBoxLayout(self.main_wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(self.magnifier)
        right_btn.setFixedSize(self.icon_size, self.icon_size)
        h_lay.addWidget(right_btn)
        
        lines = (
            f"{Lng.folder_path[Cfg.lng_index]}:",
            Lng.path_hint_texts[Cfg.lng_index].lower()
        )
        left_label = QLabel("\n".join(lines))
        left_label.setWordWrap(True)
        h_lay.addWidget(left_label)

        h_lay.addStretch()

    def check_mf_temp_path(self):
        with Dbase.main_engine.connect() as conn:
            stmt = (
                sqlalchemy.select(Dirs.rel_dir_path)
                .where(Dirs.mf_alias==self.mf.mf_alias)
            )
            dir_records = conn.execute(stmt).scalars().all()
        exist_paths = []
        for i in dir_records:
            abs_path = Utils.get_abs_any_path(
                self.mf_temp_path,
                i
            ).rstrip(os.sep)
            if os.path.exists(abs_path):
                exist_paths.append(abs_path)
        if len(dir_records) == 1:
            return True
        elif len(exist_paths) == 1 and self.mf_temp_path == exist_paths[0]:
            return False
        else:
            return True

    def ok_path_widget(self):
        self.main_wid.deleteLater()
        self.main_wid = QWidget()
        self.main_lay.addWidget(self.main_wid)

        h_lay = QHBoxLayout(self.main_wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(self.green_checkmark)
        right_btn.setFixedSize(35, 35)
        h_lay.addWidget(right_btn)

        lines = (
            f"{Lng.folder_path[Cfg.lng_index]}:",
            self.mf_temp_path
        )
        left_label = SelectableLabel('\n'.join(lines))
        h_lay.addWidget(left_label)

        h_lay.addStretch()

    def open_win_warn(self):
        self.warn_win = WarningWindow(Lng.bad_smb[Cfg.lng_index])
        self.warn_win.center_to_parent(self.window())
        self.warn_win.show()

    def start_checker(self):

        def poll_task():
            if not self.task.process_queue.empty():
                self.mf_temp_path = self.task.process_queue.get().rstrip(os.sep)
                if self.check_mf_temp_path():
                    self.mf_path_avaiable.emit()
                    self.ok_path_widget()
                    self.stop_task()
                else:
                    self.mf_temp_path = None
                    QTimer.singleShot(1, self.no_path_widget)
                    self.open_win_warn()
            else:
                QTimer.singleShot(500, poll_task)

        self.task = ProcessWorker(
            target=SmbChecker.start,
            args=(self.mf, )
        )
        self.task.start()
        QTimer.singleShot(500, poll_task)

    def stop_task(self):
        if hasattr(self, "task"):
            try:
                self.task.terminate_join()
            except Exception as e:
                print("path widget stop task error", e)

    def mouseReleaseEvent(self, a0: QMouseEvent):
        if not a0.button() != 2:
            return
        dialog = QFileDialog()
        url = dialog.getExistingDirectory()
        if url:
            self.mf_temp_path = url.rstrip(os.sep)
            if self.check_mf_temp_path():
                self.mf_path_avaiable.emit()
                self.ok_path_widget()
                self.stop_task()
            else:
                self.mf_temp_path = None
                QTimer.singleShot(1, self.no_path_widget)
                self.open_win_warn()
        return super().mouseReleaseEvent(a0)
        
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if url and os.path.isdir(url):
                self.mf_temp_path = url.rstrip(os.sep)

                if self.check_mf_temp_path():
                    self.mf_path_avaiable.emit()
                    self.ok_path_widget()
                    self.stop_task()
                else:
                    self.mf_temp_path = None
                    QTimer.singleShot(1, self.no_path_widget)
                    self.open_win_warn()
        return super().dropEvent(a0)
    
    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)

    def deleteLater(self):
        self.stop_task()
        return super().deleteLater()
    
    def closeEvent(self, a0):
        self.stop_task()
        return super().closeEvent(a0)