import os

from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeyEvent, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from typing_extensions import Literal

from cfg import Cfg, Dynamic, Static
from system.items import SettingsItem
from system.lang import Lng

from ._base_widgets import ULineEdit, UMenu


class ClearBtn(QSvgWidget):
    clicked_ = pyqtSignal()
    icon_path = os.path.join(Static.internal_images, "clear.svg")
    icon_size = 14

    def __init__(self, parent: ULineEdit):
        super().__init__(parent=parent)
        self.setFixedSize(self.icon_size, self.icon_size)
        self.load(self.icon_path)

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
        self.clear_btn.move(self.ww - 20, 8)

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

    def __init__(self, filename: Literal["sort", "filters", "calendar", "settings"]):
        super().__init__()
        self.filename = filename
        self.normal_svg_data = self._load_svg_data(f"{filename}.svg")
        self.solid_svg_data = self._load_svg_data(f"{filename}_selected.svg")

        self.v_lay = QVBoxLayout(self)
        self.v_lay.setContentsMargins(0, 0, 0, 0)
        self.v_lay.setSpacing(1)
        self.v_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.svg_btn = QSvgWidget()
        self.svg_btn.setFixedSize(self.svg_size, self.svg_size)
        self.v_lay.addWidget(self.svg_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Подпись ---
        self.lbl = QLabel()
        self.lbl.setStyleSheet("font-size: 10px;")
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_normal_style()

    def _load_svg_data(self, icon_name: str):
        path = os.path.join(Static.internal_images, icon_name)
        with open(path, "rb") as f:
            return QByteArray(f.read())

    def set_solid_style(self):
        self.svg_btn.load(self.solid_svg_data)

    def set_normal_style(self):
        self.svg_btn.load(self.normal_svg_data)
    

    def mouseReleaseEvent(self, a0):
        """Испускает сигнал при клике левой кнопкой мыши."""
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()


class DatesBtn(BarTopBtn):
    filename = "calendar"

    def __init__(self):
        super().__init__(self.filename)
        self.lbl.setText(Lng.dates[Cfg.lng_index])

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        """Испускает сигнал и применяет сплошной стиль при клике левой кнопкой мыши."""
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()
            self.set_solid_style()


class FiltersBtn(BarTopBtn):
    filename = "filters"

    def __init__(self):
        super().__init__(self.filename)
        self.lbl.setText(Lng.filters[Cfg.lng_index])
        

class SortBtn(BarTopBtn):
    filename = "sort"

    def __init__(self):
        super().__init__(self.filename)
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
    filename = "settings"

    def __init__(self):
        super().__init__(self.filename)
        self.lbl.setText(Lng.settings[Cfg.lng_index])


class ExitImgSearchBtn(QFrame):
    clicked_ = pyqtSignal()
    ICON_PATH = os.path.join(Static.internal_images, "clear.svg")
    icon_size = 15
    hh = 30
    def __init__(self):
        super().__init__()
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(2, 0, 2, 0)
        h_layout.setSpacing(5)

        h_layout.addStretch()

        text_label = QLabel(Lng.close_search[Cfg.lng_index])
        h_layout.addWidget(text_label)

        icon_container = QWidget()
        icon_container.setFixedSize(14, 18)
        h_layout.addWidget(icon_container)

        svg_widget = ClearBtn(self)
        svg_widget.setParent(icon_container)
        svg_widget.move(0, 2)

        # self.solid_style()
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
    open_img_search = pyqtSignal()
    exit_img_search = pyqtSignal()
    open_base_search = pyqtSignal()
    hh = 60

    def __init__(self):
        super().__init__()
        self.setFixedHeight(self.hh)
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 3, 0, 3)
        self.h_layout.setSpacing(15)

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
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # --- Виджет поиска ---
        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.open_base_search.emit())
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