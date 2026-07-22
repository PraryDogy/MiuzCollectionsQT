import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import CopyTask, CopyTaskItem, CopyTaskWorker

from ._base_widgets import UMainWidget, UPushButton, WinProgressbar


class ReplaceButton(UPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("font-size: 9pt;")
        self.setFixedWidth(75)



class ReplaceFilesWin(UMainWidget):
    icon_size = 40
    ww = 330
    icon_path = os.path.join(Static.internal_images, "warning.svg")

    replace_one_press = pyqtSignal()
    replace_all_press = pyqtSignal()
    stop_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.replace[JsonData.lng_index])
        self.setFixedWidth(self.ww)
        self.central_layout.setContentsMargins(5, 5, 10, 5)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = QHBoxLayout(h_wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        warn = QSvgWidget()
        warn.load(self.icon_path)
        warn.setFixedSize(self.icon_size, self.icon_size)
        h_lay.addWidget(warn)

        test_two = QLabel(Lng.replace_existing_files[JsonData.lng_index])
        test_two.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        h_lay.addWidget(test_two)

        btn_wid = QWidget()
        self.central_layout.addWidget(btn_wid, alignment=Qt.AlignmentFlag.AlignRight)

        btn_lay = QHBoxLayout(btn_wid)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(10)
        btn_lay.setAlignment(Qt.AlignmentFlag.AlignRight)

        replace_all_btn = ReplaceButton(Lng.replace_all[JsonData.lng_index])
        replace_all_btn.clicked.connect(lambda: self.replace_all_cmd())
        btn_lay.addWidget(replace_all_btn)

        replace_one_btn = ReplaceButton(Lng.replace_one[JsonData.lng_index])
        replace_one_btn.clicked.connect(lambda: self.replace_one_cmd())
        btn_lay.addWidget(replace_one_btn)

        stop_btn = ReplaceButton(Lng.stop[JsonData.lng_index])
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
    

class ErrorWin(UMainWidget):
    icon_size = 40
    icon_path = os.path.join(Static.internal_images, "warning.svg")

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.error[JsonData.lng_index])
        self.central_layout.setContentsMargins(5, 5, 10, 10)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = QHBoxLayout(h_wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        warn = QSvgWidget()
        warn.load(self.icon_path)
        warn.setFixedSize(self.icon_size, self.icon_size)
        h_lay.addWidget(warn)

        test_two = QLabel(Lng.copy_error[JsonData.lng_index])
        test_two.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        h_lay.addWidget(test_two)

        ok_btn = UPushButton(Lng.ok[JsonData.lng_index])
        ok_btn.clicked.connect(self.deleteLater)
        ok_btn.setFixedWidth(80)
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
    

class WinCopyFiles(WinProgressbar):
    finished_ = pyqtSignal(list)
    ms = 100

    def __init__(self, target_dir: str, files_to_copy: list[str]):
        super().__init__(Lng.copying[JsonData.lng_index])

        # # отладка
        # self.rel = ReplaceFilesWin()
        # self.er = ErrorWin()
        # self.rel.show()
        # self.er.show()
        # self.above_label.setText("above label above label above label")
        # self.below_label.setText("below label below label below label below label")
        # return

        self.cancel.connect(self.stop_task)
        self.cancel.connect(self.deleteLater)

        dst_text = os.path.basename(target_dir)
        if not dst_text:
            dst_text = Mf.current_mf.mf_alias
        self.above_label.setText(
            f"{Lng.copying[JsonData.lng_index]} {Lng.in_[JsonData.lng_index]} \"{dst_text}\""
        )

        self.dst_urls: list[str] = []

        self.copy_task_item = CopyTaskItem(
            dst_dir=target_dir,
            src_urls=files_to_copy,
            current_percent=0,
            copied_bytes=0,
            total_bytes=0,
            current_file_count=0,
            total_file_count=0,
            dst_urls=[],
            msg="none"
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

        self.progressbar.setMaximum(100)

    def poll_task(self):
        self.copy_timer.stop()
        finished = False

        if not self.copy_task.process_queue.empty():
            self.copy_item: CopyTaskItem = self.copy_task.process_queue.get()

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

            if len(self.dst_urls) == 0 and self.copy_item.dst_urls:
                self.dst_urls.extend(self.copy_item.dst_urls)

            self.progressbar.setValue(self.copy_item.current_percent)
            below_text = (
                self.windowTitle(),
                str(self.copy_item.current_file_count),
                Lng.from_[JsonData.lng_index],
                str(self.copy_item.total_file_count)
            )
            self.below_label.setText(" ".join(below_text))

        if not self.copy_task.is_alive() or finished:
            self.progressbar.setValue(self.progressbar.maximum())
            below_text = (
                self.windowTitle(),
                str(self.copy_item.total_file_count),
                Lng.from_[JsonData.lng_index],
                str(self.copy_item.total_file_count)
            )
            self.below_label.setText(" ".join(below_text))     
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
        self.copy_task.gui_queue.put(self.copy_item)
        self.replace_win.deleteLater()
        self.copy_timer.start(self.ms)

    def replace_all(self):
        self.copy_timer.stop()
        self.copy_item.msg = "replace_all"
        self.copy_task.gui_queue.put(self.copy_item)
        self.replace_win.deleteLater()
        self.copy_timer.start(self.ms)

    def stop_task(self):
        self.copy_timer.stop()
        self.copy_task.terminate_join()

    def closeEvent(self, a0):
        self.stop_task()
        return super().closeEvent(a0)