from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    scaner_toggle = pyqtSignal(str)

    reload_thumbnails = pyqtSignal()
    reload_menu = pyqtSignal()
    reload_filters_bar = pyqtSignal()
    reload_stbar = pyqtSignal()
    reload_title = pyqtSignal()
    reload_search_wid = pyqtSignal()
    reload_menubar = pyqtSignal()

    search_wid_clear = pyqtSignal()
    search_wid_focus = pyqtSignal()

    disable_filters = pyqtSignal()
    scroll_top = pyqtSignal()
    
    dates_btn_style = pyqtSignal(str)
    progressbar_value = pyqtSignal(object)
    btn_downloads_hide = pyqtSignal(bool)
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