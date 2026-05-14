import os

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                             QSizePolicy, QVBoxLayout, QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker, SmbChecker

from ._base_widgets import SelectableLabel


class PathWidget(QGroupBox):
    magnifier = "images/magnifier.svg"
    green_checkmark = "images/green_checkmark.svg"
    hh = 70
    icon_size = 35
    textChanged = pyqtSignal(str)
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

        mf_path = mf.get_avaiable_mf_path()
        if mf_path:
            mf.set_mf_current_path(mf_path)
            self.mf_path = mf_path
            self.ok_path_widget()
        else:
            self.mf_path = None
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
            self.mf_path
        )
        left_label = SelectableLabel('\n'.join(lines))
        h_lay.addWidget(left_label)

        h_lay.addStretch()

    def start_checker(self):

        def poll_task():
            if not self.task.process_queue.empty():
                self.mf_path = self.mf.get_avaiable_mf_path()
                self.ok_path_widget()
                self.task.terminate_join()
            else:
                QTimer.singleShot(500, poll_task)

        self.task = ProcessWorker(
            target=SmbChecker.start,
            args=(self.mf, )
        )
        self.task.start()
        QTimer.singleShot(500, poll_task)

    def write_changes(self):
        self.mf.mf_paths = [self.mf_path, ]
        Mf.write_json_data()

    def mouseReleaseEvent(self, a0: QMouseEvent):
        if not a0.button() != 2:
            return
        dialog = QFileDialog()
        url = dialog.getExistingDirectory()
        if url:
            self.mf_path = url
            self.textChanged.emit(url)
            self.ok_path_widget()
        return super().mouseReleaseEvent(a0)
    
    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
        
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if url and os.path.isdir(url):
                self.mf_path = url
                self.textChanged.emit(url)
                self.ok_path_widget()
        return super().dropEvent(a0)
    
    def deleteLater(self):
        self.task.terminate_join()
        return super().deleteLater()
    
    def closeEvent(self, a0):
        self.task.terminate_join()
        return super().closeEvent(a0)