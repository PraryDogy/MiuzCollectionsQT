import os
from functools import partial

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import (QLabel, QProgressBar, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import LayoutHor, LayoutVer
from base_widgets.wins import WinSystem
from lang import Lang
from utils.copy_files import CopyFiles
from utils.utils import Utils

MAX_ROW = 45


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


class OldProgresser(QWidget):
    remove_pressed = pyqtSignal()

    def __init__(self, files: list[str]):
        super().__init__()
        self.files = files

        v_layout = LayoutVer()
        v_layout.setContentsMargins(10, 0, 20, 0)
        self.setLayout(v_layout)

        copy_text = ", ".join([os.path.basename(i) for i in files])
        max_line = MAX_ROW
        if len(copy_text) > max_line:
            copy_text = copy_text[:max_line] + "..."

        self.copy_label = QLabel(text=copy_text, parent=self)
        self.copy_label.mouseReleaseEvent = self.reveal_cmd
        v_layout.addWidget(self.copy_label)

        v_layout.addSpacerItem(QSpacerItem(0, 10))

        h_wid = QWidget()
        v_layout.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)

        self.progress = CustomProgressBar(parent=self)
        self.progress.mouseReleaseEvent = self.reveal_cmd
        self.progress.setValue(100)
        h_layout.addWidget(self.progress)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.close_btn = QLabel(text="x")
        self.close_btn.mouseReleaseEvent = self.remove_cmd
        h_layout.addWidget(self.close_btn)

        v_layout.addSpacerItem(QSpacerItem(0, 20))

    def remove_cmd(self, a0: QMouseEvent):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.remove_pressed.emit()

    def reveal_cmd(self, a0: QMouseEvent):
        if a0.button() == Qt.MouseButton.LeftButton:
            Utils.reveal_files(files_list=self.files)
        return super().mouseReleaseEvent(a0)


class WinDownloads(WinSystem):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle(Lang.title_downloads)
        self.setFixedSize(400, 420)

        self.copy_files_list: list[CopyFiles] = []

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        self.v_layout = LayoutVer()
        self.v_layout.setContentsMargins(0, 10, 0, 10)
        self.scroll_widget.setLayout(self.v_layout)
        self.central_layout.addWidget(self.scroll_area)

        self.progress_wid = QWidget()
        self.progress_layout = LayoutVer()
        self.progress_wid.setLayout(self.progress_layout)
        self.v_layout.addWidget(self.progress_wid)
        self.v_layout.addStretch()

        for i in range(0, 2):
            wid_ = Progresser(text="test")
            self.progress_layout.addWidget(wid_)
            wid_.set_value.emit(50)

        self.add_progress_widgets()

    def add_progress_widgets(self):
        try:
            for copy_files in CopyFiles.current_threads:

                assert isinstance(copy_files, CopyFiles)

                if copy_files not in self.copy_files_list:
                    if copy_files.is_running:
                        t = self.cut_text(copy_files.get_current_file())
                        copy_wid = Progresser(text=t)
                        self.progress_layout.addWidget(copy_wid)

                        self.copy_files_list.append(copy_files)
                        self.connect_(copy_wid, copy_files)

                    else:
                        ...

            for files_list in CopyFiles.old_threads:
                if files_list not in self.copy_files_list:
                    old_ = OldProgresser(files_list)
                    cmd = lambda: self.remove_old_copy_files(old_, files_list)
                    old_.remove_pressed.connect(cmd)
                    self.progress_layout.addWidget(old_)
                    self.copy_files_list.append(files_list)

            QTimer.singleShot(1000, self.add_progress_widgets)

        except Exception as e:
            Utils.print_err(error=e)

    def remove_old_copy_files(self, wid: OldProgresser, files_list: list[str]):
        CopyFiles.old_threads.remove(files_list)
        wid.deleteLater()

    def connect_(self, wid: Progresser, task: CopyFiles):
        wid.progress_stop.connect(partial(self.stop_progress, wid, task))
        task.signals_.value_changed.connect(partial(self.change_progress_value, wid))
        task.signals_.text_changed.connect(partial(self.change_progress_text, wid))

    def stop_progress(self, widget: Progresser, task: CopyFiles):
        task.signals_.stop.emit()
        self.remove_progress(widget, task)

    def remove_progress(self, widget: Progresser, task: CopyFiles):
        try:
            widget.deleteLater()
            self.copy_files_list.remove(task)
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

        if len(name) >= MAX_ROW:
            cut_name = name[:MAX_ROW]
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
    
    def closeEvent(self, a0):
        self.closed.emit()
        return super().closeEvent(a0)