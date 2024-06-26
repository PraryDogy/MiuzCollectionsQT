from PyQt5.QtWidgets import QApplication, QFrame, QSpacerItem
from PyQt5.QtCore import Qt

from base_widgets import LayoutH, SvgBtn
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils

from ..win_settings import WinSettings
from .progress_bar import ProgressBar
import os


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

        self.switch_theme = SvgBtn(os.path.join("images", f"{cnf.theme}_switch.svg"), 18)
        self.switch_theme.mouseReleaseEvent = self.switch_theme_cmd
        self.h_layout.addWidget(self.switch_theme)

        self.h_layout.addSpacerItem(QSpacerItem(20, 0))

        self.sett_widget = SvgBtn(os.path.join("images", f"{cnf.theme}_settings.svg"), 20)
        self.sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(self.sett_widget)
   
        self.h_layout.addSpacerItem(QSpacerItem(30, 0))
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # from PyQt5.QtWidgets import QPushButton
        # self.restarter = QPushButton(self, text="Reload")
        # self.restarter.clicked.connect(self.reload)

    def reload(self):
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_filters_bar.emit()
        gui_signals_app.reload_stbar.emit()

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

        self.sett_widget.set_icon(os.path.join("images", f"{cnf.theme}_settings.svg"))
        self.switch_theme.set_icon(os.path.join("images", f"{cnf.theme}_switch.svg"))

    def sett_btn_cmd(self, e):
        self.settings = WinSettings(parent=self)
        self.settings.show()
