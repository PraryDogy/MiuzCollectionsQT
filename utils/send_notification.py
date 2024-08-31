from signals import gui_signals_app

from .main_utils import MainUtils
from cfg import cnf


class SendNotification(object):
    def __init__(self, text: str):
        super().__init__()

        if cnf.image_viewer:
            gui_signals_app.noti_img_view.emit(text)
        else:
            gui_signals_app.noti_main.emit(text)