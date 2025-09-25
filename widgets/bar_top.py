from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QFrame, QLabel, QWidget

from cfg import Cfg, Dynamic, Static
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import SettingsItem, UHBoxLayout, UMenu, UVBoxLayout
from .wid_search import WidSearch


class BarTopBtn(QFrame):
    """
    QFrame с иконкой SVG (в отдельном фрейме) и подписью.
    Меняет стиль только иконки при наведении/клике, текст остаётся неизменным.
    """

    clicked_ = pyqtSignal()
    object_name = "_frame_"
    ww, hh = 65, 45
    svg_ww, svg_hh = 23, 23
    font_size = 10

    # --- Стили ---
    gray_bg_style = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: rgba(125, 125, 125, 0.5);
        border: 1px solid transparent;
    """
    border_transparent_style = """
        border: 1px solid transparent;
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(self.ww, self.hh)

        # --- Компоновка ---
        self.v_lay = UVBoxLayout()
        self.setLayout(self.v_lay)

        # --- Фрейм под SVG ---
        self.svg_frame = QFrame()
        self.svg_frame.setObjectName(self.object_name)
        self.svg_frame.setFixedSize(self.svg_ww + 12, self.svg_hh + 6)
        self.svg_lay = UVBoxLayout()
        self.svg_frame.setLayout(self.svg_lay)

        # --- SVG-иконка ---
        self.svg_btn = QSvgWidget()
        self.svg_btn.setFixedSize(self.svg_ww, self.svg_hh)
        self.svg_lay.addWidget(self.svg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Подпись ---
        self.lbl = QLabel()
        self.lbl.setStyleSheet(f"font-size: {self.font_size}px;")

        # --- Добавляем в корневой layout ---
        self.v_lay.addWidget(self.svg_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Стиль по умолчанию ---
        self.set_normal_style()

    def set_solid_style(self):
        """Применяет сплошной серый фон только к svg_frame."""
        self.svg_frame.setStyleSheet(f"#{self.object_name} {{ {self.gray_bg_style} }}")

    def set_normal_style(self):
        """Применяет прозрачный бордер только к svg_frame."""
        self.svg_frame.setStyleSheet(f"#{self.object_name} {{ {self.border_transparent_style} }}")

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
    edit_filters = pyqtSignal(SettingsItem)

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.filters[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)
        
    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:

        def on_action(val: str):
            """Добавляет или удаляет фильтр из списка включённых и испускает сигнал."""
            if val in Dynamic.filters_enabled:
                Dynamic.filters_enabled.remove(val)
            else:
                Dynamic.filters_enabled.append(val)
            self.clicked_.emit()
        
        def reset():
            """Сбрасывает все фильтры и испускает сигнал."""
            Dynamic.filters_enabled.clear()
            self.clicked_.emit()
   
        def edit_filters():
            item = SettingsItem()
            item.action_type = item.type_filters
            self.edit_filters.emit(item)

        def favs_cmd():
            Dynamic.filter_favs = not Dynamic.filter_favs
            self.clicked_.emit()

        def only_folder_cmd():
            Dynamic.filter_only_folder = not Dynamic.filter_only_folder
            self.clicked_.emit()

        """Показывает меню фильтров при клике левой кнопкой мыши."""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.set_solid_style()
            menu = UMenu(self)
            menu.setMinimumWidth(self.menu_ww)

            favs = QAction(Lng.favorites[Cfg.lng], self, checkable=True)
            favs.setChecked(Dynamic.filter_favs)
            favs.triggered.connect(favs_cmd)
            menu.addAction(favs)

            only_folder = QAction(Lng.only_this_folder[Cfg.lng], self, checkable=True)
            only_folder.setChecked(Dynamic.filter_only_folder)
            only_folder.triggered.connect(only_folder_cmd)
            menu.addAction(only_folder)

            menu.addSeparator()

            # --- Добавляем фильтры ---
            for f in Filters.filters:
                act = QAction(f, self, checkable=True)
                act.setChecked(f in Dynamic.filters_enabled)
                act.triggered.connect(lambda _, val=f: on_action(val))
                menu.addAction(act)

            # --- Разделитель и пункт сброса ---
            menu.addSeparator()

            edit = QAction(Lng.setup[Cfg.lng], self)
            edit.triggered.connect(edit_filters)
            menu.addAction(edit)
            
            act_reset = QAction(Lng.reset[Cfg.lng], menu)
            act_reset.triggered.connect(reset)
            menu.addAction(act_reset)

            # --- Показ меню под кнопкой ---
            pos = self.mapToGlobal(self.rect().bottomLeft())
            menu.exec(pos)

            filters = (
                *Dynamic.filters_enabled,
                Dynamic.filter_favs,
                Dynamic.filter_only_folder
            )

            if not any(filters):
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


class BackBtn(BarTopBtn):
    ICON_PATH = "./images/arrow_back.svg"

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.back[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)

    def mouseReleaseEvent(self, a0):
        def cmd():
            ind = Dynamic.history.index(Dynamic.current_dir) - 1
            if ind >= 0:
                Dynamic.current_dir = Dynamic.history[ind]
                self.clicked_.emit()
        try:
            cmd()
        except Exception as e:
            print("BackBtn error", e)


class NextBtn(BarTopBtn):
    ICON_PATH = "./images/arrow_next.svg"

    def __init__(self):
        super().__init__()
        self.lbl.setText(Lng.next_[Cfg.lng])
        self.svg_btn.load(self.ICON_PATH)

    def mouseReleaseEvent(self, a0):
        def cmd():
            ind = Dynamic.history.index(Dynamic.current_dir) + 1
            if ind >= 0:
                Dynamic.current_dir = Dynamic.history[ind]
                self.clicked_.emit()
        try:
            cmd()
        except Exception as e:
            print("BackBtn error", e)


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
    reload_thumbnails = pyqtSignal()
    history_press = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.h_layout = UHBoxLayout()
        self.setLayout(self.h_layout)

        self.back_btn = BackBtn()
        self.back_btn.clicked_.connect(lambda: self.history_press.emit())
        self.h_layout.addWidget(self.back_btn)

        self.next_btn = NextBtn()
        self.h_layout.addWidget(self.next_btn)

        self.h_layout.addStretch(1)

        # --- Кнопка сортировки ---
        self.sort_btn = SortBtn()
        self.sort_btn.clicked_.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(self.sort_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка фильтров ---
        self.filters_btn = FiltersBtn()
        self.filters_btn.clicked_.connect(lambda: self.reload_thumbnails.emit())
        self.filters_btn.edit_filters.connect(self.open_settings_win.emit)
        self.h_layout.addWidget(self.filters_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка выбора даты ---
        self.dates_btn = DatesBtn()
        self.dates_btn.clicked_.connect(lambda: self.open_dates_win.emit())
        self.h_layout.addWidget(self.dates_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка настроек ---
        item = SettingsItem()
        item.action_type = item.type_general
        self.settings_btn = SettingsBtn()
        self.settings_btn.clicked_.connect(lambda: self.open_settings_win.emit(item))
        self.h_layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.h_layout.addStretch(1)

        # --- Виджет поиска ---
        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(self.search_wid, alignment=Qt.AlignmentFlag.AlignRight)

        self.h_layout.setContentsMargins(0, 2, 0, 2)
        self.adjustSize()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)