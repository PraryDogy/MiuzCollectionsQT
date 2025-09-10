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

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.filters[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)

    def _on_action(self, val: str):
        """Добавляет или удаляет фильтр из списка включённых и испускает сигнал."""
        if val in Dynamic.enabled_filters:
            Dynamic.enabled_filters.remove(val)
        else:
            Dynamic.enabled_filters.append(val)
        self.clicked_.emit()

    def reset(self):
        """Сбрасывает все фильтры и испускает сигнал."""
        Dynamic.enabled_filters.clear()
        self.clicked_.emit()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        """Показывает меню фильтров при клике левой кнопкой мыши."""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.set_solid_style()
            menu = UMenu(self)
            menu.setMinimumWidth(self.menu_ww)

            # --- Добавляем фильтры ---
            for f in Filters.filters:
                act = QAction(f, self, checkable=True)
                act.setChecked(f in Dynamic.enabled_filters)
                act.triggered.connect(lambda _, val=f: self._on_action(val))
                menu.addAction(act)

            # --- Разделитель и пункт сброса ---
            menu.addSeparator()
            act_reset = QAction(Lng.reset[Cfg.lng], menu)
            act_reset.triggered.connect(self.reset)
            menu.addAction(act_reset)

            # --- Показ меню под кнопкой ---
            pos = self.mapToGlobal(self.rect().bottomLeft())
            menu.exec(pos)

            # --- Если фильтры пусты, вернуть обычный стиль ---
            if not Dynamic.enabled_filters:
                self.set_normal_style()


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
    open_dates_win = pyqtSignal()
    open_settings_win = pyqtSignal()
    reload_thumbnails = pyqtSignal()

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
        self.h_layout.addWidget(
            self.sort_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        # сортировка по слоям по джепегам: добавим их в фильтры
        self.filters_btn = FiltersBtn()
        self.filters_btn.clicked_.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(
            self.filters_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.dates_btn = DatesBtn()
        self.dates_btn.clicked_.connect(lambda: self.open_dates_win.emit())
        self.h_layout.addWidget(
            self.dates_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.settings_btn = SettingsBtn()
        self.settings_btn.clicked_.connect(lambda: self.open_settings_win.emit())
        self.h_layout.addWidget(
            self.settings_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.h_layout.addStretch(1)

        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(
            self.search_wid,
            alignment=Qt.AlignmentFlag.AlignRight
        )
