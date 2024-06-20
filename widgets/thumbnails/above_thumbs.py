from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QSizePolicy, QSpacerItem, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes


class Manager:
    btn_w = 120
    btn_h = 28


class ResetDatesBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.reset_dates)
        self.setFixedSize(Manager.btn_w, Manager.btn_h)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_reset_dates_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        cnf.date_start, cnf.date_end = None, None
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.set_dates_btn_normal.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class ResetSearchBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.reset_search)
        self.setFixedSize(Manager.btn_w, Manager.btn_h)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_reset_search_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.clear_search.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class ResetFiltersBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.show_all)
        self.setFixedSize(Manager.btn_w, Manager.btn_h)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_reset_filters_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.disable_filters.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class ShowAllBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.show_all)
        self.setFixedSize(Manager.btn_w, Manager.btn_h)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_show_all_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        cnf.date_start, cnf.date_end = None, None
        cnf.curr_coll = cnf.ALL_COLLS
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.clear_search.emit()
        gui_signals_app.disable_filters.emit()

        gui_signals_app.reload_title.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.reload_menu.emit()

        gui_signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class AboveThumbsNoImages(QWidget):
    def __init__(self, width):
        super().__init__()

        self.v_layout = LayoutV()
        self.setLayout(self.v_layout)

        noimg_t = cnf.lng.no_photo

        title_label = QLabel(text=noimg_t)
        title_label.setFixedWidth(width - 20)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_label.setWordWrap(True)
        self.v_layout.addWidget(title_label)
        title_label.setObjectName(Names.th_title)
        title_label.setStyleSheet(Themes.current)

        h_layout = LayoutH()
        h_layout.setContentsMargins(0, 10, 0, 0)
        self.v_layout.addLayout(h_layout)

        merg_fltr_vals = {
            **cnf.cust_fltr_vals,
            **cnf.sys_fltr_vals
            }

        merg_fltr_lng = {
            **cnf.lng.cust_fltr_names,
            **cnf.lng.sys_fltr_names
            }

        if cnf.search_text:
            noimg_t = (f"{cnf.lng.no_photo} {cnf.lng.with_name}: "
                       f"{cnf.search_text}")

            title_label.setText(noimg_t)

            s_label = ResetSearchBtn()
            h_layout.addWidget(s_label)

        elif any((cnf.date_start, cnf.date_end)):
            noimg_t = (f"{cnf.lng.no_photo}: "
                       f"{cnf.date_start_text} - {cnf.date_end_text}")

            title_label.setText(noimg_t)
            h_layout.addWidget(ResetDatesBtn())

        elif any(merg_fltr_vals.values()):
            filters = (f"{merg_fltr_lng[code_name].lower()}"
                       for code_name, val in merg_fltr_vals.items()
                       if val)
            filters = ",  ".join(filters)
            noimg_t = (f"{cnf.lng.no_photo_filter}: {filters}")

            title_label.setText(noimg_t)
            h_layout.addWidget(ResetFiltersBtn())
        
        else:
            h_layout.addWidget(ShowAllBtn())


class AboveThumbs(QWidget):
    def __init__(self, width):
        super().__init__()

        self.v_layout = LayoutV()
        self.setLayout(self.v_layout)


        label = QLabel()
        self.v_layout.addWidget(label)
        label.setFixedWidth(width - 20)
        label.setWordWrap(True)
        label.setObjectName(Names.th_title)
        label.setStyleSheet(Themes.current)

        h_layout = LayoutH()
        h_layout.setContentsMargins(0, 10, 0, 0)
        self.v_layout.addLayout(h_layout)

        if any((cnf.date_start, cnf.date_end)):
            label.setText(
                f"{cnf.lng.photos_named_dates}: {cnf.date_start_text} - {cnf.date_end_text}"
                )
            h_layout.addWidget(ResetDatesBtn())

            spacer = QSpacerItem(1, 10)
            self.v_layout.addSpacerItem(spacer)

        elif cnf.search_text:
            label.setText(f"{cnf.lng.search}: {cnf.search_text}")
            h_layout.addWidget(ResetSearchBtn())
            h_layout.addSpacerItem(QSpacerItem(1, 30))

            spacer = QSpacerItem(1, 10)
            self.v_layout.addSpacerItem(spacer)

        else:
            self.deleteLater()