import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf
from widgets._base_widgets import UMainWindow


class PathWidget(QGroupBox):
    magnifier = "images/magnifier.svg"
    green_checkmark = "images/green_checkmark.svg"
    max_row = 45
    clicked = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.url = None
        self.setAcceptDrops(True)
        self.setFixedHeight(90)
    
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(2, 20, 2, 20)
        self.main_lay.setSpacing(0)

        self.main_wid = self.no_path_widget()
        self.main_lay.addWidget(self.main_wid)

    def no_path_widget(self):
        wid = QWidget()

        h_lay = QHBoxLayout(wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        h_lay.addStretch()

        right_btn = QSvgWidget()
        right_btn.load(self.magnifier)
        right_btn.setFixedSize(35, 35)
        h_lay.addWidget(right_btn)

        left_label = QLabel(Lng.path_hint_texts[Cfg.lng_index])
        left_label.setWordWrap(True)
        h_lay.addWidget(left_label)

        h_lay.addStretch()

        return wid
    
    def ok_path_widget(self):
        wid = QWidget()

        h_lay = QHBoxLayout(wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        h_lay.addStretch()

        right_btn = QSvgWidget()
        right_btn.load(self.green_checkmark)
        right_btn.setFixedSize(35, 35)
        h_lay.addWidget(right_btn)

        if len(self.url) > self.max_row * 2:
            url = self.url[:self.max_row*2] + "..."
        url = self.lined_text(self.url)

        left_label = QLabel(url)
        h_lay.addWidget(left_label)

        h_lay.addStretch()

        return wid

    def lined_text(self, text: str) -> str:
        if len(text) > self.max_row:
            return "\n".join(
                text[i:i + self.max_row]
                for i in range(0, len(text), self.max_row)
            )
        return text

    def mouseReleaseEvent(self, a0):
        dialog = QFileDialog()
        url = dialog.getExistingDirectory()
        if url:
            self.url = url
            self.clicked.emit(url)
            self.main_wid.deleteLater()
            self.main_wid = self.ok_path_widget()
            self.main_lay.addWidget(self.main_wid)
        return super().mouseReleaseEvent(a0)
    
    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
        
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if url and os.path.isdir(url):
                self.url = url
                self.clicked.emit(url)
                self.main_wid.deleteLater()
                self.main_wid = self.ok_path_widget()
                self.main_lay.addWidget(self.main_wid)

        return super().dropEvent(a0)
    

class WarnWidget(QWidget):
    warn = "images/warning.svg"
    def __init__(self):
        super().__init__()
        h_lay = QHBoxLayout(self)
        h_lay.setContentsMargins(2, 5, 2, 5)
        h_lay.setSpacing(10)

        warn_wid = QSvgWidget()
        warn_wid.load(self.warn)
        warn_wid.setFixedSize(30, 30)
        h_lay.addWidget(warn_wid)

        lines = (
            f"{Lng.access_error_text[Cfg.lng_index]} \"{Mf.current_mf.mf_alias}\".",
            Lng.network_error_text[Cfg.lng_index]
        )
        up_label = QLabel("\n".join(lines))
        up_label.setWordWrap(True)
        h_lay.addWidget(up_label)


class WinSmb(UMainWindow):
    clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.set_close_only()
        self.set_always_on_top()
        self.setWindowTitle(Lng.attention[Cfg.lng_index])
        self.url = ""
        self.central_layout.setContentsMargins(10, 10, 10, 5)
        self.central_layout.setSpacing(10)

        warn_widget = WarnWidget()
        self.central_layout.addWidget(warn_widget)

        self.path_widget = PathWidget()
        self.central_layout.addWidget(self.path_widget)

        btns_wid = QWidget()
        self.central_layout.addWidget(btns_wid)
        btns_lay = QHBoxLayout(btns_wid)
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)

        btns_lay.addStretch()
        ok_btn = QPushButton(Lng.ok[Cfg.lng_index])
        ok_btn.clicked.connect(self.ok_clicked)
        ok_btn.setFixedWidth(90)
        btns_lay.addWidget(ok_btn)
        cancel_btn = QPushButton(Lng.cancel[Cfg.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btns_lay.addWidget(cancel_btn)
        btns_lay.addStretch()

        self.adjustSize()

    def ok_clicked(self):
        if self.path_widget.url:
            self.clicked.emit(self.path_widget.url)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
