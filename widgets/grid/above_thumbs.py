from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QSizePolicy, QSpacerItem, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import ALL_COLLS, LIMIT, Dynamic, JsonData
from signals import signals_app
from styles import Names, Themes

BTN_W, BTN_H = 120, 28


class ResetDatesBtn(QLabel):
    def __init__(self):
        super().__init__(text=Dynamic.lng.reset_dates)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_reset_dates_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        Dynamic.date_start, Dynamic.date_end = None, None
        Dynamic.current_photo_limit = LIMIT

        signals_app.dates_btn_style.emit("normal")
        signals_app.reload_thumbnails.emit()
        signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class ResetSearchBtn(QLabel):
    def __init__(self):
        super().__init__(text=Dynamic.lng.reset_search)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_reset_search_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        Dynamic.current_photo_limit = LIMIT

        signals_app.clear_search.emit()
        signals_app.reload_thumbnails.emit()
        signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class ResetFiltersBtn(QLabel):
    def __init__(self):
        super().__init__(text=Dynamic.lng.show_all)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_reset_filters_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        Dynamic.current_photo_limit = LIMIT

        signals_app.disable_filters.emit()
        signals_app.reload_thumbnails.emit()
        signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class ShowAllBtn(QLabel):
    def __init__(self):
        super().__init__(text=Dynamic.lng.show_all)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(Names.th_show_all_btn)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        Dynamic.date_start, Dynamic.date_end = None, None
        JsonData.curr_coll = ALL_COLLS
        Dynamic.current_photo_limit = LIMIT

        signals_app.clear_search.emit()
        signals_app.disable_filters.emit()

        signals_app.reload_title.emit()
        signals_app.reload_thumbnails.emit()
        signals_app.reload_menu.emit()

        signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(ev)


class AboveThumbsNoImages(QWidget):
    def __init__(self, width):
        super().__init__()

        self.v_layout = LayoutV()
        self.setLayout(self.v_layout)

        noimg_t = Dynamic.lng.no_photo

        title_label = QLabel(text=noimg_t)
        title_label.setFixedWidth(width - 20)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_label.setWordWrap(True)
        self.v_layout.addWidget(title_label)
        title_label.setObjectName(Names.th_title)
        title_label.setStyleSheet(Themes.current)

        h_wid = QWidget()
        h_layout = LayoutH()
        h_wid.setLayout(h_layout)
        h_layout.setContentsMargins(0, 10, 0, 0)
        self.v_layout.addWidget(h_wid)

        merg_fltr_vals = {
            **JsonData.cust_fltr_vals,
            **JsonData.sys_fltr_vals
            }

        merg_fltr_lng = {
            **Dynamic.lng.cust_fltr_names,
            **Dynamic.lng.sys_fltr_names
            }

        if Dynamic.search_widget_text:
            noimg_t = (f"{Dynamic.lng.no_photo} {Dynamic.lng.with_name}: "
                       f"{Dynamic.search_widget_text}")

            title_label.setText(noimg_t)

            s_label = ResetSearchBtn()
            h_layout.addWidget(s_label)

        elif any((Dynamic.date_start, Dynamic.date_end)):
            noimg_t = (f"{Dynamic.lng.no_photo}: "
                       f"{Dynamic.date_start_text} - {Dynamic.date_end_text}")

            title_label.setText(noimg_t)
            h_layout.addWidget(ResetDatesBtn())

        elif any(merg_fltr_vals.values()):
            filters = (f"{merg_fltr_lng[code_name].lower()}"
                       for code_name, val in merg_fltr_vals.items()
                       if val)
            filters = ",  ".join(filters)
            noimg_t = (f"{Dynamic.lng.no_photo_filter}: {filters}")

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

        h_wid = QWidget()
        h_layout = LayoutH()
        h_wid.setLayout(h_layout)
        h_layout.setContentsMargins(0, 10, 0, 0)
        self.v_layout.addWidget(h_wid)

        if any((Dynamic.date_start, Dynamic.date_end)):
            label.setText(
                f"{Dynamic.lng.photos_named_dates}: {Dynamic.date_start_text} - {Dynamic.date_end_text}"
                )
            h_layout.addWidget(ResetDatesBtn())

            spacer = QSpacerItem(1, 10)
            self.v_layout.addSpacerItem(spacer)

        elif Dynamic.search_widget_text:
            label.setText(f"{Dynamic.lng.search}: {Dynamic.search_widget_text}")
            h_layout.addWidget(ResetSearchBtn())
            h_layout.addSpacerItem(QSpacerItem(1, 30))

            spacer = QSpacerItem(1, 10)
            self.v_layout.addSpacerItem(spacer)

        else:
            self.deleteLater()