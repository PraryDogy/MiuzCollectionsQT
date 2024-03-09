from PyQt5.QtCore import QObject, pyqtSignal


class GuiSignals(QObject):
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
    set_focus_viewer = pyqtSignal()

    scan_progress_value = pyqtSignal(int)

    progress_search_photos = pyqtSignal()
    progress_add_photos = pyqtSignal()

    def __init__(self):
        super().__init__()


gui_signals_app = GuiSignals()