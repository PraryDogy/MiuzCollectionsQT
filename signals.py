from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    bar_bottom_filters = pyqtSignal()
    bar_top_reset_filters = pyqtSignal()
    btn_dates_style = pyqtSignal(str)
    grid_thumbnails_cmd = pyqtSignal(str)
    progressbar_text = pyqtSignal(str)
    menu_left_cmd = pyqtSignal(str)
    slider_change_value = pyqtSignal(int)
    thumbnail_select = pyqtSignal(str)
    wid_search_cmd = pyqtSignal(str)
    win_img_view_open_in = pyqtSignal(object)
    win_main_cmd = pyqtSignal(str)
    win_downloads_open = pyqtSignal()
    win_downloads_close = pyqtSignal()

    def __init__(self):
        super().__init__()


class SignalsApp:
    instance: Signals = None

    @classmethod
    def init(cls):
        cls.instance = Signals()