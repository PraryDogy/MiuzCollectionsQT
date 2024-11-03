from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    bar_top_reset_filters = pyqtSignal()
    btn_dates_style = pyqtSignal(str)
    btn_downloads_toggle = pyqtSignal(str)
    grid_thumbnails_cmd = pyqtSignal(str)
    noti_win_main = pyqtSignal(str)
    noti_win_img_view = pyqtSignal(str)
    progressbar_change_value = pyqtSignal(int)
    reload_menu_left = pyqtSignal()
    scaner_toggle = pyqtSignal(str)
    slider_change_value = pyqtSignal(int)
    thumbnail_select = pyqtSignal(str)
    wid_search_cmd = pyqtSignal(str)
    win_img_view_open_in = pyqtSignal(object)
    win_main_cmd = pyqtSignal(str)

    def __init__(self):
        super().__init__()


signals_app = Signals()