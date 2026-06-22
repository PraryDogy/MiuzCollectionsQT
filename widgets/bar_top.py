from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QFrame, QLabel, QWidget

from cfg import Cfg, Dynamic
from system.items import SettingsItem
from system.lang import Lng

from ._base_widgets import UHBoxLayout, ULineEdit, UMenu, UVBoxLayout


class ClearBtn(QSvgWidget):
    clicked_ = pyqtSignal()
    svg_clear = "./images/clear.svg"
    svg_size = 14

    def __init__(self, parent: ULineEdit):
        super().__init__(parent=parent)
        self.setFixedSize(self.svg_size, self.svg_size)
        self.load(self.svg_clear)

    def disable(self):
        self.hide()
        self.setDisabled(True)

    def enable(self):
        self.show()
        self.setDisabled(False)

    def mouseReleaseEvent(self, ev):
        self.clicked_.emit()

    def enterEvent(self, a0):
        self.setCursor(Qt.CursorShape.ArrowCursor)


class WidSearch(ULineEdit):
    reload_thumbnails = pyqtSignal()
    open_img_search = pyqtSignal()
    ww = 162

    def __init__(self):
        super().__init__()
        self.setFixedWidth(self.ww)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(Lng.search[Cfg.lng_index])

        self.clear_btn = ClearBtn(parent=self)
        self.clear_btn.clicked_.connect(self.clear_search)
        self.clear_btn.disable()
        self.clear_btn.move(
            self.width() - ClearBtn.svg_size - 8,
            (ClearBtn.svg_size * 2) // 4
        )

    def create_search(self, new_text):
        if len(new_text) > 0:
            Dynamic.search_widget_text = new_text
            self.clear_btn.enable()
        else:
            Dynamic.search_widget_text = None
            self.clear_btn.disable()

    def delayed_search(self):
        self.reload_thumbnails.emit()

    def clear_search(self):
        self.clear()
        Dynamic.search_widget_text = None
        Dynamic.loaded_thumbs = 0
        Dynamic.thumb_path_set.clear()
        self.reload_thumbnails.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.delayed_search()
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)
    
    
    def mouseDoubleClickEvent(self, a0):
        self.open_img_search.emit()
        return super().mouseDoubleClickEvent(a0)
    

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
        self.lbl.setText(Lng.dates[Cfg.lng_index])
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
        self.lbl.setText(Lng.filters[Cfg.lng_index])
        self.svg_btn.load(self.ICON_PATH)
        

class SortBtn(BarTopBtn):
    ICON_PATH = "./images/sort.svg"

    def __init__(self):
        super().__init__()
        self.svg_btn.load(self.ICON_PATH)
        self.set_text()

    def set_text(self):
        """Устанавливает текст кнопки в зависимости от текущей сортировки."""
        text = Lng.sort_by_mod_short[Cfg.lng_index] if Dynamic.sort_by_mod else Lng.sort_by_recent_short[Cfg.lng_index]
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
            act_mod = QAction(Lng.sort_by_mod[Cfg.lng_index], self, checkable=True)
            act_recent = QAction(Lng.sort_by_recent[Cfg.lng_index], self, checkable=True)

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
        self.lbl.setText(Lng.settings[Cfg.lng_index])
        self.svg_btn.load(self.ICON_PATH)


class ExitImgSearchBtn(UFrame):
    clicked_ = pyqtSignal()
    ICON_PATH = "./images/clear.svg"
    svg_size = 15
    hh = 30
    def __init__(self):
        super().__init__()
        h_layout = UHBoxLayout(self)
        h_layout.setContentsMargins(2, 0, 2, 0)
        h_layout.setSpacing(10)

        h_layout.addStretch()

        text_label = QLabel("Закрыть поиск")
        h_layout.addWidget(text_label)

        svg_widget = ClearBtn(self)
        h_layout.addWidget(svg_widget)

        self.solid_style()
        self.setFixedHeight(self.hh)

    def mouseReleaseEvent(self, a0):
        self.clicked_.emit()
        return super().mouseReleaseEvent(a0)


class BarTop(QWidget):
    open_dates_win = pyqtSignal()
    open_settings_win = pyqtSignal(SettingsItem)
    open_filters_win = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    history_press = pyqtSignal()
    level_up = pyqtSignal()
    open_img_search = pyqtSignal()
    exit_img_search = pyqtSignal()
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

        self.h_layout.addStretch(0)

        right_widget = QWidget()
        right_widget.setFixedWidth(WidSearch.ww)
        self.h_layout.addWidget(right_widget)
        right_layout = UHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # --- Виджет поиска ---
        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.search_wid.open_img_search.connect(lambda: self.open_img_search.emit())
        right_layout.addWidget(self.search_wid, alignment=Qt.AlignmentFlag.AlignRight)

        self.exit_search_btn = ExitImgSearchBtn()
        self.exit_search_btn.clicked_.connect(self.exit_img_search.emit)
        right_layout.addWidget(self.exit_search_btn, alignment=Qt.AlignmentFlag.AlignRight)
        self.exit_search_btn.hide()

    def show_img_search(self):
        self.search_wid.hide()
        self.exit_search_btn.show()        

    def show_base_search(self):
        self.search_wid.show()
        self.exit_search_btn.hide()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)