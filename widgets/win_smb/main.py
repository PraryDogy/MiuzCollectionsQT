from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QWidget

from base_widgets import Btn, WinStandartBase
from cfg import cnf


class WinSmb(WinStandartBase):
    finished = pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.cancel_cmd)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.set_title(cnf.lng.no_connection)
        self.disable_min_max()

        self.init_ui()
        self.setFixedSize(300, 130)
        self.center_win(parent=parent)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def cancel_cmd(self, event):
        pass

    def pass_btn_cmd(self, event):
        self.finished.emit()
        self.close()

    def init_ui(self):
        descr = QLabel(cnf.lng.choose_coll_smb)
        self.content_layout.addWidget(descr)

        self.pass_btn = Btn(cnf.lng.close)
        self.pass_btn.mouseReleaseEvent = self.pass_btn_cmd
        self.content_layout.addWidget(self.pass_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        return
        return super().keyPressEvent(a0)
