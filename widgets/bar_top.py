from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QFrame, QLabel, QWidget

from cfg import Cfg, Dynamic, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import UHBoxLayout, UMenu, UVBoxLayout
from .wid_search import WidSearch


class BarTopBtn(QFrame):
    """
    QFrame с иконкой SVG и подписью, который изменяет стиль при наведении
    и испускает сигнал при клике.

    Сигналы:
        clicked_ (pyqtSignal): испускается при клике мышью на виджет.

    Атрибуты:
        object_name (str): имя объекта для CSS.
        ww, hh (int): размеры виджета.
        svg_ww, svg_hh (int): размеры SVG-иконки.
        font_size (int): размер шрифта подписи.
        gray_bg_style (str): CSS стиль с серым фоном.
        border_transparent_style (str): CSS стиль с прозрачным бордером.
    """

    clicked_ = pyqtSignal()
    object_name = "_frame_"
    ww, hh = 65, 45
    svg_ww, svg_hh = 20, 20
    font_size = 10

    # --- Стили ---
    gray_bg_style = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: rgba(130, 130, 130, 0.5);
        border: 1px solid transparent;
        padding-left: 2px;
        padding-right: 2px;
    """
    border_transparent_style = f"""
        border: 1px solid transparent;
        padding-left: 2px;
        padding-right: 2px;
    """

    def __init__(self):
        super().__init__()
        self.setObjectName(self.object_name)
        self.setFixedSize(self.ww, self.hh)

        # --- Компоновка ---
        self.v_lay = UVBoxLayout()
        self.setLayout(self.v_lay)

        # --- SVG-иконка ---
        self.svg_btn = QSvgWidget()
        self.svg_btn.setFixedSize(self.svg_ww, self.svg_hh)
        self.v_lay.addWidget(self.svg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Подпись ---
        self.lbl = QLabel()
        self.lbl.setStyleSheet(f"font-size: {self.font_size}px;")
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Стиль по умолчанию ---
        self.set_normal_style()

    def set_solid_style(self):
        """Применяет сплошной серый фон."""
        self.setStyleSheet(f"#{self.object_name} {{ {self.gray_bg_style} }}")

    def set_normal_style(self):
        """Применяет прозрачный бордер."""
        self.setStyleSheet(f"#{self.object_name} {{ {self.border_transparent_style} }}")

    def mouseReleaseEvent(self, a0):
        """Испускает сигнал при клике левой кнопкой мыши."""
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()


class DatesBtn(BarTopBtn):
    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.dates[Cfg.lng])
        self.svg_btn.load("./images/calendar.svg")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()
            self.set_solid_style()


class FiltersBtn(BarTopBtn):
    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.filters[Cfg.lng])
        self.svg_btn.load("./images/filters.svg")

    def _on_action(self, val: str):
        if val in Dynamic.enabled_filters:
            Dynamic.enabled_filters.remove(val)
        else:
            Dynamic.enabled_filters.append(val)
        self.clicked_.emit()

    def reset(self):
        Dynamic.enabled_filters.clear()
        self.clicked_.emit()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.set_solid_style()
            menu = UMenu(self)
            menu.setMinimumWidth(200)

            for f in Filters.filters:
                act = QAction(f, self, checkable=True)
                act.setChecked(f in Dynamic.enabled_filters)
                act.triggered.connect(lambda _, val=f: self._on_action(val))
                menu.addAction(act)

            menu.addSeparator()
            act = QAction(Lng.reset[Cfg.lng], menu)
            act.triggered.connect(self.reset)
            menu.addAction(act)

            pos = self.mapToGlobal(self.rect().bottomLeft())
            menu.exec(pos)

            if not Dynamic.enabled_filters:
                self.set_normal_style()


class SortBtn(BarTopBtn):
    def __init__(self):
        super().__init__()
        self.svg_btn.load("./images/sort.svg")
        self.set_text()

    def set_text(self):
        if Dynamic.sort_by_mod:
            text = Lng.sort_by_mod_short[Cfg.lng]
        else:
            text = Lng.sort_by_recent_short[Cfg.lng]
        self.lbl.setText(text)

    def menu_clicked(self, value: bool):
        Dynamic.sort_by_mod = value
        self.set_text()
        self.clicked_.emit()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.set_solid_style()
            menu = UMenu(ev)

            act1 = QAction(Lng.sort_by_mod[Cfg.lng], self, checkable=True)
            act2 = QAction(Lng.sort_by_recent[Cfg.lng], self, checkable=True)

            # состояние — допустим, у тебя есть self.sort_by_mod_flag: bool
            act1.setChecked(Dynamic.sort_by_mod)
            act2.setChecked(not Dynamic.sort_by_mod)

            act1.triggered.connect(lambda: self.menu_clicked(True))
            act2.triggered.connect(lambda: self.menu_clicked(False))

            menu.addAction(act1)
            menu.addAction(act2)

            pos = self.mapToGlobal(self.rect().bottomLeft())
            menu.exec(pos)
            self.set_normal_style()


class SettingsBtn(BarTopBtn):
    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.settings[Cfg.lng])
        self.svg_btn.load("./images/settings.svg")


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

        self.sort_btn = SortBtn()
        self.sort_btn.clicked_.connect(lambda: self.reload_thumbnails.emit())
        self.sort_btn.clicked_.connect(lambda: self.scroll_to_top.emit())
        self.h_layout.addWidget(
            self.sort_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        # сортировка по слоям по джепегам: добавим их в фильтры
        self.filters_btn = FiltersBtn()
        self.filters_btn.clicked_.connect(lambda: self.reload_thumbnails.emit())
        self.filters_btn.clicked_.connect(lambda: self.scroll_to_top.emit())
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
