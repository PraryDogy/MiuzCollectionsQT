from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from base_widgets import LayoutH, LayoutV, SvgBtn
from cfg import cnf
from signals import gui_signals_app
from styles import Styles
from utils import MainUtils

from ..win_settings import WinSettings
from .progress_bar import ProgressBar
from .thumb_move import ThumbMove


class StBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(28)
        self.setStyleSheet(
            f"""
            background-color: {Styles.st_bar_bg_color};
            border-bottom-right-radius: {Styles.base_radius}px;
            """)

        v_layout = LayoutV(self)

        h_frame = QFrame()
        h_frame.setFixedHeight(1)
        h_frame.setStyleSheet(
            f"""
            background-color: black;
            """)
        v_layout.addWidget(h_frame)

        main_wid = QWidget()
        main_wid.setContentsMargins(0, 0, 0, 0)
        main_wid.setStyleSheet(
            f"""
            background-color: {Styles.st_bar_bg_color};
            """)
        v_layout.addWidget(main_wid)
        self.h_layout = LayoutH(main_wid)
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
        self.h_layout.addLayout(self.thumb_move)

        # self.h_layout.addSpacerItem(QSpacerItem(10, 0))

        sett_base = QWidget()
        sett_base.setFixedWidth(60)
        sett_base.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(sett_base)

        sett_layout = LayoutH()
        sett_base.setLayout(sett_layout)

        sett_widget = SvgBtn("settings.svg", 17)
        sett_layout.addWidget(sett_widget)

        self.zoom_wid = SvgBtn(self.get_zoom_icon(), 17)
        self.zoom_wid.mouseReleaseEvent = self.zoom_cmd
        self.h_layout.addWidget(self.zoom_wid)

        self.h_layout.addSpacerItem(QSpacerItem(30, 0))

    def reload_stbar(self):
        MainUtils.clear_layout(self.h_layout)
        self.init_ui()

    def sett_btn_cmd(self, e):
        settings_win = WinSettings()
        settings_win.show()

    def zoom_cmd(self, e):
        cnf.zoom = not cnf.zoom
        self.zoom_wid.set_icon(self.get_zoom_icon())
        gui_signals_app.reload_thumbnails.emit()

    def get_zoom_icon(self):
        if cnf.zoom:
            return "grid_big.svg"
        else:
            return "grid_small.svg"