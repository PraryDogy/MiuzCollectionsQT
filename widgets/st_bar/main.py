from PyQt5.QtWidgets import QFrame, QSpacerItem, QWidget, QApplication

from base_widgets import LayoutH, SvgBtn, SvgShadowed
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils

from ..win_settings import WinSettings
from .progress_bar import ProgressBar
from .thumb_move import ThumbMove


class Manager:
    win_settings = None


class StBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(28)
        self.setObjectName(Names.st_bar_frame)
        self.setStyleSheet(Themes.current)
        
        self.h_layout = LayoutH(self)
        self.init_ui()
        
        gui_signals_app.reload_stbar.connect(self.reload_stbar)

    def init_ui(self):
        self.h_layout.addStretch(1)

        self.h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.progress_bar = ProgressBar()
        self.h_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        self.h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.thumb_move = ThumbMove()
        # self.h_layout.addWidget(self.thumb_move)

        self.h_layout.addSpacerItem(QSpacerItem(10, 0))

        sett_widget = SvgBtn("settings.svg", 17)
        sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(sett_widget)

        self.h_layout.addSpacerItem(QSpacerItem(20, 0))

        self.zoom_wid = SvgBtn(self.get_zoom_icon(), 17)
        self.zoom_wid.mouseReleaseEvent = self.zoom_cmd
        self.h_layout.addWidget(self.zoom_wid)

        self.h_layout.addSpacerItem(QSpacerItem(20, 0))

        switch_theme = SvgBtn("switch_theme.svg", 17)
        switch_theme.mouseReleaseEvent = self.switch_theme_cmd
        self.h_layout.addWidget(switch_theme)

        self.h_layout.addSpacerItem(QSpacerItem(30, 0))

    def reload_stbar(self):
        MainUtils.clear_layout(self.h_layout)
        self.init_ui()

    def switch_theme_cmd(self, e):
        all_widgets = QApplication.allWidgets()
        widgets = [
            widget
            for widget in all_widgets
            if widget.objectName()
            ]
        
        if cnf.theme == "dark_theme":
            Themes.set_theme("light_theme")
            cnf.theme = "light_theme"
        else:
            Themes.set_theme("dark_theme")
            cnf.theme = "dark_theme"

        for i in widgets:
            i.setStyleSheet(Themes.current)

    def sett_btn_cmd(self, e):
        Manager.win_settings = WinSettings()
        Manager.win_settings.show()

    def zoom_cmd(self, e):
        cnf.zoom = not cnf.zoom
        self.zoom_wid.set_icon(self.get_zoom_icon())
        gui_signals_app.reload_thumbnails.emit()

    def get_zoom_icon(self):
        if cnf.zoom:
            return "grid_big.svg"
        else:
            return "grid_small.svg"