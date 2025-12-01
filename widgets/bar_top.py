from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QFrame, QLabel, QSpacerItem, QWidget

from cfg import Dynamic, Static, cfg
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import SettingsItem, UHBoxLayout, UMenu, UVBoxLayout
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
        self.lbl.setText(Lng.dates[cfg.lng])
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
        self.lbl.setText(Lng.filters[cfg.lng])
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

            favs = QAction(Lng.favorites[cfg.lng], self, checkable=True)
            favs.setChecked(Dynamic.filter_favs)
            favs.triggered.connect(favs_cmd)
            menu.addAction(favs)

            only_folder = QAction(Lng.only_this_folder[cfg.lng], self, checkable=True)
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

            edit = QAction(Lng.setup[cfg.lng], self)
            edit.triggered.connect(edit_filters)
            menu.addAction(edit)
            
            act_reset = QAction(Lng.reset[cfg.lng], menu)
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
        text = Lng.sort_by_mod_short[cfg.lng] if Dynamic.sort_by_mod else Lng.sort_by_recent_short[cfg.lng]
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
            act_mod = QAction(Lng.sort_by_mod[cfg.lng], self, checkable=True)
            act_recent = QAction(Lng.sort_by_recent[cfg.lng], self, checkable=True)

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
        self.lbl.setText(Lng.settings[cfg.lng])
        self.svg_btn.load(self.ICON_PATH)


class HistoryNavBtn(BarTopBtn):
    """
    Базовый класс для кнопок навигации по истории.
    direction: int = -1 для "назад", +1 для "вперед"
    """
    ICON_PATH = ""
    direction: int = -1

    def __init__(self):
        super().__init__()
        self.svg_btn.load(self.ICON_PATH)

    def mouseReleaseEvent(self, a0):
        try:
            self.set_solid_style()
            QTimer.singleShot(100, self.set_normal_style)
            if Dynamic.current_dir not in Dynamic.history:
                return  # нет текущей позиции
            curr_ind = Dynamic.history.index(Dynamic.current_dir)
            new_ind = curr_ind + self.direction
            if 0 <= new_ind < len(Dynamic.history):
                Dynamic.current_dir = Dynamic.history[new_ind]
                self.clicked_.emit()
        except Exception as e:
            print("HistoryNavBtn error", e)


class BackBtn(HistoryNavBtn):
    ICON_PATH = "./images/arrow_back.svg"
    def __init__(self):
        super().__init__()
        self.direction = -1
        self.lbl.setText(Lng.back[cfg.lng])


class NextBtn(HistoryNavBtn):
    ICON_PATH = "./images/arrow_next.svg"
    def __init__(self):
        super().__init__()
        self.direction = +1
        self.lbl.setText(Lng.forward[cfg.lng])


class LevelUpBtn(BarTopBtn):
    ICON_PATH = "./images/level_up.svg"
    def __init__(self):
        super().__init__()
        self.svg_btn.load(self.ICON_PATH)
        self.lbl.setText(Lng.level_up[cfg.lng])

    def mouseReleaseEvent(self, a0):
        try:
            self.set_solid_style()
            QTimer.singleShot(100, self.set_normal_style)
            self.clicked_.emit()
        except Exception as e:
            print("HistoryNavBtn error", e)

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
    level_up = pyqtSignal()
    text_height = 53

    def __init__(self):
        super().__init__()
        self.setFixedHeight(self.text_height)
        self.h_layout = UHBoxLayout()
        self.h_layout.setContentsMargins(0, 3, 0, 3)
        self.h_layout.setSpacing(0)
        self.setLayout(self.h_layout)

        self.back_btn = BackBtn()
        self.back_btn.clicked_.connect(lambda: self.history_press.emit())
        self.h_layout.addWidget(self.back_btn)

        self.next_btn = NextBtn()
        self.next_btn.clicked_.connect(lambda: self.history_press.emit())
        self.h_layout.addWidget(self.next_btn)

        self.level_up_btn = LevelUpBtn()
        self.level_up_btn.clicked_.connect(lambda: self.level_up.emit())
        self.h_layout.addWidget(self.level_up_btn)

        self.h_layout.addStretch(1)
        self.h_layout.addSpacerItem(QSpacerItem(25, 0))

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
        self.h_layout.addSpacerItem(QSpacerItem(25, 0))

        # --- Виджет поиска ---
        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.h_layout.addWidget(self.search_wid, alignment=Qt.AlignmentFlag.AlignRight)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)