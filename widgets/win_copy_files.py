import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from cfg import cfg
from system.items import CopyTaskItem
from system.lang import Lng
from system.multiprocess import CopyTask, CopyTaskWorker

from ._base_widgets import SingleActionWindow
from .progressbar_win import ProgressbarWin


class ReplaceFilesWin(SingleActionWindow):
    descr_text = "Заменить существующие файлы?"
    title_text = "Замена"
    replace_one_text = "Заменить"
    replace_all_text = "Заменить все"
    stop_text = "Стоп"
    icon_size = 50
    icon_path = "./images/warning.svg"

    replace_one_press = pyqtSignal()
    replace_all_press = pyqtSignal()
    stop_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.title_text)
        self.setFixedSize(400, 100)
        self.central_layout.setContentsMargins(5, 5, 5, 5)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        warn = QSvgWidget()
        warn.load(self.icon_path)
        warn.setFixedSize(self.icon_size, self.icon_size)
        h_lay.addWidget(warn)

        test_two = QLabel(self.descr_text)
        test_two.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        h_lay.addWidget(test_two)

        btn_wid = QWidget()
        self.central_layout.addWidget(btn_wid, alignment=Qt.AlignmentFlag.AlignRight)

        btn_lay = QHBoxLayout()
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)
        btn_lay.setAlignment(Qt.AlignmentFlag.AlignRight)

        replace_all_btn = QPushButton(self.replace_all_text)
        replace_all_btn.setFixedWidth(95)
        replace_all_btn.clicked.connect(lambda: self.replace_all_cmd())
        btn_lay.addWidget(replace_all_btn)

        replace_one_btn = QPushButton(self.replace_one_text)
        replace_one_btn.setFixedWidth(95)
        replace_one_btn.clicked.connect(lambda: self.replace_one_cmd())
        btn_lay.addWidget(replace_one_btn)

        stop_btn = QPushButton(self.stop_text)
        stop_btn.setFixedWidth(95)
        stop_btn.clicked.connect(lambda: self.stop_cmd())
        btn_lay.addWidget(stop_btn)
        
        self.adjustSize()

    def replace_one_cmd(self):
        self.replace_one_press.emit()

    def replace_all_cmd(self):
        self.replace_all_press.emit()

    def stop_cmd(self):
        self.stop_pressed.emit()

    def closeEvent(self, a0):
        a0.ignore()
    

class ErrorWin(SingleActionWindow):
    descr_text = "Произошла ошибка при копировании"
    title_text = "Ошибка"
    ok_text = "Ок"
    icon_size = 50

    def __init__(self):
        super().__init__()
        self.setWindowTitle(ErrorWin.title_text)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        warn = QSvgWidget()
        warn.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        warn.load(self.icon_path)
        warn.resize(self.icon_size, self.icon_size)
        h_lay.addWidget(warn)

        test_two = QLabel(ErrorWin.descr_text)
        test_two.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        h_lay.addWidget(test_two)

        ok_btn = QPushButton(ErrorWin.ok_text)
        ok_btn.clicked.connect(self.deleteLater)
        ok_btn.setFixedWidth(90)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.deleteLater()
        elif a0.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if a0.key() == Qt.Key.Key_Q:
                return
        return super().keyPressEvent(a0)
    

class WinCopyFiles(ProgressbarWin):
    finished_ = pyqtSignal(list)
    ms = 500

    def __init__(self, dst_dir: str, src_urls: list[str], is_cut: bool):
        super().__init__(Lng.copying[cfg.lng])
        self.dst_urls: list[str] = []
        self.cancel.connect(self.deleteLater)
        is_cut = True if is_cut == "cut" else False

        self.copy_task_item = CopyTaskItem(
            dst_dir=dst_dir,
            src_urls=src_urls,
            is_cut=is_cut
        )
        self.copy_task = CopyTaskWorker(
            target=CopyTask.start,
            args=(self.copy_task_item, )
        )
        self.copy_timer = QTimer(self)
        self.copy_timer.setSingleShot(True)
        self.copy_timer.timeout.connect(self.poll_task)

        self.copy_task.start()
        self.copy_timer.start(self.ms)

    def poll_task(self):
        self.copy_timer.stop()
        finished = False

        if not self.copy_task.proc_q.empty():
            self.copy_item: CopyTaskItem = self.copy_task.proc_q.get()

            if self.copy_item.msg == "error":
                self.error_win = ErrorWin()
                self.error_win.center_to_parent(self.window())
                self.error_win.show()
                self.stop_task()
                self.deleteLater()
                return
            
            elif self.copy_item.msg == "need_replace":
                self.replace_win = ReplaceFilesWin()
                self.replace_win.center_to_parent(self)
                self.replace_win.replace_all_press.connect(self.replace_all)
                self.replace_win.replace_one_press.connect(self.replace_one)
                self.replace_win.stop_pressed.connect(self.stop_pressed)
                self.replace_win.show()
                return
            
            elif self.copy_item.msg == "finished":
                finished = True
            
            if self.progressbar.maximum() == 0:
                self.progressbar.setMaximum(self.copy_item.total_size)

            if len(self.dst_urls) == 0 and self.copy_item.dst_urls:
                self.dst_urls.extend(self.copy_item.dst_urls)

            self.progressbar.setValue(self.copy_item.current_size)
            self.below_label.setText(
                f'{self.windowTitle()} {self.copy_item.current_count} из {self.copy_item.total_count}'
            )

        if not self.copy_task.is_alive() or finished:
            self.progressbar.setValue(self.progressbar.maximum())
            self.below_label.setText(
                f'{self.windowTitle()} {self.copy_item.total_count} из {self.copy_item.total_count}'
            )     
            self.finished_.emit(self.dst_urls)
            self.stop_task()
            self.deleteLater()
        else:
            self.copy_timer.start(self.ms)

    def limit_string(self, text: str, limit: int = 30):
        if len(text) > limit:
            return text[:limit] + "..."
        return text
    
    def stop_pressed(self):
        self.replace_win.deleteLater()
        self.stop_task()
        self.deleteLater()
    
    def replace_one(self):
        self.copy_timer.stop()
        self.copy_item.msg = "replace_one"
        self.copy_task.gui_q.put(self.copy_item)
        self.replace_win.deleteLater()
        self.copy_timer.start(self.ms)

    def replace_all(self):
        self.copy_timer.stop()
        self.copy_item.msg = "replace_all"
        self.copy_task.gui_q.put(self.copy_item)
        self.replace_win.deleteLater()
        self.copy_timer.start(self.ms)

    def stop_task(self):
        self.copy_timer.stop()
        self.copy_task.terminate()
