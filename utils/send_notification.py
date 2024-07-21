from signals import gui_signals_app

from .main_utils import MainUtils


class SendNotification(object):
    def __init__(self, text: str):
        super().__init__()
        win = None

        for i in MainUtils.get_app().topLevelWidgets():
            if "ImageView" in str(i):
                win = i
                break
        
        if not win:
            gui_signals_app.noti_main.emit(text)
        else:
            gui_signals_app.noti_img_view.emit(text)

