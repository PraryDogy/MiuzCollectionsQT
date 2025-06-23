from PyQt5.QtCore import QObject, pyqtSignal


class Signals(QObject):
    grid_thumbnails_cmd = pyqtSignal(str)
    progressbar_text = pyqtSignal(str)
    menu_left_cmd = pyqtSignal(str)
    slider_change_value = pyqtSignal(int)
    wid_search_cmd = pyqtSignal(str)
    win_main_cmd = pyqtSignal(str)
    win_downloads_open = pyqtSignal()
    win_downloads_close = pyqtSignal()

    def __init__(self):
        super().__init__()


class SignalsApp:
    """
    bar_bottom_filters: None  
    bar_top_reset_filters: None  
    dtn_dates_style: "solid" or "normal" or "border"  
    grid_thumbnails_cmd: "resize" or "reload" or "to_top"  
    menu_left_cmd: "reload" or "select_all_colls"  
    progressbar_text: str  
    slider_change_value: int  
    wid_search_cmd: "focus"  
    win_downloads_close: None  
    win_downloads_open: None  
    win_main_cmd: "show" or "exit" or "set_title"  
    """

    instance: Signals = None

    @classmethod
    def init(cls):
        cls.instance = Signals()