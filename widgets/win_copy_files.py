import os
from queue import Empty

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import CopyTask, CopyTaskItem, CopyTaskWorker

from ._base_widgets import (ActiveButton, TransparentLabel, TransparentWidget,
                            UMainWidget, UPushButton, WarningWindow,
                            WinProgressbar, UCheckBox)


class ReplaceFilesWin(UMainWidget):
    icon_size = 25
    ww = 330
    icon_path = Static.COMMON_ICONS / "yellow_warning.svg"

    replace_one_press = pyqtSignal()
    replace_all_press = pyqtSignal()
    stop_pressed = pyqtSignal()

    def __init__(self, filename_: str):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.replace[JsonData.lng_index])
        # self.setFixedWidth(self.ww)
        self.central_layout.setContentsMargins(10, 0, 10, 10)
        self.central_layout.setSpacing(10)

        self.warn_text_widget = TransparentWidget()
        self.central_layout.addWidget(self.warn_text_widget)
        self.warn_text_layout = QHBoxLayout(self.warn_text_widget)
        self.warn_text_layout.setContentsMargins(0, 0, 0, 0)
        self.warn_text_layout.setSpacing(10)

        self.warn_svg_widget = QSvgWidget()
        self.warn_svg_widget.load(str(self.icon_path))
        self.warn_svg_widget.setFixedSize(self.icon_size, self.icon_size)
        self.warn_text_layout.addWidget(self.warn_svg_widget)

        text = Lng.file_exists[JsonData.lng_index].format(filename=filename_)
        self.warn_text_widget = TransparentLabel(text)
        self.warn_text_layout.addWidget(self.warn_text_widget)


        btn_wid = TransparentWidget()
        self.central_layout.addWidget(btn_wid)

        btn_lay = QHBoxLayout(btn_wid)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(5)

        self.checkbox_widget = UCheckBox(Lng.replace_all[JsonData.lng_index])
        # self.checkbox_widget.setText(Lng.replace_all[JsonData.lng_index])
        btn_lay.addWidget(self.checkbox_widget)

        btn_lay.addSpacing(25)
        btn_lay.addStretch()

        stop_btn = UPushButton(Lng.cancel[JsonData.lng_index])
        stop_btn.clicked.connect(lambda: self.stop_cmd())
        btn_lay.addWidget(stop_btn)

        skip_btn = UPushButton(Lng.skip[JsonData.lng_index])
        # skip_btn.clicked.connect(lambda: self.stop_cmd())
        btn_lay.addWidget(skip_btn)

        replace_one_btn = ActiveButton(Lng.replace_one[JsonData.lng_index])
        replace_one_btn.clicked.connect(lambda: self.replace_one_cmd())
        btn_lay.addWidget(replace_one_btn)

        for i in (stop_btn, skip_btn, replace_one_btn, self.checkbox_widget):
            i.setFixedHeight(22)
            i.ensurePolished()
        
        self.adjustSize()

    def replace_one_cmd(self):
        self.replace_one_press.emit()

    def replace_all_cmd(self):
        self.replace_all_press.emit()

    def stop_cmd(self):
        self.stop_pressed.emit()

    def closeEvent(self, a0):
        self.stop_cmd()
        return super().closeEvent(a0)

    def deleteLater(self):
        self.stop_cmd
        return super().deleteLater()
    

class WinCopyFiles(WinProgressbar):
    finished_ = pyqtSignal(list)

    ms = 100

    def __init__(
        self,
        target_dir: str,
        files_to_copy: list[str],
    ):
        super().__init__(
            Lng.copying[JsonData.lng_index]
        )

        self.set_close_only()

        # отладка окон
        QTimer.singleShot(300, self.TEST)
        return


        dst_text = os.path.basename(target_dir)

        if not dst_text:
            dst_text = Mf.current_mf.mf_alias

        self.above_label.setText(
            f'{Lng.copying[JsonData.lng_index]} '
            f'{Lng.in_[JsonData.lng_index]} '
            f'"{dst_text}"'
        )

        self.below_label.setText(
            Lng.preparing[JsonData.lng_index]
        )

        self.dst_urls: list[str] = []
        self.copy_item: CopyTaskItem | None = None
        self.stopping = False

        self.copy_item = CopyTaskItem(
            dst_dir=target_dir,
            src_urls=files_to_copy,
            current_percent=0,
            copied_bytes=0,
            total_bytes=0,
            current_file_count=0,
            total_file_count=0,
            dst_urls=[],
            msg="none",
        )

        self.copy_task = CopyTaskWorker(
            target=CopyTask.start,
            args=(self.copy_item,),
        )

        self.copy_timer = QTimer(self)
        self.copy_timer.setSingleShot(True)
        self.copy_timer.timeout.connect(
            self.poll_task
        )

        self.progressbar.setMaximum(100)

        self.copy_task.start()
        self.copy_timer.start(self.ms)


    def TEST(self):
        # отладка
        self.progressbar.setValue(50)

        self.above_label.setText("above label above label above label")
        self.below_label.setText("below label below label below label below label")

        self.rel = ReplaceFilesWin(filename_="test.jpg")
        self.rel.stop_pressed.connect(lambda: os._exit(1))
        self.rel.show()

        # self.er = WarningWindow(Lng.copy_error[JsonData.lng_index])
        # self.er.show()

        # self.cancel.connect(self.stop_task)
        # self.cancel.connect(self.deleteLater)

    def poll_task(self):
        if self.stopping:
            return

        while True:
            try:
                copy_item = (
                    self.copy_task.process_queue.get_nowait()
                )
            except Empty:
                break

            self.copy_item = copy_item

            if copy_item.dst_urls:
                self.dst_urls = list(
                    copy_item.dst_urls
                )

            if copy_item.msg == "error":
                self.show_error()
                return

            if copy_item.msg == "need_replace":
                self.show_replace_window()
                return

            if copy_item.msg == "finished":
                self.finish_task()
                return

            self.update_progress(copy_item)

        if not self.copy_task.is_alive():
            self.finish_task()
            return

        self.copy_timer.start(self.ms)

    def update_progress(
        self,
        copy_item: CopyTaskItem,
    ):
        self.progressbar.setValue(
            copy_item.current_percent
        )

        below_text = (
            self.windowTitle(),
            str(copy_item.current_file_count),
            Lng.from_[JsonData.lng_index],
            str(copy_item.total_file_count),
        )

        self.below_label.setText(
            " ".join(below_text)
        )

    def show_replace_window(self):
        self.replace_win = ReplaceFilesWin()

        self.replace_win.center_to_parent(self)

        self.replace_win.replace_all_press.connect(
            self.replace_all
        )

        self.replace_win.replace_one_press.connect(
            self.replace_one
        )

        self.replace_win.stop_pressed.connect(
            self.stop_pressed
        )

        self.replace_win.show()

    def replace_one(self):
        if self.stopping:
            return

        self.replace_win.deleteLater()

        self.copy_task.replace_one()

        self.copy_timer.start(self.ms)

    def replace_all(self):
        if self.stopping:
            return

        self.replace_win.deleteLater()

        self.copy_task.replace_all()

        self.copy_timer.start(self.ms)

    def stop_pressed(self):
        if hasattr(self, "replace_win"):
            self.replace_win.deleteLater()

        self.stop_task()
        self.deleteLater()

    def show_error(self):
        self.error_win = WarningWindow(Lng.copy_error[JsonData.lng_index])
        self.error_win.center_to_parent(self.window())
        self.error_win.show()

        self.stop_task()
        self.deleteLater()

    def finish_task(self):
        if self.stopping:
            return

        self.progressbar.setValue(
            self.progressbar.maximum()
        )

        if self.copy_item:
            below_text = (
                self.windowTitle(),
                str(self.copy_item.total_file_count),
                Lng.from_[JsonData.lng_index],
                str(self.copy_item.total_file_count),
            )

            self.below_label.setText(
                " ".join(below_text)
            )

        self.finished_.emit(self.dst_urls)

        self.stop_task()
        self.deleteLater()

    def stop_task(self):
        if self.stopping:
            return

        self.stopping = True
        self.copy_timer.stop()

        if self.copy_task.is_alive():
            self.copy_task.cancel()

        self.copy_task.terminate_join()

    def closeEvent(self, event):
        self.stop_task()
        super().closeEvent(event)
