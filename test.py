from functools import partial

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QLabel, QProgressBar, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import Btn, LayoutV, WinStandartBase
from cfg import cnf
from styles import Names, Themes
from utils import MainUtils
from utils.copy_files import ThreadCopyFiles
import os

class Progresser(QWidget):
    set_value = pyqtSignal(int)
    set_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        v_layout = LayoutV()
        v_layout.setContentsMargins(10, 0, 20, 0)
        self.setLayout(v_layout)

        self.copy_label = QLabel(text=cnf.lng.copying_files, parent=self)
        self.copy_label.setFixedHeight(20)
        v_layout.addWidget(self.copy_label)
        self.set_text.connect(self.set_text_label)

        v_layout.addSpacerItem(QSpacerItem(0, 10))

        self.progress = QProgressBar(parent=self)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        v_layout.addWidget(self.progress)
        self.set_value.connect(lambda v: self.progress.setValue(v))

        v_layout.addSpacerItem(QSpacerItem(0, 10))

        self.cancel_btn = Btn(text=cnf.lng.cancel)
        # v_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def set_text_label(self, text: str):
        self.copy_label.setText(text)


class DownloadsWin(WinStandartBase):
    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.my_close)
        self.copy_threads: list = []

        self.set_title(cnf.lng.title_downloads)
        self.disable_min()
        self.disable_max()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(400, 420)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName(Names.th_scrollbar)
        self.scroll_area.setStyleSheet(Themes.current)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName(Names.th_scroll_widget)
        self.scroll_widget.setStyleSheet(Themes.current)
        self.scroll_area.setWidget(self.scroll_widget)

        self.v_layout = LayoutV()
        self.scroll_widget.setLayout(self.v_layout)
        self.content_layout.addWidget(self.scroll_area)

        self.progress_wid = QWidget()
        self.progress_layout = LayoutV()
        self.progress_wid.setLayout(self.progress_layout)
        self.v_layout.addWidget(self.progress_wid)
        self.v_layout.addStretch()

        self.add_progress_widgets()

    def add_progress_widgets(self):
        for copy_task in cnf.copy_threads:

            if copy_task not in self.copy_threads:
                progress = Progresser()
                self.progress_layout.addWidget(progress)

                copy_task: ThreadCopyFiles
                self.copy_threads.append(copy_task)

                copy_task.value_changed.connect(partial(self.change_progress_value, progress))
                copy_task.text_changed.connect(partial(self.change_progress_text, progress))
                copy_task.finished.connect(partial(self.remove_progress, progress, copy_task))

        QTimer.singleShot(1000, self.add_progress_widgets)

    def remove_progress(self, widget: Progresser, task: ThreadCopyFiles):
        QTimer.singleShot(1000, widget.deleteLater)
        self.copy_threads.remove(task)
    
    def change_progress_text(self, widget: Progresser, text: str):
        text = self.cut_text(text)

        try:
            widget.set_text.emit(text)
        except Exception as e:
            # MainUtils.print_err(parent=self, error=e)
            pass

    def change_progress_value(self, widget: Progresser, value: int):
        try:
            widget.set_value.emit(value)
        except Exception as e:
            # MainUtils.print_err(parent=self, error=e)
            pass

    def cut_text(self, text: str):
        name, ext = os.path.splitext(text)
        name = f"{cnf.lng.copying} {name}"
        max_row = 27

        if len(name) >= max_row:
            cut_name = name[:max_row]
            cut_name = cut_name[:-6]
            name = cut_name + "..." + name[-3:] + ext
        else:
            name = name + ext

        return name

    def my_close(self, event):
        self.close()
        return

    def set_value(self, value: int):
        try:
            self.progress.setValue(value)
        except (Exception, RuntimeError) as e:
            MainUtils.print_err(parent=self, error=e)
