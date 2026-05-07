from PyQt5.QtCore import pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QVBoxLayout, QWidget, QGroupBox)

from widgets._base_widgets import UMainWindow
import os
import sys


class PathWidget(QGroupBox):
    magnifier = "images/magnifier.svg"
    green_checkmark = "images/green_checkmark.svg"
    clicked = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.url = None
    
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

        lines = (
            "Перетяните сюда каталог изображений",
            "или нажмите, чтобы указать путь к каталогу."
        )
        left_label = QLabel("\n".join(lines))
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

        left_label = QLabel(self.url)
        left_label.setWordWrap(True)
        h_lay.addWidget(left_label)

        h_lay.addStretch()

        return wid

    def mouseReleaseEvent(self, a0):
        url = QFileDialog.getExistingDirectory(
            caption="Выберите папку",
            directory=os.path.join(os.path.expanduser("~"), "Downloads")
        )
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


class WinSmb(UMainWindow):
    def __init__(self):
        super().__init__()
        self.set_close_only()
        self.url = ""

        self.central_layout.setSpacing(10)

        lines = (
            "Не могу получить доступ к каталогу изображений 'Тест'",
            "Укажите правильный путь к каталогу"
        )
        up_label = QLabel("\n".join(lines))
        up_label.setStyleSheet(
            """
                margin-left: 3px;
                margin-right: 3px;
            """
        )
        self.central_layout.addWidget(up_label)

        bottom_wid = PathWidget()
        self.central_layout.addWidget(bottom_wid)

        btns_wid = QWidget()
        btns_lay = QHBoxLayout()
        btns_wid.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(0)


app = QApplication(sys.argv)
main_win = WinSmb()
main_win.show()
app.exec()