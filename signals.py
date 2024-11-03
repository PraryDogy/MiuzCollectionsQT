from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    scaner_start = pyqtSignal()
    scaner_stop = pyqtSignal()

    reload_thumbnails = pyqtSignal()
    reload_menu = pyqtSignal()
    reload_filters_bar = pyqtSignal()
    reload_stbar = pyqtSignal()
    reload_title = pyqtSignal()
    reload_search_wid = pyqtSignal()
    reload_menubar = pyqtSignal()

    disable_filters = pyqtSignal()
    clear_search = pyqtSignal()
    scroll_top = pyqtSignal()

    set_dates_btn_blue_border = pyqtSignal()
    set_dates_btn_normal = pyqtSignal()
    set_dates_btn_blue = pyqtSignal()

    set_focus_search = pyqtSignal()

    progressbar_value = pyqtSignal(object)

    btn_downloads_hide = pyqtSignal()

    noti_win_main = pyqtSignal(str)
    noti_win_img_view = pyqtSignal(str)

    thumbnail_select = pyqtSignal(str)
    win_img_view_open_in = pyqtSignal(object)
    grid_thumbnails_resize = pyqtSignal()
    slider_change_value = pyqtSignal(int)

    win_main_show = pyqtSignal()
    win_img_view_show = pyqtSignal()

    def __init__(self):
        super().__init__()


signals_app = Signals()