from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent

from cfg import cnf

from base_widgets import Btn
from signals import signals_app

class LimitBtn(Btn):
    def __init__(self):
        super().__init__(text=cnf.lng.show_more)
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        cnf.current_photo_limit += cnf.LIMIT
        signals_app.reload_thumbnails.emit()
        return super().mouseReleaseEvent(ev)