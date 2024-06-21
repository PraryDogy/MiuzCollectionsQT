from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QProgressBar, QSpacerItem, QWidget

from base_widgets import Btn, WinStandartBase
from cfg import cnf


class WinCopyFiles(WinStandartBase):
    cancel_sign = pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.my_close)
        self.set_title(cnf.lng.copying_title)
        self.disable_min_max()
        self.disable_close()
        self.setFixedSize(270, 130)

        label = QLabel(text=cnf.lng.copying_files, parent=self)
        label.setFixedHeight(15)
        self.content_layout.addWidget(label)

        self.progress = QProgressBar(parent=self)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.content_layout.addWidget(self.progress)

        self.content_layout.addSpacerItem(QSpacerItem(0, 10))

        self.cancel_btn = Btn(cnf.lng.cancel)
        self.cancel_btn.mouseReleaseEvent = self.cancel_btn_cmd
        self.content_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.center_win(parent=parent)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        return
        return super().keyPressEvent(a0)

    def my_close(self, event):
        return

    def cancel_btn_cmd(self, e):
        self.cancel_sign.emit()
        self.close()

    def set_value(self, value: int):
        try:
            self.progress.setValue(value)
        except (Exception, RuntimeError) as e:
            print(e)
