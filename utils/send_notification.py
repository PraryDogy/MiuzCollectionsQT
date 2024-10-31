from signals import signals_app

from .main_utils import MainUtils
from cfg import cnf


class SendNotification(object):
    def __init__(self, text: str):
        super().__init__()

        if cnf.image_viewer:
            signals_app.noti_img_view.emit(text)
        else:
            signals_app.noti_main.emit(text)