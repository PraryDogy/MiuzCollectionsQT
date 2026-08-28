import os

from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeyEvent, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from typing_extensions import Literal

from cfg import Dynamic, JsonData, Static
from system.items import SettingsItem
from system.lang import Lng

from ._base_widgets import GrayTextLabel, ULineEditLight, UMenu
from pathlib import Path

class ClearBtn(QSvgWidget):
    clicked_ = pyqtSignal()
    icon_path = Static.COMMON_ICONS / "cancel.svg"
    icon_size = 11

    def __init__(self, parent: ULineEditLight):
        super().__init__(parent=parent)
        self.setFixedSize(self.icon_size, self.icon_size)
        self.load(str(self.icon_path))

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


class WidSearch(ULineEditLight):
    reload_thumbnails = pyqtSignal()
    open_img_search = pyqtSignal()
    ww = 162

    def __init__(self):
        super().__init__()
        self.setFixedWidth(self.ww)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(Lng.search[JsonData.lng_index])

        self.clear_btn = ClearBtn(parent=self)
        self.clear_btn.clicked_.connect(self.clear_search)
        self.clear_btn.disable()
        self.clear_btn.move(self.ww - 20, 10)

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


class BarTopBtn(QWidget):
    clicked_ = pyqtSignal()
    svg_size = 30

    def __init__(self, base_svg: Path, selected_svg: Path):
        super().__init__()
        
        self.base_svg = self._load_svg_data(base_svg)
        self.selected_svg = self._load_svg_data(selected_svg)

        self.v_lay = QVBoxLayout(self)
        self.v_lay.setContentsMargins(0, 0, 0, 0)
        self.v_lay.setSpacing(1)
        self.v_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.svg_btn = QSvgWidget()
        self.svg_btn.setFixedSize(self.svg_size, self.svg_size)
        self.v_lay.addWidget(self.svg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl = GrayTextLabel("")
        self.lbl.set_font_size(9)
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_base_style()

        for i in (base_svg, selected_svg):
            if not i.exists():
                print(" bar top btn icon not exists", i)

    def _load_svg_data(self, path: str):
        with open(path, "rb") as f:
            return QByteArray(f.read())

    def set_selected_style(self):
        self.svg_btn.load(self.selected_svg)
        self.svg_btn.update()  # Принудительное обновление кадра

    def set_base_style(self):
        self.svg_btn.load(self.base_svg)
        self.svg_btn.update()  # Принудительное обновление кадра

    def mousePressEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.set_selected_style()
        super().mousePressEvent(a0)  # Передаем событие дальше

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.set_base_style()  # Возвращаем исходный стиль при отпускании
            self.clicked_.emit()
        super().mouseReleaseEvent(a0)  # ОБЯЗАТЕЛЬНО вызываем базовый класс


class FiltersBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "filters.svg"
    selected_svg = Static.BAR_TOP_ICONS / "filters_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        self.lbl.setText(Lng.filters[JsonData.lng_index])
        

class SortBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "sort.svg"
    selected_svg = Static.BAR_TOP_ICONS / "sort_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        self.set_text()

    def set_text(self):
        """Устанавливает текст кнопки в зависимости от текущей сортировки."""
        text = (
            Lng.sort_by_mod_short[JsonData.lng_index]
            if Dynamic.sort_by_mod
            else Lng.sort_by_recent_short[JsonData.lng_index]
        )
        self.lbl.setText(text)

    def menu_clicked(self, value: bool):
        """Обрабатывает выбор сортировки из меню."""
        Dynamic.sort_by_mod = value
        self.set_text()
        self.clicked_.emit()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        """Показывает меню выбора сортировки при клике левой кнопкой мыши."""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            menu = UMenu(ev)

            # --- Создаем пункты меню ---
            act_mod = QAction(Lng.sort_by_mod[JsonData.lng_index], self, checkable=True)
            act_recent = QAction(Lng.sort_by_recent[JsonData.lng_index], self, checkable=True)

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
            self.set_base_style()


class SettingsBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "settings.svg"
    selected_svg = Static.BAR_TOP_ICONS / "settings_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        self.lbl.setText(Lng.settings[JsonData.lng_index])


class ImgSearchBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "img_search.svg"
    selected_svg = Static.BAR_TOP_ICONS / "img_search_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        self.lbl.setText(Lng.image_search_short[JsonData.lng_index])


class BarTop(QFrame):
    open_settings_win = pyqtSignal(SettingsItem)
    open_filters_win = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    open_img_search_win = pyqtSignal()
    start_text_search = pyqtSignal()
    hh = 60

    def __init__(self):
        super().__init__()
        # self.setFixedHeight(self.hh)
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 3, 0, 5)
        self.h_layout.setSpacing(15)

        self.h_layout.addStretch(0)

        # --- Кнопка сортировки ---
        self.sort_btn = SortBtn()
        self.sort_btn.clicked_.connect(self.reload_thumbnails.emit)
        self.h_layout.addWidget(self.sort_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.img_search_btn = ImgSearchBtn()
        self.img_search_btn.clicked_.connect(self.open_img_search_win.emit)
        self.h_layout.addWidget(self.img_search_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка фильтров ---
        self.filters_btn = FiltersBtn()
        self.filters_btn.clicked_.connect(self.open_filters_win.emit)
        self.h_layout.addWidget(self.filters_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- Кнопка настроек ---
        item = SettingsItem("general", "")
        self.settings_btn = SettingsBtn()
        self.settings_btn.clicked_.connect(lambda: self.open_settings_win.emit(item))
        self.h_layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.h_layout.addStretch(0)

        right_widget = QWidget()
        right_widget.setFixedWidth(WidSearch.ww)
        self.h_layout.addWidget(right_widget)
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # --- Виджет поиска ---
        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(self.start_text_search.emit)
        right_layout.addWidget(self.search_wid, alignment=Qt.AlignmentFlag.AlignRight)

        # Флаг для отслеживания состояния скролла (заглушка от спама)
        self._is_scrolled = False 

    def _update_style(self):
        """Принудительно обновляет QSS стили у виджета"""
        self.style().unpolish(self)
        self.style().polish(self)

    def handle_scroll_value(self, value: int):
        """
        Принимает позицию скролла и переключает динамическое свойство 'scrolled'.
        Обновление стиля срабатывает только при фактическом изменении состояния.
        """
        is_currently_scrolled = value > 0
        
        # Защита от спама: если состояние не изменилось, выходим
        if self._is_scrolled == is_currently_scrolled:
            return

        self._is_scrolled = is_currently_scrolled
        self.setProperty("scrolled", is_currently_scrolled)
        self._update_style()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)
