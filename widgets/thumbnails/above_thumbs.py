from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy, QSpacerItem

from cfg import cnf

from base_widgets import LayoutH, LayoutV
from styles import Styles
from signals import gui_signals_app

class ResetDatesBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.reset_dates)
        self.setFixedSize(Styles.thumbs_item_w, Styles.thumbs_item_h)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_item_color};
            border-radius: {Styles.small_radius};
            """)

    def mouseReleaseEvent(self, event):
        cnf.date_start, cnf.date_end = None, None
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.set_dates_btn_normal.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()


class ResetSearchBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.reset_search)
        self.setFixedSize(Styles.thumbs_item_w, Styles.thumbs_item_h)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_item_color};
            border-radius: {Styles.small_radius};
            """)

    def mouseReleaseEvent(self, event):
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.clear_search.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()


class ResetFiltersBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.show_all)
        self.setFixedSize(Styles.thumbs_item_w, Styles.thumbs_item_h)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_item_color};
            border-radius: {Styles.small_radius};
            """)

    def mouseReleaseEvent(self, event):
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.disable_filters.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()


class ShowAllBtn(QLabel):
    def __init__(self):
        super().__init__(text=cnf.lng.show_all)
        self.setFixedSize(Styles.thumbs_item_w, Styles.thumbs_item_h)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_item_color};
            border-radius: {Styles.small_radius};
            """)

    def mouseReleaseEvent(self, event):
        cnf.date_start, cnf.date_end = None, None
        cnf.curr_coll = cnf.ALL_COLLS
        cnf.current_limit = cnf.LIMIT

        gui_signals_app.clear_search.emit()
        gui_signals_app.disable_filters.emit()

        gui_signals_app.reload_title.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.reload_menu.emit()

        gui_signals_app.scroll_top.emit()


class AboveThumbsNoImages(LayoutV):
    def __init__(self, width):
        super().__init__()

        noimg_t = cnf.lng.no_photo

        title_label = QLabel(text=noimg_t)
        title_label.setFixedWidth(width - 20)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(
            f"""
            font-size: {Styles.title_font_size};
            font-weight: bold;
            """)
        self.addWidget(title_label)

        h_layout = LayoutH()
        h_layout.setContentsMargins(0, 10, 0, 0)
        self.addLayout(h_layout)

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


class AboveThumbs(LayoutV):
    def __init__(self, width):
        super().__init__()
        label = QLabel()
        self.addWidget(label)
        label.setFixedWidth(width - 20)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"""
            font-size: {Styles.title_font_size};
            font-weight: bold;
            """)

        h_layout = LayoutH()
        h_layout.setContentsMargins(0, 10, 0, 0)
        self.addLayout(h_layout)

        if any((cnf.date_start, cnf.date_end)):
            label.setText(
                f"{cnf.lng.photos_named_dates}: {cnf.date_start_text} - {cnf.date_end_text}"
                )
            h_layout.addWidget(ResetDatesBtn())

            spacer = QSpacerItem(1, 10)
            self.addSpacerItem(spacer)

        elif cnf.search_text:
            label.setText(f"{cnf.lng.search}: {cnf.search_text}")
            h_layout.addWidget(ResetSearchBtn())
            h_layout.addSpacerItem(QSpacerItem(1, 30))

            spacer = QSpacerItem(1, 10)
            self.addSpacerItem(spacer)

        else:
            self.deleteLater()
