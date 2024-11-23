from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from base_widgets import Btn
from cfg import GRID_LIMIT, Dynamic
from lang import Lang
from utils.utils import Utils


class LimitBtn(Btn):
    _clicked =  pyqtSignal()

    def __init__(self):
        super().__init__(text=Lang.show_more)
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        Dynamic.grid_offset += GRID_LIMIT
        self._clicked.emit()
        self.setDisabled(True)
        self.setText("")
        self.setObjectName("thumbnail")
        Utils.style(self, "normal")