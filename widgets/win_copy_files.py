import os
from queue import Empty

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import CopyTask, CopyTaskItem, CopyTaskWorker

from ._base_widgets import (ActiveButton, TransparentLabel, TransparentWidget,
                            UCheckBox, UPushButton, VerticalWindow,
                            WarningWindow, WinProgressbar)


class ReplaceWin(VerticalWindow):
    replace_pressed = pyqtSignal()
    skip_pressed = pyqtSignal()
    cancel_pressed = pyqtSignal()
    keep_both = pyqtSignal()

    warn_svg = Static.COMMON_ICONS / "yellow_warning.svg"
    warn_svg_size = (65, 65)

    def __init__(self, filename: str, show_checkbox: bool):
        super().__init__()

        self.filename = filename
        self.show_checkbox = show_checkbox

        self.setWindowTitle(Lng.replace)
        self.set_close_only()
        self.set_always_on_top()
        self.show_titlebar_sep()

        self._init_ui()
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

    def _init_ui(self):
        icon = QSvgWidget()
        icon.load(str(self.warn_svg))
        icon.setFixedSize(*self.warn_svg_size)

        self.icon_text_layout.addWidget(
            icon,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        message = TransparentLabel(
            Lng.file_exists
        )
        self.icon_text_layout.addWidget(message)

        self.filename_label = TransparentLabel(self.filename)
        self.filename_label.setFixedWidth(message.sizeHint().width())
        self.filename_label.set_elide(True)
        self.icon_text_layout.addWidget(self.filename_label)

        self.icon_text_layout.addSpacing(5)

        self.replace_all_checkbox = UCheckBox(
            Lng.apply_to_all_files
        )
        self.replace_all_checkbox.clicked.connect(
            self._checkbox_clicked
        )
        self.replace_all_checkbox.setChecked(False)

        if self.show_checkbox:
            self.icon_text_layout.addWidget(
                self.replace_all_checkbox
            )

        self.actions_widget = TransparentWidget()
        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(5)

        self.replace_button = ActiveButton(
            Lng.replace
        )
        self.replace_button.clicked.connect(self._replace)
        self.actions_layout.addWidget(self.replace_button)

        self.keep_both_button = UPushButton(
            Lng.keep_both
        )
        self.keep_both_button.clicked.connect(self._keep_both)
        self.actions_layout.addWidget(self.keep_both_button)

        self.btn_layout.addWidget(self.actions_widget)

        self.skip_button = UPushButton(
            Lng.skip
        )
        self.skip_button.clicked.connect(self._skip)
        self.btn_layout.addWidget(self.skip_button)

        self.cancel_button = UPushButton(
            Lng.cancel
        )
        self.cancel_button.clicked.connect(self._cancel)
        self.btn_layout.addWidget(self.cancel_button)

    def _checkbox_clicked(self):
        if self.replace_all_checkbox.isChecked():
            self.replace_button.setText(
                Lng.replace_all
            )
            self.keep_both_button.setText(
                Lng.keep_all
            )
        else:
            self.replace_button.setText(
                Lng.replace
            )
            self.keep_both_button.setText(
                Lng.keep_both
            )

    def _keep_both(self):
        self.keep_both.emit()

    def _replace(self):
        self.replace_pressed.emit()

    def _skip(self):
        self.skip_pressed.emit()

    def _cancel(self):
        self.cancel_pressed.emit()

    def is_replace_all(self) -> bool:
        return self.replace_all_checkbox.isChecked()

    def closeEvent(self, event):
        self.cancel_pressed.emit()
        event.accept()


class WinCopyFiles(WinProgressbar):
    finished_ = pyqtSignal(list)
    ms = 100

    def __init__(
        self,
        target_dir: str,
        files_to_copy: list[str],
    ):
        super().__init__(Lng.copying)

        self.set_close_only()
        self.adjustSize()
        self.setFixedHeight(self.height())

        self.target_dir = target_dir
        self.files_to_copy = files_to_copy
        self.dst_urls: list[str] = []

        self.copy_item: CopyTaskItem | None = None
        self.replace_win: ReplaceWin | None = None
        self.stopping = False

        dst_text = os.path.basename(target_dir)
        if not dst_text:
            dst_text = Mf.current_mf.mf_alias

        self.above_label.setText(
            f'{Lng.copying} '
            f'{Lng.in_} "{dst_text}"'
        )
        self.below_label.setText(
            Lng.preparing
        )

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
        self.copy_timer.timeout.connect(self.poll_task)

        self.progressbar.setMaximum(100)

        self.copy_task.start()
        self.copy_timer.start(self.ms)

    def poll_task(self):
        if self.stopping:
            return

        while True:
            try:
                copy_item: CopyTaskItem = (
                    self.copy_task.process_queue.get_nowait()
                )
            except Empty:
                break

            self.copy_item = copy_item

            if copy_item.dst_urls:
                self.dst_urls = list(copy_item.dst_urls)

            if copy_item.msg == "error":
                self.show_error(copy_item.error_traceback)
                return

            if copy_item.msg == "need_replace":
                self.show_replace_window(copy_item)
                return

            if copy_item.msg == "finished":
                self.finish_task()
                return

            self.update_progress(copy_item)

        if not self.copy_task.is_alive():
            self.finish_task()
            return

        self.copy_timer.start(self.ms)

    def update_progress(self, copy_item: CopyTaskItem):
        self.progressbar.setValue(copy_item.current_percent)

        below_text = (
            self.windowTitle(),
            str(copy_item.current_file_count),
            Lng.from_,
            str(copy_item.total_file_count),
        )
        self.below_label.setText(" ".join(below_text))

    def show_replace_window(self, copy_item: CopyTaskItem):
        if self.stopping:
            return

        index = copy_item.current_file_count - 1
        filename = ""

        if 0 <= index < len(copy_item.src_urls):
            filename = os.path.basename(
                copy_item.src_urls[index]
            )

        self.replace_win = ReplaceWin(
            filename,
            len(copy_item.src_urls) > 1,
        )
        self.replace_win.center_to_parent(self)

        self.replace_win.replace_pressed.connect(
            self.replace_file
        )
        self.replace_win.keep_both.connect(
            self.keep_both_file
        )
        self.replace_win.skip_pressed.connect(
            self.skip_file
        )
        self.replace_win.cancel_pressed.connect(
            self.cancel_from_replace
        )

        self.replace_win.show()

    def replace_file(self):
        if self.stopping or self.replace_win is None:
            return

        replace_all = self.replace_win.is_replace_all()

        self.close_replace_window()

        if replace_all:
            self.copy_task.replace_all()
        else:
            self.copy_task.replace_one()

        self.copy_timer.start(self.ms)

    def keep_both_file(self):
        if self.stopping or self.replace_win is None:
            return

        keep_all = self.replace_win.is_replace_all()

        self.close_replace_window()

        if keep_all:
            self.copy_task.keep_all()
        else:
            self.copy_task.keep_both()

        self.copy_timer.start(self.ms)

    def skip_file(self):
        if self.stopping or self.replace_win is None:
            return

        self.close_replace_window()
        self.copy_task.skip()
        self.copy_timer.start(self.ms)

    def cancel_from_replace(self):
        if self.stopping:
            return

        self.close_replace_window()
        self.stop_task()
        self.deleteLater()

    def close_replace_window(self):
        if self.replace_win is None:
            return

        window = self.replace_win
        self.replace_win = None

        window.blockSignals(True)
        window.close()
        window.deleteLater()

        QTimer.singleShot(50, self.raise_)

    def show_error(self, traceback_text: str):
        if self.stopping:
            return

        self.close_replace_window()

        self.error_win = WarningWindow(
            Lng.copy_error,
            traceback_text,
        )
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
                Lng.from_,
                str(self.copy_item.total_file_count),
            )
            self.below_label.setText(" ".join(below_text))

        self.finished_.emit(self.dst_urls)

        self.stop_task()
        self.deleteLater()

    def stop_task(self):
        if self.stopping:
            return

        self.stopping = True
        self.copy_timer.stop()

        self.close_replace_window()

        if self.copy_task.is_alive():
            self.copy_task.cancel()

        self.copy_task.terminate_join()

    def closeEvent(self, event):
        self.stop_task()
        super().closeEvent(event)