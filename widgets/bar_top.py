from pathlib import Path

from PyQt6.QtCore import QByteArray, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import (TransparentFrame, TransparentLabel,
                            TransparentWidget, ULineEdit, UMenu, UPushButton)
from .win_text_search import WinTextSearch

BTN_H = 27



class SearchWidBaseSvg(QSvgWidget):
    clicked_ = pyqtSignal()
    icon_path = None  # Переопределяется в наследниках
    icon_size = 11

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(self.icon_size, self.icon_size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.icon_path:
            self.load(str(self.icon_path))
        self.hide()

    def enable(self):
        self.show()

    def disable(self):
        self.hide()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)


class SearchWidClearSvg(SearchWidBaseSvg):
    icon_path = Static.COMMON_ICONS / "cancel.svg"
    right_margin = 8  # Отступ крайней кнопки от правого края


class SearchWidTextSearchSvg(SearchWidBaseSvg):
    icon_path = Static.COMMON_ICONS / "list_view.svg" 
    spacing = 10  # Расстояние между этой кнопкой и кнопкой очистки


class SearchWidLineEdit(ULineEdit):
    reload_thumbnails = pyqtSignal()
    ww = 162

    def __init__(self):
        super().__init__()
        self.setFixedHeight(BTN_H)
        self.setMinimumWidth(self.ww)
        self.setMaximumWidth(self.ww * 2)

        self.textChanged.connect(self.create_search)

        # Кнопка Очистки (правая)
        self.clear_btn = SearchWidClearSvg(self)
        self.clear_btn.clicked_.connect(self.clear_search)

        # Новая кнопка (левая)
        self.left_btn = SearchWidTextSearchSvg(self)
        self.left_btn.clicked_.connect(self.open_win_text_search) # Подключите ваш метод

        self.update_buttons_position()

    def open_win_text_search(self):
        text = ", ".join(Dynamic.search_words_list)
        self.win_text_search = WinTextSearch(text)
        self.win_text_search.ok_clicked.connect(self.win_text_search_cmd)
        self.win_text_search.center_to_parent(self.window())
        self.win_text_search.show()

    def update_placeholder(self):
        self.setPlaceholderText(
            f"{Lng.search[JsonData.lng_index]} {Lng.in_[JsonData.lng_index]} {Mf.current_mf.mf_alias}"
        )

    def win_text_search_cmd(self, text: str):
        if text:
            self.setText(text)
            self.create_search(text)
            self.delayed_search()
        else:
            self.clear_search()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_buttons_position()

    def update_buttons_position(self):
        # Позиционируем правую кнопку (Clear)
        clear_x = self.width() - self.clear_btn.width() - self.clear_btn.right_margin
        clear_y = (self.height() - self.clear_btn.height()) // 2
        self.clear_btn.move(clear_x, clear_y)

        # Позиционируем левую кнопку относительно правой кнопки
        left_x = clear_x - self.left_btn.width() - self.left_btn.spacing
        left_y = (self.height() - self.left_btn.height()) // 2
        self.left_btn.move(left_x, left_y)

    def create_search(self, new_text: str):
        Dynamic.search_words_list = [
            word for item in new_text.split(",") if (word := item.strip())
        ]

        if Dynamic.search_words_list:
            self.clear_btn.enable()
            self.left_btn.enable()    # Поведение «такое же»: показываем вместе
        else:
            self.clear_btn.disable()
            self.left_btn.disable()   # Скрываем вместе

    def delayed_search(self):
        self.reload_thumbnails.emit()

    def clear_search(self):
        self.clear()
        if Dynamic.search_words_list:
            Dynamic.search_words_list.clear()
            Dynamic.loaded_thumbs = 0
            self.reload_thumbnails.emit()

    def keyPressEvent(self, event: QKeyEvent | None):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.delayed_search()
        elif event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        super().keyPressEvent(event)


class BarTopBtn(QSvgWidget):
    clicked_ = pyqtSignal()

    def __init__(self, base_svg: Path, selected_svg: Path):
        super().__init__()

        self.base_svg = self._load_svg_data(base_svg)
        self.selected_svg = self._load_svg_data(selected_svg)

        self.setFixedSize(BTN_H + 2, BTN_H + 2)
        self.load(self.base_svg)

        for path in (base_svg, selected_svg):
            if not path.exists():
                print("bar top btn icon not exists", path)

    @staticmethod
    def _load_svg_data(path: Path):
        with open(path, "rb") as f:
            return QByteArray(f.read())

    def set_selected_style(self):
        self.load(self.selected_svg)

    def set_base_style(self):
        self.load(self.base_svg)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_selected_style()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_base_style()
            self.clicked_.emit()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)


class SettingsBtn(BarTopBtn):
    base_svg = Static.COMMON_ICONS / "settings.svg"
    selected_svg = Static.COMMON_ICONS / "settings_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)


class ImgSearchBtn(BarTopBtn):
    base_svg = Static.COMMON_ICONS / "camera.svg"
    selected_svg = Static.COMMON_ICONS / "camera_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)


class BarTopCatalogTitle(TransparentLabel):
    def __init__(self, text: str):
        super().__init__(text)


class BarTopCatalogBtn(UPushButton):
    icon_size = QSize(13, 13)
    button_size = (110, 22)
    def __init__(self, text):
        super().__init__(text)
        self.setIconSize(self.icon_size)
        self.setFixedSize(*self.button_size)


class BarTopCatalogWidget(TransparentWidget):
    image_folder_svg = Static.COMMON_ICONS / "image_folder.svg"
    new_folder_svg = Static.COMMON_ICONS / "new_folder.svg"
    mf_open = pyqtSignal(Mf)
    mf_new = pyqtSignal(SettingsItem)

    def __init__(self):
        super().__init__()
        self.image_folder_icon = QIcon(str(self.image_folder_svg))
        self.new_folder_icon = QIcon(str(self.new_folder_svg))

        self.h_lay = QHBoxLayout(self)
        self.h_lay.setContentsMargins(0, 0, 0, 0)
        self.h_lay.setSpacing(0)

        self.title = BarTopCatalogTitle(Lng.catalog[JsonData.lng_index])
        self.h_lay.addWidget(self.title)

        self.h_lay.addSpacing(10)

        self.button = BarTopCatalogBtn("")
        self.set_btn_text(Mf.current_mf)
        self.button.setIcon(self.image_folder_icon)
        self.h_lay.addWidget(self.button)

        self.button_menu = UMenu(parent=self)
        self.button_menu.setMaximumWidth(200)
        self.button.setMenu(self.button_menu)

        for i in Mf.items:
            action = QAction(i.mf_alias, self.button_menu)
            action.setIcon(self.image_folder_icon)
            action.setIconVisibleInMenu(True)
            action.triggered.connect(
                lambda e, mf=i: self.mf_open_cmd(mf)
            )
            self.button_menu.addAction(action)

        self.button_menu.addSeparator()

        new_folder_action = QAction(Lng.new_folder[JsonData.lng_index], self.button_menu)
        new_folder_action.setIcon(self.new_folder_icon)
        new_folder_action.setIconVisibleInMenu(True)
        new_folder_action.triggered.connect(self.mf_new_cmd)
        self.button_menu.addAction(new_folder_action)

    def mf_new_cmd(self):
        setting_item = SettingsItem(
            type_="new_folder",
            content=""
        )
        self.mf_new.emit(setting_item)

    def mf_open_cmd(self, mf: Mf):
        self.set_btn_text(mf)
        self.mf_open.emit(mf)

    def set_btn_text(self, mf: Mf):
        text = f"{mf.mf_alias}"
        self.button.setText(text)


class BarTop(TransparentFrame):
    open_settings_win = pyqtSignal(SettingsItem)
    open_img_search_win = pyqtSignal()
    start_text_search = pyqtSignal()
    mf_open = pyqtSignal(Mf)
    mf_new = pyqtSignal(SettingsItem)

    def __init__(self):
        super().__init__()
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(10)

        self.catalog_btn = BarTopCatalogWidget()
        self.catalog_btn.mf_open.connect(self.mf_open.emit)
        self.catalog_btn.mf_new.connect(self.mf_new.emit)
        self.h_layout.addWidget(self.catalog_btn)

        self.h_layout.addStretch(0)

        # --- Кнопка поиска по картинке ---
        self.img_search_btn = ImgSearchBtn()
        self.img_search_btn.clicked_.connect(self.open_img_search_win.emit)
        self.h_layout.addWidget(self.img_search_btn)

        # --- Виджет поиска ---
        self.search_wid = SearchWidLineEdit()
        self.search_wid.reload_thumbnails.connect(self.start_text_search.emit)
        self.h_layout.addWidget(self.search_wid)

        self.h_layout.addStretch(0)

        # --- Кнопка настроек ---
        item = SettingsItem("general", "")
        self.settings_btn = SettingsBtn()
        self.settings_btn.clicked_.connect(lambda: self.open_settings_win.emit(item))
        self.h_layout.addWidget(self.settings_btn)

        # Флаг для отслеживания состояния скролла (заглушка от спама)
        self._is_scrolled = False 

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)
