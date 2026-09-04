import os
from pathlib import Path

from PyQt6.QtCore import QByteArray, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                             QWidget)
from typing_extensions import Literal

from cfg import Dynamic, JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import (BaseGrayLabel, BaseSep, UFrame, ULineEditLight, UMenu,
                            UPushButton)


BAR_TOP_BTN_HEIGHT = 30



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
        self.setFixedSize(self.ww, BAR_TOP_BTN_HEIGHT)

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


class BarTopTitle(QLabel):
    def __init__(self, text: str):
        super().__init__(text)


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

        # 1. АКТИВИРУЕМ МЕТКУ И ДОБАВЛЯЕМ В LAYOUT
        self.lbl = BaseGrayLabel("")
        self.lbl.set_font_size(9)
        self.v_lay.addWidget(self.lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_base_style()

        for i in (base_svg, selected_svg):
            if not i.exists():
                print(" bar top btn icon not exists", i)

    def set_text(self, text: str):
        """Новый метод для одновременной установки подсказки и текста под иконкой."""
        self.setToolTip(text)
        self.lbl.setText(text)

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


class FiltersBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "filters.svg"
    selected_svg = Static.BAR_TOP_ICONS / "filters_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        # 2. Используем новый метод вместо setToolTip
        self.set_text(Lng.filters[JsonData.lng_index])


class SettingsBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "settings.svg"
    selected_svg = Static.BAR_TOP_ICONS / "settings_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        # 3. Используем новый метод вместо setToolTip
        self.set_text(Lng.settings[JsonData.lng_index])


class ImgSearchBtn(BarTopBtn):
    base_svg = Static.BAR_TOP_ICONS / "img_search.svg"
    selected_svg = Static.BAR_TOP_ICONS / "img_search_selected.svg"

    def __init__(self):
        super().__init__(self.base_svg, self.selected_svg)
        # 4. Используем новый метод вместо setToolTip
        self.set_text(Lng.image_search_short[JsonData.lng_index])


class BarTopCatalogBtn(UPushButton):
    on_mf_clicked = pyqtSignal(Mf)
    mf_new = pyqtSignal(SettingsItem)
    image_folder_svg = Static.COMMON_ICONS / "image_folder.svg"
    new_folder_svg = Static.COMMON_ICONS / "new_folder.svg"
    btn_size = (150, 25)

    def __init__(self):
        super().__init__("")
        self.setText(Mf.current_mf.mf_alias)
        self.setFixedSize(*self.btn_size)
        self.set_text(Mf.current_mf)
        self.mf_folder_icon = QIcon(str(self.image_folder_svg))
        self.setIcon(self.mf_folder_icon)

        self.menu_ = UMenu(None)
        self.setMenu(self.menu_)

        self.menu_.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        for mf in Mf.items:
            action = QAction(mf.mf_alias, self.menu_)
            action.triggered.connect(lambda e, mf=mf: self.action_cmd(e, mf))
            self.menu_.addAction(action)

            action.setIcon(self.mf_folder_icon)
            action.setIconVisibleInMenu(True)

        self.menu_.addSeparator()

        add_new = QAction(Lng.add[JsonData.lng_index], self.menu_)
        add_new_icon = QIcon(str(self.new_folder_svg))
        add_new.setIcon(add_new_icon)
        add_new.setIconVisibleInMenu(True)
        add_new.triggered.connect(self.mf_new_cmd)
        self.menu_.addAction(add_new)

    def adjust_menu_geometry(self):
        self.menu_.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.menu_.setMinimumWidth(self.width())
        self.menu_.move(self.menu_.x() + 30, self.menu_.y())

    def action_cmd(self, e, mf: Mf):
        self.on_mf_clicked.emit(mf)
        self.set_text(mf)

    def mf_new_cmd(self):
        item = SettingsItem(
            type_="new_folder",
            content=""
        )
        self.mf_new.emit(item)

    def set_text(self, mf: Mf):
        text = f" {mf.mf_alias}"
        self.setText(text)


class CatalogFrame(UFrame):
    on_mf_clicked = pyqtSignal(Mf)
    mf_new = pyqtSignal(SettingsItem)
    image_folder_svg = Static.COMMON_ICONS / "image_folder.svg"
    new_folder_svg = Static.COMMON_ICONS / "new_folder.svg"

    def __init__(self):
        super().__init__()
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(0)

        self.catalog_title = BarTopTitle(Lng.catalog[JsonData.lng_index] + ":")
        self.h_layout.addWidget(self.catalog_title)

        self.h_layout.addSpacing(10)

        self.catalog_btn = BarTopCatalogBtn()
        self.catalog_btn.on_mf_clicked.connect(self.on_mf_clicked.emit)
        self.catalog_btn.mf_new.connect(self.mf_new.emit)
        self.h_layout.addWidget(self.catalog_btn)


class BarTop(UFrame):
    open_settings_win = pyqtSignal(SettingsItem)
    open_filters_win = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    open_img_search_win = pyqtSignal()
    start_text_search = pyqtSignal()
    on_mf_clicked = pyqtSignal(Mf)
    mf_new = pyqtSignal(SettingsItem)
    LEFT_SPACING = 30

    def __init__(self):
        super().__init__()
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)

        self.catalog_frame = CatalogFrame()
        self.catalog_frame.on_mf_clicked.connect(self.on_mf_clicked.emit)
        self.catalog_frame.mf_new.connect(self.mf_new.emit)
        self.h_layout.addWidget(self.catalog_frame)

        self.h_layout.addStretch(0)

        # --- Кнопка поиска по картинке ---
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
        right_widget.setFixedWidth(BarTopLineEdit.ww)
        self.h_layout.addWidget(right_widget)
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 3, 0, 0)
        right_layout.setSpacing(0)

        # --- Виджет поиска ---
        self.search_wid = BarTopLineEdit()
        self.search_wid.reload_thumbnails.connect(self.start_text_search.emit)
        right_layout.addWidget(self.search_wid, alignment=Qt.AlignmentFlag.AlignRight)

        # Флаг для отслеживания состояния скролла (заглушка от спама)
        self._is_scrolled = False

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)
