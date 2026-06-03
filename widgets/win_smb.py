import os

import sqlalchemy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from cfg import Cfg
from system.database import Dbase, Dirs, Thumbs
from system.lang import Lng
from system.main_folder import Mf
from system.utils import Utils

from ._base_widgets import UMainWindow
from .path_widget import PathWidget
from .win_warn import WarningWindow


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
        self.temp_path = ""

        self.set_close_only()
        self.set_always_on_top()
        self.setWindowTitle(Lng.attention[Cfg.lng_index])
        self.central_layout.setContentsMargins(10, 10, 10, 5)
        self.central_layout.setSpacing(10)

        self.warn_widget = WarnWidget(mf)
        self.central_layout.addWidget(self.warn_widget)

        self.path_widget = PathWidget(mf)
        self.path_widget.mf_is_avaiable.connect(self.mf_is_avaiable)
        self.central_layout.addWidget(self.path_widget)

        btns_wid = QWidget()
        self.central_layout.addWidget(btns_wid)
        btns_lay = QHBoxLayout(btns_wid)
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)

        btns_lay.addStretch()
        self.ok_btn = QPushButton(Lng.ok[Cfg.lng_index])
        self.ok_btn.clicked.connect(self.ok_clicked)
        self.ok_btn.setFixedWidth(90)
        btns_lay.addWidget(self.ok_btn)
        cancel_btn = QPushButton(Lng.cancel[Cfg.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btns_lay.addWidget(cancel_btn)
        btns_lay.addStretch()

        self.adjustSize()

    def mf_is_avaiable(self, mf_path: str):
        self.temp_path = mf_path
        if self.temp_path:
            conn = Dbase.main_engine.connect()
            stmt = (
                sqlalchemy.select(Dirs.rel_dir_path)
                .where(Dirs.mf_alias==self.mf.mf_alias)
            )
            result = conn.execute(stmt).scalars()
            paths = []
            for i in result:
                abs_path = Utils.get_abs_any_path(self.temp_path, i).rstrip(os.sep)
                if os.path.exists(abs_path):
                    paths.append(abs_path)
            if len(paths) == 1 and self.temp_path == paths[0]:
                self.temp_path = ""
                QTimer.singleShot(100, self.path_widget.no_path_widget)
                self.warn_win = WarningWindow(Lng.bad_smb[Cfg.lng_index])
                self.warn_win.center_to_parent(self)
                self.warn_win.show()

    def ok_clicked(self):
        if self.temp_path:
            self.mf.mf_paths = [self.temp_path, ]
            Mf.write_json_data()
            # try:
            #     self.warn_win.deleteLater()
            # except AttributeError:
            #     ...
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.deleteLater()
        return super().keyPressEvent(a0)
