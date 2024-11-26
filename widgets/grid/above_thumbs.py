from PyQt5.QtWidgets import (QLabel, QPushButton, QSizePolicy, QSpacerItem,
                             QWidget)

from base_widgets import LayoutHor, LayoutVer
from cfg import Dynamic, Filters, JsonData, Static
from lang import Lang
from signals import SignalsApp

BTN_W = 120


class ResetBtn(QPushButton):
    def __init__(self, text: str):
        super().__init__(text=text)

        self.setFixedWidth(BTN_W)
        # self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class ResetDatesBtn(ResetBtn):
    def __init__(self):
        super().__init__(text=Lang.reset)
        self.clicked.connect(self.cmd_)

    def cmd_(self, *args) -> None:
        Dynamic.date_start, Dynamic.date_end = None, None
        Dynamic.grid_offset = 0

        SignalsApp.all_.btn_dates_style.emit("normal")
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")


class ResetSearchBtn(ResetBtn):
    def __init__(self):
        super().__init__(text=Lang.reset)
        self.clicked.connect(self.cmd_)

    def cmd_(self, *args) -> None:
        Dynamic.grid_offset = 0

        SignalsApp.all_.wid_search_cmd.emit("clear")
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")


class ResetFiltersBtn(ResetBtn):
    def __init__(self):
        super().__init__(text=Lang.reset)
        self.clicked.connect(self.cmd_)

    def cmd_(self, *args) -> None:
        Dynamic.grid_offset = 0

        SignalsApp.all_.bar_top_reset_filters.emit()
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")


class ShowAllBtn(ResetBtn):
    def __init__(self):
        super().__init__(text=Lang.show_all)
        self.clicked.connect(self.cmd_)

    def cmd_(self, *args) -> None:
        Dynamic.date_start, Dynamic.date_end = None, None
        Dynamic.curr_coll_name = Static.NAME_ALL_COLLS
        Dynamic.grid_offset = 0

        SignalsApp.all_.wid_search_cmd.emit("clear")
        SignalsApp.all_.bar_top_reset_filters.emit()

        SignalsApp.all_.win_main_cmd.emit("set_title")
        SignalsApp.all_.menu_left_cmd.emit("select_all_colls")

        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")


class ErrorTitle(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        title = QLabel()
        title.setStyleSheet(Static.TITLE_NORMAL)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
            )
        self.v_layout.addWidget(title)

        h_wid = QWidget()
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)
        self.v_layout.addWidget(h_wid)

        enabled_filters = [
            filter.names[JsonData.lang_ind]
            for filter in Filters.current
            if filter.value
            ]

        if Dynamic.search_widget_text:
            noimg_t = (f"{Lang.no_photo} {Lang.with_name}: "
                       f"{Dynamic.search_widget_text}")

            title.setText(noimg_t)

            s_label = ResetSearchBtn()
            h_layout.addWidget(s_label)

        elif any((Dynamic.date_start, Dynamic.date_end)):
            noimg_t = (f"{Lang.no_photo}: "
                       f"{Dynamic.date_start_text} - {Dynamic.date_end_text}")

            title.setText(noimg_t)
            h_layout.addWidget(ResetDatesBtn())

        elif enabled_filters:

            enabled_filters = ", ".join(enabled_filters)

            noimg_t = (f"{Lang.no_photo_filter}: {enabled_filters}")

            title.setText(noimg_t)
            h_layout.addWidget(ResetFiltersBtn())
        
        else:
            h_layout.addWidget(ShowAllBtn())


class FilterTitle(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        title = QLabel()
        title.setStyleSheet(Static.TITLE_NORMAL)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
            )
        self.v_layout.addWidget(title)

        h_wid = QWidget()
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)
        self.v_layout.addWidget(h_wid)

        if any((Dynamic.date_start, Dynamic.date_end)):
            title.setText(
                f"{Lang.photos_named_dates}: {Dynamic.date_start_text} - {Dynamic.date_end_text}"
                )
            h_layout.addWidget(ResetDatesBtn())

            spacer = QSpacerItem(1, 10)
            self.v_layout.addSpacerItem(spacer)

        elif Dynamic.search_widget_text:
            title.setText(f"{Lang.search}: {Dynamic.search_widget_text}")
            h_layout.addWidget(ResetSearchBtn())
            h_layout.addSpacerItem(QSpacerItem(1, 30))

            spacer = QSpacerItem(1, 10)
            self.v_layout.addSpacerItem(spacer)

        else:
            self.deleteLater()