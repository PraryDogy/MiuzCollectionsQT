from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from base_widgets import Btn
from cfg import LIMIT, Dynamic
from signals import SignalsApp


class LimitBtn(Btn):
    _clicked =  pyqtSignal()

    def __init__(self):
        super().__init__(text=Dynamic.lang.show_more)
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        Dynamic.current_photo_limit += LIMIT
        self._clicked.emit()
        # SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        # return super().mouseReleaseEvent(ev)