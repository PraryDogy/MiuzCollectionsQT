from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    scaner_start = pyqtSignal()
    scaner_stop = pyqtSignal()
    migrate_finished = pyqtSignal()

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
    progressbar_show = pyqtSignal()
    progressbar_hide = pyqtSignal()

    hide_downloads = pyqtSignal()
    show_downloads = pyqtSignal()

    noti_main = pyqtSignal(str)
    noti_img_view = pyqtSignal(str)

    move_to_wid = pyqtSignal(QObject)
    select_new_wid = pyqtSignal(str)

    def __init__(self):
        super().__init__()


signals_app = Signals()