import os
from pathlib import Path

from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from typing_extensions import Literal

from cfg import Dynamic, JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import (GrayTextLabel, HSep, UFrame, ULineEditLight, UMenu,
                            UPushButton)


BTN_H = 23


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


class BarTopLineEdit(ULineEditLight):
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
    svg_size = 32

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

        self.set_base_style()

        for i in (base_svg, selected_svg):
            if not i.exists():
                print(" bar top btn icon not exists", i)

    def _load_svg_data(self, path: Path):  # Исправил аннотацию типа со str на Path, так как вы передаете Path
        with open(path, "rb") as f:
            return QByteArray(f.read())

    def set_selected_style(self):
        self.svg_btn.load(self.selected_svg)
        self.svg_btn.update()

    def set_base_style(self):
        self.svg_btn.load(self.base_svg)
        self.svg_btn.update()

    def mousePressEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.set_selected_style()
        super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.set_base_style()
            self.clicked_.emit()
        super().mouseReleaseEvent(a0)


class SettingsBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "settings.svg"
    selected_svg = Static.BAR_TOP_ICONS / "settings_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)


class ImgSearchBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "img_search.svg"
    selected_svg = Static.BAR_TOP_ICONS / "img_search_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)


class BarTopCatalogTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)


class BarTopCatalogBtn(UPushButton):
    def __init__(self, text):
        super().__init__(text)


class BarTopCatalogWidget(QWidget):
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
        self.button.setFixedSize(120, BTN_H)
        self.button.setIcon(self.image_folder_icon)
        self.h_lay.addWidget(self.button)

        self.button_menu = UMenu(None)
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


class BarTop(UFrame):
    open_settings_win = pyqtSignal(SettingsItem)
    open_img_search_win = pyqtSignal()
    start_text_search = pyqtSignal()
    mf_open = pyqtSignal(Mf)
    mf_new = pyqtSignal(SettingsItem)

    def __init__(self):
        super().__init__()
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(10)

        self.catalog_btn = BarTopCatalogWidget()
        self.catalog_btn.mf_open.connect(self.mf_open.emit)
        self.catalog_btn.mf_new.connect(self.mf_new.emit)
        self.h_layout.addWidget(self.catalog_btn)

        self.h_layout.addStretch(0)


        # --- Виджет поиска ---
        self.search_wid = BarTopLineEdit()
        self.search_wid.reload_thumbnails.connect(self.start_text_search.emit)
        self.h_layout.addWidget(self.search_wid)

        self.h_layout.addStretch(0)


        # --- Кнопка поиска по картинке ---
        self.img_search_btn = ImgSearchBtn()
        self.img_search_btn.clicked_.connect(self.open_img_search_win.emit)
        self.h_layout.addWidget(self.img_search_btn)

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
