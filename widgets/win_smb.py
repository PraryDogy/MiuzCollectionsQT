from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import UMainWindow
from .path_widget import PathWidget
from .win_warn import ConfirmWindow


class SuperWarnWindow(UMainWindow):
    ok_clicked = pyqtSignal()
    svg = "./images/super_warning.svg"
    svg_size = 60

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.attention[Cfg.lng_index])
        self.set_always_on_top()
        self.set_close_only()
        above_layout = QHBoxLayout()
        above_layout.setSpacing(15)
        above_layout.setContentsMargins(0, 0, 15, 0)
        self.central_layout.setSpacing(10)
        self.central_layout.addLayout(above_layout)

        svg_widget = QSvgWidget()
        svg_widget.load(self.svg)
        svg_widget.setFixedSize(self.svg_size, self.svg_size)
        above_layout.addWidget(svg_widget)

        question = QLabel(Lng.confirm_mf_path[Cfg.lng_index])
        if Cfg.lng_index == 0:
            ww = 270
        else:
            ww = 260
        question.setFixedWidth(ww)
        question.setWordWrap(True)
        above_layout.addWidget(question)

        btns_lay = QHBoxLayout()
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)
        self.central_layout.addLayout(btns_lay)

        btns_lay.addStretch()
        self.ok_btn = QPushButton(Lng.ok[Cfg.lng_index])
        self.ok_btn.clicked.connect(self.ok_clicked.emit)
        self.ok_btn.setFixedWidth(90)
        btns_lay.addWidget(self.ok_btn)
        cancel_btn = QPushButton(Lng.cancel[Cfg.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btns_lay.addWidget(cancel_btn)
        btns_lay.addStretch()

        self.adjustSize()


    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class WarnWidget(QWidget):
    warn = "images/warning.svg"
    def __init__(self, mf: Mf):
        super().__init__()
        self.setFixedWidth(350)
        h_lay = QHBoxLayout(self)
        h_lay.setContentsMargins(2, 5, 2, 5)
        h_lay.setSpacing(10)

        warn_wid = QSvgWidget()
        warn_wid.load(self.warn)
        warn_wid.setFixedSize(30, 30)
        h_lay.addWidget(warn_wid)

        lines = (
            f"{Lng.access_error_text[Cfg.lng_index]} \"{mf.mf_alias}\".",
            Lng.network_error_text[Cfg.lng_index]
        )
        up_label = QLabel("\n".join(lines))
        up_label.setWordWrap(True)
        h_lay.addWidget(up_label)


class WinSmb(UMainWindow):

    def __init__(self, mf: Mf):
        super().__init__()
        self.mf = mf
        self.mf_temp_path = ""

        self.set_close_only()
        self.set_always_on_top()
        self.setWindowTitle(Lng.attention[Cfg.lng_index])
        self.central_layout.setContentsMargins(10, 10, 10, 5)
        self.central_layout.setSpacing(10)

        self.warn_widget = WarnWidget(mf)
        self.central_layout.addWidget(self.warn_widget)

        self.path_widget = PathWidget(mf)
        self.central_layout.addWidget(self.path_widget)

        btns_wid = QWidget()
        self.central_layout.addWidget(btns_wid)
        btns_lay = QHBoxLayout(btns_wid)
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)

        btns_lay.addStretch()
        self.ok_btn = QPushButton(Lng.ok[Cfg.lng_index])
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(90)
        btns_lay.addWidget(self.ok_btn)
        cancel_btn = QPushButton(Lng.cancel[Cfg.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btns_lay.addWidget(cancel_btn)
        btns_lay.addStretch()

        self.adjustSize()

    def ok_cmd(self):

        def ok_clicked():
            if self.path_widget.mf_temp_path:
                self.mf.mf_paths = [self.path_widget.mf_temp_path, ]
                self.mf.mf_current_path = self.path_widget.mf_temp_path
                Mf.write_json_data()
                self.super_win.deleteLater()
                self.deleteLater()

        if self.path_widget.mf_temp_path:
            self.super_win = SuperWarnWindow()
            self.super_win.ok_clicked.connect(ok_clicked)
            self.super_win.center_to_parent(self)
            self.super_win.show()

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key.Key_Escape, ):
            self.deleteLater()
        return super().keyPressEvent(a0)

    def deleteLater(self):
        return super().deleteLater()