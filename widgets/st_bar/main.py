import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QFrame, QSpacerItem, QWidget

from base_widgets import LayoutH, SvgBtn
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils

from ..win_downloads import DownloadsWin
from ..win_settings import WinSettings
from .progress_bar import ProgressBar


class SwitchView(SvgBtn):
    def __init__(self, size: int, parent: QWidget = None):
        icn = f"{cnf.theme}_{str(cnf.small_view).lower()}_view.svg"
        super().__init__(icon_path=os.path.join("images", icn), size=size, parent=parent)

    def switch_icon(self):
        icn = f"{cnf.theme}_{str(cnf.small_view).lower()}_view.svg"
        self.set_icon(icon_path=os.path.join("images", icn))


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
        gui_signals_app.jerk_downloads.connect(self.jerk_downloads)

    def init_ui(self):
        self.h_layout.addStretch(1)

        self.h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.progress_bar = ProgressBar()
        self.h_layout.addWidget(self.progress_bar)

        self.h_layout.addSpacerItem(QSpacerItem(15, 0))

        self.switch_view = SwitchView(size=20)
        self.switch_view.mouseReleaseEvent = self.switch_view_cmd
        self.h_layout.addWidget(self.switch_view)
        self.switch_view.setToolTip(cnf.lng.view_mode)

        self.h_layout.addSpacerItem(QSpacerItem(15, 0))

        self.switch_theme = SvgBtn(icon_path=os.path.join("images", f"{cnf.theme}_switch.svg"), size=20)
        self.switch_theme.mouseReleaseEvent = self.switch_theme_cmd
        self.h_layout.addWidget(self.switch_theme)
        self.switch_theme.setToolTip(cnf.lng.set_theme)

        self.h_layout.addSpacerItem(QSpacerItem(15, 0))

        self.downloads = SvgBtn(icon_path=os.path.join("images", f"{cnf.theme}_downloads.svg") , size=20)
        self.downloads.mouseReleaseEvent = self.open_downloads
        self.h_layout.addWidget(self.downloads)
        self.switch_view.setToolTip(cnf.lng.title_downloads)

        self.h_layout.addSpacerItem(QSpacerItem(15, 0))

        self.sett_widget = SvgBtn(icon_path=os.path.join("images", f"{cnf.theme}_settings.svg"), size=20)
        self.sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(self.sett_widget)
        self.sett_widget.setToolTip(cnf.lng.settings)
   
        self.h_layout.addSpacerItem(QSpacerItem(30, 0))
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.progress_bar.hide()

        # from PyQt5.QtCore import QTimer
        # QTimer.singleShot(1000, self.progress_bar.show)

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
        self.downloads.set_icon(os.path.join("images", f"{cnf.theme}_downloads.svg"))
        self.switch_theme.set_icon(os.path.join("images", f"{cnf.theme}_switch.svg"))
        self.switch_view.switch_icon()

        cnf.write_json_cfg()

    def open_downloads(self, e):
        self.downloads_win = DownloadsWin(parent=self)
        self.downloads_win.center_win(self)
        self.downloads_win.show()

    def jerk_downloads(self):
        self.blue_downloads()
        ms = 200
        QTimer.singleShot(ms, self.default_downloads)
        QTimer.singleShot(ms*2, self.blue_downloads)
        QTimer.singleShot(ms*3, self.default_downloads)
        QTimer.singleShot(ms*4, self.blue_downloads)
        QTimer.singleShot(ms*5, self.default_downloads)

    def default_downloads(self):
        self.downloads.set_icon(os.path.join("images", f"{cnf.theme}_downloads.svg"))

    def blue_downloads(self):
        self.downloads.set_icon(os.path.join("images", f"blue_downloads.svg"))

    def sett_btn_cmd(self, e):
        self.settings = WinSettings(parent=self)
        self.settings.show()

    def switch_view_cmd(self, e):
        cnf.small_view = not cnf.small_view
        gui_signals_app.reload_thumbnails.emit()
        self.switch_view.switch_icon()
        cnf.write_json_cfg()
