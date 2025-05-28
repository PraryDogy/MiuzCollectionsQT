import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import (QLabel, QProgressBar, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import LayoutHor, LayoutVer
from base_widgets.svg_btn import SvgBtn
from base_widgets.wins import WinSystem
from cfg import Static
from lang import Lang
from utils.copy_files import CopyFiles
from utils.utils import Utils

MAX_ROW = 45
SVG_SIZE = 16


class BaseDownloadsItem(QWidget):
    stop_btn_pressed = pyqtSignal()

    def __init__(self, files: list[str]):
        super().__init__()

        t = "\n".join(os.path.basename(i) for i in files)
        self.setToolTip(t)

        v_layout = LayoutVer()
        v_layout.setContentsMargins(10, 0, 20, 0)
        self.setLayout(v_layout)

        self.text_label = QLabel()
        v_layout.addWidget(self.text_label)

        copy_text = ", ".join([os.path.basename(i) for i in files])
        max_line = MAX_ROW
        if len(copy_text) > max_line:
            copy_text = copy_text[:max_line] + "..."
        self.text_label.setText(copy_text)

        v_layout.addSpacerItem(QSpacerItem(0, 10))

        h_wid = QWidget()
        v_layout.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.progress_bar.setFixedHeight(6)
        h_layout.addWidget(self.progress_bar)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        icon_path = os.path.join(Static.IMAGES, "clear.svg")
        self.stop_btn = SvgBtn(icon_path=icon_path, size=SVG_SIZE)
        self.stop_btn.mouseReleaseEvent = self.stop_cmd
        h_layout.addWidget(self.stop_btn)

        v_layout.addSpacerItem(QSpacerItem(0, 20))

    def stop_cmd(self, a0: QMouseEvent):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.stop_btn_pressed.emit()


class CurrentDownloadsItem(BaseDownloadsItem):
    def __init__(self, files: list[str]):
        super().__init__(files=files)
        self.progress_bar.setValue(0)


class OldDownloadsItem(BaseDownloadsItem):
    def __init__(self, files: list[str]):
        super().__init__(files=files)
        self.files = files
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #357227;
                border-radius: 3px;
            }
        """)

    def mouseReleaseEvent(self, a0):
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

        self.download_items: list[CopyFiles] = []

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

        # for i in range(0, 3):
        #     test = CurrentDownloadsItem([])
        #     test.progress_bar.setValue(50)
        #     self.progress_layout.addWidget(test)

        # for i in range(0, 3):
        #     test = OldDownloadsItem([])
        #     self.progress_layout.addWidget(test)

        self.add_progress_widgets()

    def add_progress_widgets(self):
        try:
            self.main_actions()
        except Exception as e:
            print("win downloads.py > add_progress_widgets error", e)

    def main_actions(self):

        for thread in CopyFiles.current_threads:

            if thread not in self.download_items:
                if not thread.is_finished():
                    item = CurrentDownloadsItem(thread.files)
                    one = lambda: self.remove_from_file_lists(download_item=thread)
                    item.stop_btn_pressed.connect(one)
                    item.stop_btn_pressed.connect(item.deleteLater)
                    thread.signals_.finished_.connect(one)
                    thread.signals_.finished_.connect(item.deleteLater)
                    thread.signals_.value_changed.connect(item.progress_bar.setValue)
                    self.progress_layout.addWidget(item)
                    self.download_items.append(thread)

        for files_list in CopyFiles.list_of_file_lists:
            if files_list not in self.download_items:
                item = OldDownloadsItem(files=files_list)
                one = lambda: self.remove_from_file_lists(download_item=files_list)
                item.stop_btn_pressed.connect(one)
                item.stop_btn_pressed.connect(item.deleteLater)
                self.progress_layout.addWidget(item)
                self.download_items.append(files_list)

        QTimer.singleShot(1000, self.add_progress_widgets)

    def remove_from_file_lists(self, download_item: list[str] | CopyFiles):
        try:
            self.download_items.remove(download_item)
            if isinstance(download_item, list):
                CopyFiles.list_of_file_lists.remove(download_item)
            elif isinstance(download_item, CopyFiles):
                download_item.signals_.stop.emit()
        except Exception:
            ...

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
            self.close()
        return super().keyPressEvent(a0)
    
    def closeEvent(self, a0):
        self.closed.emit()
        return super().closeEvent(a0)