import os
import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker

from ._base_widgets import (MfPathWidget, SuperConfirmWindow, UMainWidget,
                            UPushButton)


def restart_app():
    ProcessWorker.stop_all() 
    os.execl(sys.executable, sys.executable, *sys.argv)
    QApplication.exit(0)


class WarnWidget(QWidget):
    icon_path = Static.COMMON_ICONS / "yellow_warning.svg"

    def __init__(self, mf: Mf):
        super().__init__()
        self.setFixedWidth(350)
        h_lay = QHBoxLayout(self)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        warn_wid = QSvgWidget()
        warn_wid.load(str(self.icon_path))
        warn_wid.setFixedSize(30, 30)
        h_lay.addWidget(warn_wid)

        lines = (
            f"{Lng.access_error_text[JsonData.lng_index]} \"{mf.mf_alias}\".",
            Lng.network_error_text[JsonData.lng_index]
        )
        up_label = QLabel("\n".join(lines))
        up_label.setWordWrap(True)
        h_lay.addWidget(up_label)


class WinSmb(UMainWidget):

    def __init__(self, mf: Mf):
        super().__init__()
        self.mf = mf

        self.set_close_only()
        self.set_always_on_top()
        self.setWindowTitle(Lng.attention[JsonData.lng_index])
        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)

        self.warn_widget = WarnWidget(mf)
        self.central_layout.addWidget(self.warn_widget)

        self.path_widget = MfPathWidget(JsonData.lng_index, mf.mf_current_path)
        self.central_layout.addWidget(self.path_widget)

        btns_wid = QWidget()
        self.central_layout.addWidget(btns_wid)
        btns_lay = QHBoxLayout(btns_wid)
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)

        btns_lay.addStretch()
        self.ok_btn = UPushButton(Lng.ok[JsonData.lng_index])
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_lay.addWidget(self.ok_btn)
        cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        btns_lay.addWidget(cancel_btn)
        btns_lay.addStretch()

        self.adjustSize()

    def ok_cmd(self):

        def ok_clicked():
            self.mf.mf_paths = [mf_path, ]
            self.mf.mf_current_path = mf_path
            Mf.write_json_data()
            restart_app()

        mf_path = self.path_widget.validate()
        if mf_path:
            self.super_win = SuperConfirmWindow(
                Lng.confirm_mf_path[JsonData.lng_index],
                301, 105
            )
            self.super_win.ok_clicked.connect(ok_clicked)
            self.super_win.center_to_parent(self)
            self.super_win.show()

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key.Key_Escape, ):
            self.deleteLater()
        return super().keyPressEvent(a0)

    def deleteLater(self):
        return super().deleteLater()