from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QSpacerItem, QWidget

from base_widgets import Btn, LayoutHor, SvgBtn, WinStandart
from cfg import Dynamic


class WinSmb(WinStandart):
    _finished = pyqtSignal()

    def __init__(self, parent: QWidget, text: str = None):
        super().__init__(close_func=self.close_cmd)

        if text:
            self.my_text = text
        else:
            self.my_text = Dynamic.lng.choose_coll_smb

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.set_titlebar_title(Dynamic.lng.no_connection)
        self.min_btn_disable()
        self.max_btn_disable()
        # self.disable_close()

        self.init_ui()
        self.setFixedSize(350, 170)
        self.center_relative_parent(parent=parent)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def close_cmd(self, *args):
        self._finished.emit()
        self.close()

    def init_ui(self):
        h_wid = QWidget()
        self.content_lay_v.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)

        icon_label = SvgBtn("images/warning.svg", 40)
        h_layout.addWidget(icon_label)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        descr = QLabel(self.my_text)
        h_layout.addWidget(descr)

        h_layout.addStretch()

        self.content_lay_v.addSpacerItem(QSpacerItem(0, 10))

        self.ok_btn = Btn(Dynamic.lng.ok)
        self.ok_btn.mouseReleaseEvent = self.close_cmd
        self.content_lay_v.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close_cmd()