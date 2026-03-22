from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFrame, QLabel, QWidget

from cfg import Cfg, Dynamic
from system.items import SettingsItem
from system.lang import Lng

from ._base_widgets import UHBoxLayout, UMenu, UVBoxLayout
from .wid_search import WidSearch


class UFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("uFrame")
        self.normal_style()

    def normal_style(self):
        self.setStyleSheet("""
            QFrame#uFrame {
                background: transparent;
                padding-left: 2px;
                padding-right: 2px;
            }
        """)

    def solid_style(self):
        self.setStyleSheet("""
            QFrame#uFrame {
                background: rgba(125, 125, 125, 0.5);
                border-radius: 7px;
                padding-left: 2px;
                padding-right: 2px;
            }
        """)


class BarTopBtn(QWidget):
    """
    QFrame с иконкой SVG (в отдельном фрейме) и подписью.
    Меняет стиль только иконки при наведении/клике, текст остаётся неизменным.
    """

    clicked_ = pyqtSignal()
    width_ = 40
    height_ = 35
    svg_size = 20


    def __init__(self):
        super().__init__()
        
        self.v_lay = UVBoxLayout()
        self.v_lay.setSpacing(1)
        self.v_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.v_lay)

        # --- Фрейм под SVG ---
        self.svg_frame = UFrame()
        self.svg_frame.setFixedSize(self.width_, self.height_)
        self.svg_lay = UVBoxLayout()
        self.svg_frame.setLayout(self.svg_lay)
        self.v_lay.addWidget(self.svg_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- SVG-иконка ---
        self.svg_btn = QSvgWidget()
        self.svg_btn.setFixedSize(self.svg_size, self.svg_size)
        self.svg_lay.addWidget(self.svg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Подпись ---
        self.lbl = QLabel()
        self.lbl.setStyleSheet(f"font-size: 10px;")
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_solid_style(self):
        self.svg_frame.solid_style()

    def set_normal_style(self):
        self.svg_frame.normal_style()

    def mouseReleaseEvent(self, a0):
        """Испускает сигнал при клике левой кнопкой мыши."""
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()


class DatesBtn(BarTopBtn):
    """
    Кнопка для выбора даты с SVG-иконкой календаря и подписью.
    
    Особенности:
        - Испускает сигнал `clicked_` при клике.
        - Меняет стиль на сплошной при нажатии.
        - Использует SVG-иконку календаря.
    """

    ICON_PATH = "./images/calendar.svg"

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.dates[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        """Испускает сигнал и применяет сплошной стиль при клике левой кнопкой мыши."""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()
            self.set_solid_style()


class FiltersBtn(BarTopBtn):
    """
    Кнопка для управления фильтрами с SVG-иконкой.

    Особенности:
        - Отображает список фильтров через выпадающее меню.
        - Позволяет включать/выключать фильтры.
        - Сигнал `clicked_` испускается при изменении фильтров.
        - Имеет пункт сброса всех фильтров.
    """

    ICON_PATH = "./images/filters.svg"
    menu_ww = 200
    # edit_filters = pyqtSignal(SettingsItem)

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.filters[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)
        

class SortBtn(BarTopBtn):
    """
    Кнопка для выбора порядка сортировки с SVG-иконкой.

    Особенности:
        - Отображает текущий способ сортировки (по модификации или по дате).
        - Сигнал `clicked_` испускается при изменении сортировки.
        - Выпадающее меню позволяет выбрать способ сортировки.
    """

    ICON_PATH = "./images/sort.svg"

    def __init__(self):
        super().__init__()
        self.svg_btn.load(self.ICON_PATH)
        self.set_text()

    def set_text(self):
        """Устанавливает текст кнопки в зависимости от текущей сортировки."""
        text = Lng.sort_by_mod_short[Cfg.lng] if Dynamic.sort_by_mod else Lng.sort_by_recent_short[Cfg.lng]
        self.lbl.setText(text)

    def menu_clicked(self, value: bool):
        """Обрабатывает выбор сортировки из меню."""
        Dynamic.sort_by_mod = value
        self.set_text()
        self.clicked_.emit()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        """Показывает меню выбора сортировки при клике левой кнопкой мыши."""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.set_solid_style()
            menu = UMenu(ev)

            # --- Создаем пункты меню ---
            act_mod = QAction(Lng.sort_by_mod[Cfg.lng], self, checkable=True)
            act_recent = QAction(Lng.sort_by_recent[Cfg.lng], self, checkable=True)

            act_mod.setChecked(Dynamic.sort_by_mod)
            act_recent.setChecked(not Dynamic.sort_by_mod)

            act_mod.triggered.connect(lambda: self.menu_clicked(True))
            act_recent.triggered.connect(lambda: self.menu_clicked(False))

            menu.addAction(act_mod)
            menu.addAction(act_recent)

            # --- Показ меню под кнопкой ---
            pos = self.mapToGlobal(self.rect().bottomLeft())
            menu.exec(pos)

            # --- Вернуть нормальный стиль после закрытия меню ---
            self.set_normal_style()


class SettingsBtn(BarTopBtn):
    """
    Кнопка для открытия окна настроек с SVG-иконкой.

    Особенности:
        - Испускает сигнал `clicked_` при клике.
        - Отображает подпись "Настройки".
    """

    ICON_PATH = "./images/settings.svg"

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.settings[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)


class BarTop(QWidget):
    """
    Верхняя панель с кнопками управления и поиском.

    Сигналы:
        open_dates_win: открывает окно выбора даты.
        open_settings_win: открывает окно настроек.
        reload_thumbnails: обновляет миниатюры при изменении фильтров или сортировки.

    Атрибуты:
        sort_btn: кнопка сортировки.
        filters_btn: кнопка фильтров.
        dates_btn: кнопка открытия окна выбора даты.
        settings_btn: кнопка настроек.
        search_wid: виджет поиска.
    """

    open_dates_win = pyqtSignal()
    open_settings_win = pyqtSignal(SettingsItem)
    open_filters_win = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    history_press = pyqtSignal()
    level_up = pyqtSignal()
    text_height = 53
    text_spacing = 15

    def __init__(self):
        super().__init__()
        self.setFixedHeight(self.text_height)
        self.h_layout = UHBoxLayout()
        self.h_layout.setContentsMargins(0, 3, 0, 3)
        self.h_layout.setSpacing(self.text_spacing)
        self.setLayout(self.h_layout)

        self.h_layout.addStretch(0)

        # --- Кнопка сортировки ---
        self.sort_btn = SortBtn()
        self.sort_btn.clicked_.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(self.sort_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка фильтров ---
        self.filters_btn = FiltersBtn()
        self.filters_btn.clicked_.connect(self.open_filters_win.emit)
        self.h_layout.addWidget(self.filters_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка выбора даты ---
        self.dates_btn = DatesBtn()
        self.dates_btn.clicked_.connect(lambda: self.open_dates_win.emit())
        self.h_layout.addWidget(self.dates_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка настроек ---
        item = SettingsItem("general", "")
        self.settings_btn = SettingsBtn()
        self.settings_btn.clicked_.connect(lambda: self.open_settings_win.emit(item))
        self.h_layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.h_layout.addStretch()

        # --- Виджет поиска ---
        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(self.search_wid, alignment=Qt.AlignmentFlag.AlignRight)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)