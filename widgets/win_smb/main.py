from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QWidget, QSpacerItem

from base_widgets import Btn, LayoutH, WinStandartBase, SvgBtn
from cfg import cnf


class WinSmb(WinStandartBase):
    finished = pyqtSignal()

    def __init__(self, parent: QWidget, text: str = None):
        super().__init__(close_func=self.cancel_cmd)

        if text:
            self.my_text = text
        else:
            self.my_text = cnf.lng.choose_coll_smb

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.set_title(cnf.lng.no_connection)
        self.disable_min()
        self.disable_max()
        self.disable_close()

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
        h_wid = QWidget()
        self.content_layout.addWidget(h_wid)
        h_layout = LayoutH()
        h_wid.setLayout(h_layout)

        icon_label = SvgBtn("images/warning.svg", 40)
        h_layout.addWidget(icon_label)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        descr = QLabel(self.my_text)
        h_layout.addWidget(descr)

        h_layout.addStretch()

        self.content_layout.addSpacerItem(QSpacerItem(0, 10))

        self.pass_btn = Btn(cnf.lng.ok)
        self.pass_btn.mouseReleaseEvent = self.pass_btn_cmd
        self.content_layout.addWidget(self.pass_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        # return
        # return super().keyPressEvent(a0)
