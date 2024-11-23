import os
from functools import partial

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QLabel, QProgressBar, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import LayoutHor, LayoutVer
from base_widgets.wins import WinChild
from lang import Lang
from utils.copy_files import CopyFiles
from utils.utils import Utils


class CustomProgressBar(QProgressBar):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setTextVisible(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(7)


class Progresser(QWidget):
    set_value = pyqtSignal(int)
    set_text = pyqtSignal(str)
    progress_stop = pyqtSignal()

    def __init__(self, text: str):
        super().__init__()

        v_layout = LayoutVer()
        v_layout.setContentsMargins(10, 0, 20, 0)
        self.setLayout(v_layout)

        self.copy_label = QLabel(text=text, parent=self)
        v_layout.addWidget(self.copy_label)
        self.set_text.connect(self.set_text_label)

        v_layout.addSpacerItem(QSpacerItem(0, 10))

        h_wid = QWidget()
        v_layout.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)


        self.progress = CustomProgressBar(parent=self)
        self.progress.setValue(0)
        h_layout.addWidget(self.progress)
        self.set_value.connect(lambda v: self.progress.setValue(v))

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.close_btn = QLabel(text="x")
        self.close_btn.mouseReleaseEvent = self.close_cmd
        h_layout.addWidget(self.close_btn)

        v_layout.addSpacerItem(QSpacerItem(0, 20))

    def set_text_label(self, text: str):
        self.copy_label.setText(text)

    def close_cmd(self, e):
        self.progress_stop.emit()


class WinDownloads(WinChild):
    def __init__(self):
        super().__init__()
        self.content_lay_v.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle(Lang.title_downloads)
        self.setFixedSize(400, 420)

        self.copy_threads: list[CopyFiles] = []

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        self.v_layout = LayoutVer()
        self.scroll_widget.setLayout(self.v_layout)
        self.content_lay_v.addWidget(self.scroll_area)

        self.progress_wid = QWidget()
        self.progress_layout = LayoutVer()
        self.progress_wid.setLayout(self.progress_layout)
        self.v_layout.addWidget(self.progress_wid)
        self.v_layout.addStretch()

        # for i in range(0, 10):
            # wid_ = Progresser(text="test")
            # self.progress_layout.addWidget(wid_)
            # wid_.set_value.emit(50)

        self.add_progress_widgets()

    def add_progress_widgets(self):
        try:
            for copy_task in CopyFiles.current_threads:

                copy_task: CopyFiles

                if copy_task not in self.copy_threads and copy_task.is_running:
                    t = self.cut_text(copy_task.get_current_file())
                    copy_wid = Progresser(text=t)
                    self.progress_layout.addWidget(copy_wid)

                    self.copy_threads.append(copy_task)
                    self.connect_(copy_wid, copy_task)

            QTimer.singleShot(1000, self.add_progress_widgets)

        except Exception as e:
            Utils.print_err(error=e)

    def connect_(self, wid: Progresser, task: CopyFiles):
        wid.progress_stop.connect(partial(self.stop_progress, wid, task))
        task.signals_.value_changed.connect(partial(self.change_progress_value, wid))
        task.signals_.text_changed.connect(partial(self.change_progress_text, wid))
        task.signals_.finished_.connect(partial(self.remove_progress, wid, task))

    def stop_progress(self, widget: Progresser, task: CopyFiles):
        task.signals_.stop.emit()
        self.remove_progress(widget, task)

    def remove_progress(self, widget: Progresser, task: CopyFiles):
        try:
            widget.deleteLater()
            self.copy_threads.remove(task)
        except Exception as e:
            Utils.print_err(error=e)
    
    def change_progress_text(self, widget: Progresser, text: str):
        text = self.cut_text(text)

        try:
            widget.set_text.emit(text)
        except Exception as e:
            # MainUtils.print_err(error=e)
            pass

    def change_progress_value(self, widget: Progresser, value: int):
        try:
            widget.set_value.emit(value)
        except Exception as e:
            # MainUtils.print_err(error=e)
            pass

    def cut_text(self, text: str):
        name, ext = os.path.splitext(text)
        name = f"{Lang.copying} {name}"
        max_row = 27

        if len(name) >= max_row:
            cut_name = name[:max_row]
            cut_name = cut_name[:-6]
            name = cut_name + "..." + name[-3:] + ext
        else:
            name = name + ext

        return name

    def set_value(self, value: int):
        try:
            self.progress.setValue(value)
        except (Exception, RuntimeError) as e:
            Utils.print_err(error=e)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
            self.close()
        return super().keyPressEvent(a0)