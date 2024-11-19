from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    bar_top_reset_filters = pyqtSignal()
    btn_dates_style = pyqtSignal(str)
    btn_downloads_toggle = pyqtSignal(str)
    grid_thumbnails_cmd = pyqtSignal(str)
    progressbar_text = pyqtSignal(str)
    menu_left_cmd = pyqtSignal(str)
    slider_change_value = pyqtSignal(int)
    thumbnail_select = pyqtSignal(str)
    wid_search_cmd = pyqtSignal(str)
    win_img_view_open_in = pyqtSignal(object)
    win_main_cmd = pyqtSignal(str)

    def __init__(self):
        super().__init__()


class SignalsApp:
    all_: Signals = None

    @classmethod
    def init(cls):
        cls.all_ = Signals()
        print("signals app started")