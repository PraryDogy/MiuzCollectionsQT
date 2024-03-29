from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSpacerItem

from base_widgets import Btn, WinStandartBase
from cfg import cnf
from signals import gui_signals_app


class WinSmb(WinStandartBase):
    def __init__(self):
        super().__init__(close_func=self.close_cmd)
        self.disable_min_max()
        self.set_title(cnf.lng.no_connection)
        self.setWindowModality(Qt.WindowModality.ApplicationModal, Qt.WindowAnimationOff)

        # QLineEdit
        label = QLabel(cnf.lng.smb_descr)
        self.content_layout.addWidget(label)

        self.content_layout.addSpacerItem(QSpacerItem(0, 10))


        # перейти в настройки
        close = Btn(cnf.lng.close)
        close.mouseReleaseEvent = self.close_cmd
        self.content_layout.addWidget(close, alignment=Qt.AlignCenter)

        self.fit_size()
        self.center_win()
    
    def close_cmd(self, e):
        self.delete_win.emit()
        self.deleteLater()
        gui_signals_app.set_focus_viewer.emit()

