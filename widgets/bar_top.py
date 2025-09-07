from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QFrame, QLabel, QWidget

from cfg import Cfg, Dynamic, Static
from system.lang import Lng

from ._base_widgets import UHBoxLayout, UVBoxLayout
from .wid_search import WidSearch

BTN_W, BTN_H = 80, 28


class BarTopBtn(QFrame):
    clicked = pyqtSignal()
    object_name = "_frame_"
    ww_ = 65
    hh_ = 45

    def __init__(self):
        """
        QFrame с изменением стиля при наведении курсора и svg иконкой.
        """
        super().__init__()
        self.setObjectName(self.object_name)
        self.setFixedSize(self.ww_, self.hh_)

        self.v_lay = UVBoxLayout()
        self.setLayout(self.v_lay)

        self.svg_btn = QSvgWidget()
        self.svg_btn.setFixedSize(20, 20)
        self.v_lay.addWidget(self.svg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl = QLabel()
        self.lbl.setStyleSheet("font-size: 10px;")
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_normal_style()

    def set_solid_style(self):
        self.setStyleSheet(f"#{self.object_name} {{ {Static.blue_bg_style} }}")

    def set_normal_style(self):
        self.setStyleSheet(f"#{self.object_name} {{ {Static.border_transparent_style} }}")

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(a0)  # Можно оставить, если родительский класс этого требует


class DatesBtn(BarTopBtn):
    clicked_ = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.dates[Cfg.lng])
        self.svg_btn.load("./images/filter.svg")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()
            self.set_solid_style()


class FiltersBtn(BarTopBtn):
    clicked_ = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.filters[Cfg.lng])
        self.svg_btn.load("./images/filter.svg")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()


class TypesBtn(BarTopBtn):
    clicked_ = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.type_[Cfg.lng])
        self.svg_btn.load("./images/filter.svg")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()


class SortBtn(BarTopBtn):
    clicked_ = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.sort[Cfg.lng])
        self.svg_btn.load("./images/filter.svg")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()


class SettingsBtn(BarTopBtn):
    clicked_ = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.settings[Cfg.lng])
        self.svg_btn.load("./images/settings.svg")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()



class BarTop(QWidget):
    open_dates = pyqtSignal()
    open_settings = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    scroll_to_top = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.h_layout = UHBoxLayout()
        self.setLayout(self.h_layout)
        self.filter_btns = []
        self.win_dates = None
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        self.filter_btns.clear()

        self.h_layout.addStretch(1)


        # сортировка по слоям по джепегам: добавим их в фильтры
        self.filters_btn = FiltersBtn()
        self.filters_btn.clicked_.connect(lambda: self.open_settings.emit())
        self.h_layout.addWidget(
            self.filters_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.dates_btn = DatesBtn()
        self.dates_btn.clicked_.connect(lambda: self.open_dates.emit())
        self.h_layout.addWidget(
            self.dates_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.settings_btn = SettingsBtn()
        self.settings_btn.clicked_.connect(lambda: self.open_settings.emit())
        self.h_layout.addWidget(
            self.settings_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.h_layout.addStretch(1)

        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.search_wid.scroll_to_top.connect(lambda: self.scroll_to_top.emit())
        self.h_layout.addWidget(
            self.search_wid,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        # if any((Dynamic.date_start, Dynamic.date_end)):
        #     self.dates_btn.set_solid_style()
        # else:
        #     self.dates_btn.set_normal_style()
    