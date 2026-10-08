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
                            WinProgressbar, UCheckBox, GrayTextLabel)


from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout


from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QSizePolicy


class ElidedLabel(GrayTextLabel):
    def __init__(self):
        super().__init__(text="")

        self._full_text = ""

        self.setWordWrap(False)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

    def setFullText(self, text: str):
        self._full_text = text
        self.setToolTip(text)
        self._update_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_text()

    def _update_text(self):
        if not self._full_text:
            super().setText("")
            return

        width = self.contentsRect().width()

        if width <= 0:
            return

        metrics = QFontMetrics(self.font())

        text = metrics.elidedText(
            self._full_text,
            Qt.TextElideMode.ElideMiddle,
            width,
        )

        super().setText(text)


class ReplaceWin(UMainWidget):
    replace_pressed = pyqtSignal()
    skip_pressed = pyqtSignal()
    cancel_pressed = pyqtSignal()

    warn_svg = Static.COMMON_ICONS / "yellow_warning.svg"
    warn_svg_size = (45, 45)
    ww = 360

    def __init__(self, filename: str, parent=None):
        super().__init__(parent)

        self.filename = filename

        self.setWindowTitle(
            Lng.replace[JsonData.lng_index]
        )

        self.central_layout.setContentsMargins(
            10, 5, 10, 5
        )
        self.central_layout.setSpacing(5)

        self._init_ui()
        self.set_close_only()
        self.setFixedWidth(self.ww)
        self.adjustSize()
        self.setFixedHeight(self.height())

    def _init_ui(self):
        # =========================================================
        # Верхняя часть: иконка + текст
        # =========================================================

        icon_widget = TransparentWidget()
        self.central_layout.addWidget(icon_widget)

        icon_layout = QHBoxLayout(icon_widget)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(10)

        # ---------------------------------------------------------
        # Warning icon
        # ---------------------------------------------------------

        icon = QSvgWidget()
        icon.load(str(self.warn_svg))
        icon.setFixedSize(*self.warn_svg_size)

        icon_layout.addWidget(
            icon,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        # ---------------------------------------------------------
        # Text
        # ---------------------------------------------------------

        text_widget = TransparentWidget()
        text_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        icon_layout.addWidget(
            text_widget,
            1,
        )

        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        # ---------------------------------------------------------
        # Filename
        # ---------------------------------------------------------

        self.filename_label = ElidedLabel()

        self.filename_label.setFullText(
            self.filename
        )

        text_layout.addWidget(
            self.filename_label
        )

        # ---------------------------------------------------------
        # Message
        # ---------------------------------------------------------

        message = GrayTextLabel(
            Lng.file_exists[JsonData.lng_index]
        )

        message.setWordWrap(False)

        text_layout.addWidget(
            message
        )

        # =========================================================
        # Buttons
        # =========================================================

        btns_widget = TransparentWidget()
        self.central_layout.addWidget(btns_widget)

        buttons_layout = QHBoxLayout(btns_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # ---------------------------------------------------------
        # Replace all
        # ---------------------------------------------------------

        self.replace_all_checkbox = UCheckBox(
            Lng.replace_all[JsonData.lng_index]
        )

        self.replace_all_checkbox.setChecked(False)

        buttons_layout.addWidget(
            self.replace_all_checkbox
        )

        buttons_layout.addStretch(1)
        buttons_layout.addSpacing(20)

        # ---------------------------------------------------------
        # Cancel
        # ---------------------------------------------------------

        self.cancel_button = UPushButton(
            Lng.cancel[JsonData.lng_index]
        )

        self.cancel_button.clicked.connect(
            self._cancel
        )

        buttons_layout.addWidget(
            self.cancel_button
        )

        # ---------------------------------------------------------
        # Skip
        # ---------------------------------------------------------

        self.skip_button = UPushButton(
            Lng.skip[JsonData.lng_index]
        )

        self.skip_button.clicked.connect(
            self._skip
        )

        buttons_layout.addWidget(
            self.skip_button
        )

        # ---------------------------------------------------------
        # Replace
        # ---------------------------------------------------------

        self.replace_button = ActiveButton(
            Lng.replace[JsonData.lng_index]
        )

        self.replace_button.clicked.connect(
            self._replace
        )

        buttons_layout.addWidget(
            self.replace_button
        )

        # ---------------------------------------------------------
        # Button size
        # ---------------------------------------------------------

        for button in (
            self.cancel_button,
            self.skip_button,
            self.replace_button,
        ):
            button.setFixedHeight(23)

    # =============================================================
    # Actions
    # =============================================================

    def _replace(self):
        self.replace_pressed.emit()

    def _skip(self):
        self.skip_pressed.emit()

    def _cancel(self):
        self.cancel_pressed.emit()

    # =============================================================
    # Public API
    # =============================================================

    def is_replace_all(self) -> bool:
        return self.replace_all_checkbox.isChecked()

    # =============================================================
    # Window events
    # =============================================================

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
        super().__init__(
            Lng.copying[JsonData.lng_index]
        )

        self.set_close_only()

        self.target_dir = target_dir
        self.files_to_copy = files_to_copy

        self.dst_urls: list[str] = []

        self.copy_item: CopyTaskItem | None = None
        self.replace_win: ReplaceWin | None = None

        self.stopping = False

        # --------------------------------------------------
        # Labels
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Copy item
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Worker
        # --------------------------------------------------

        self.copy_task = CopyTaskWorker(
            target=CopyTask.start,
            args=(self.copy_item,),
        )

        # --------------------------------------------------
        # Timer
        # --------------------------------------------------

        self.copy_timer = QTimer(self)
        self.copy_timer.setSingleShot(True)
        self.copy_timer.timeout.connect(
            self.poll_task
        )

        self.progressbar.setMaximum(100)

        # --------------------------------------------------
        # Start
        # --------------------------------------------------

        self.copy_task.start()
        self.copy_timer.start(self.ms)

    # ======================================================
    # Queue
    # ======================================================

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
                self.show_replace_window(
                    copy_item
                )
                return

            if copy_item.msg == "finished":
                self.finish_task()
                return

            self.update_progress(copy_item)

        if not self.copy_task.is_alive():
            self.finish_task()
            return

        self.copy_timer.start(self.ms)

    # ======================================================
    # Progress
    # ======================================================

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

    # ======================================================
    # Replace window
    # ======================================================

    def show_replace_window(
        self,
        copy_item: CopyTaskItem,
    ):
        if self.stopping:
            return

        filename = ""

        index = (
            copy_item.current_file_count - 1
        )

        if 0 <= index < len(copy_item.src_urls):
            filename = os.path.basename(
                copy_item.src_urls[index]
            )

        self.replace_win = ReplaceWin(
            filename=filename
        )

        self.replace_win.center_to_parent(self)

        self.replace_win.replace_pressed.connect(
            self.replace_file
        )

        self.replace_win.skip_pressed.connect(
            self.skip_file
        )

        self.replace_win.cancel_pressed.connect(
            self.cancel_from_replace
        )

        self.replace_win.show()

    # ======================================================
    # Replace
    # ======================================================

    def replace_file(self):
        if self.stopping:
            return

        replace_all = (
            self.replace_win
            and self.replace_win.replace_all_checkbox.isChecked()
        )

        self.close_replace_window()

        if replace_all:
            self.copy_task.replace_all()
        else:
            self.copy_task.replace_one()

        self.copy_timer.start(self.ms)

    # ======================================================
    # Skip
    # ======================================================

    def skip_file(self):
        if self.stopping:
            return

        self.close_replace_window()

        self.copy_task.skip()

        self.copy_timer.start(self.ms)

    # ======================================================
    # Cancel
    # ======================================================

    def cancel_from_replace(self):
        if self.stopping:
            return

        self.close_replace_window()

        self.stop_task()
        self.deleteLater()

    # ======================================================
    # Close ReplaceWin
    # ======================================================

    def close_replace_window(self):
        if self.replace_win is None:
            return

        self.replace_win.blockSignals(True)
        self.replace_win.close()
        self.replace_win.deleteLater()
        self.replace_win = None

    # ======================================================
    # Error
    # ======================================================

    def show_error(self):
        if self.stopping:
            return

        self.close_replace_window()

        self.error_win = WarningWindow(
            Lng.copy_error[JsonData.lng_index]
        )

        self.error_win.center_to_parent(
            self.window()
        )

        self.error_win.show()

        self.stop_task()
        self.deleteLater()

    # ======================================================
    # Finish
    # ======================================================

    def finish_task(self):
        if self.stopping:
            return

        self.progressbar.setValue(
            self.progressbar.maximum()
        )

        if self.copy_item:
            below_text = (
                self.windowTitle(),
                str(
                    self.copy_item.total_file_count
                ),
                Lng.from_[JsonData.lng_index],
                str(
                    self.copy_item.total_file_count
                ),
            )

            self.below_label.setText(
                " ".join(below_text)
            )

        self.finished_.emit(
            self.dst_urls
        )

        self.stop_task()
        self.deleteLater()

    # ======================================================
    # Stop
    # ======================================================

    def stop_task(self):
        if self.stopping:
            return

        self.stopping = True

        self.copy_timer.stop()

        if self.replace_win is not None:
            self.replace_win.blockSignals(True)
            self.replace_win.close()
            self.replace_win.deleteLater()
            self.replace_win = None

        if self.copy_task.is_alive():
            self.copy_task.cancel()

        self.copy_task.terminate_join()

    # ======================================================
    # Close
    # ======================================================

    def closeEvent(self, event):
        self.stop_task()
        super().closeEvent(event)