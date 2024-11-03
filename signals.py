from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    scaner_toggle = pyqtSignal(str)

    reload_grid_thumbnails = pyqtSignal()
    reload_menu_left = pyqtSignal()
    reload_win_main_title = pyqtSignal()

    wid_search_cmd = pyqtSignal(str)

    bar_top_reset_filters = pyqtSignal()

    grid_thumbnails_to_top = pyqtSignal()
    grid_thumbnails_resize = pyqtSignal()
    thumbnail_select = pyqtSignal(str)

    btn_dates_style = pyqtSignal(str)
    btn_downloads_toggle = pyqtSignal(str)

    progressbar_value = pyqtSignal(int)

    noti_win_main = pyqtSignal(str)
    noti_win_img_view = pyqtSignal(str)

    slider_change_value = pyqtSignal(int)

    win_img_view_open_in = pyqtSignal(object)
    win_main_show = pyqtSignal()
    win_img_view_show = pyqtSignal()

    def __init__(self):
        super().__init__()


signals_app = Signals()