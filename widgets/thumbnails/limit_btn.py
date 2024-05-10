from PyQt5.QtCore import Qt

from cfg import cnf

from base_widgets import Btn
from signals import gui_signals_app

class LimitBtn(Btn):
    def __init__(self):
        super().__init__(text=cnf.lng.show_more)
        self.setFixedWidth(100)
        self.setAlignment(Qt.AlignCenter)

    def mouseReleaseEvent(self, event):
        cnf.current_limit += cnf.LIMIT
        gui_signals_app.reload_thumbnails.emit()
