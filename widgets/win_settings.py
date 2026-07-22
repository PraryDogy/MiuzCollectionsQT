import copy
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QContextMenuEvent, QIcon, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QFileDialog, QGraphicsOpacityEffect,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QSpacerItem, QSpinBox, QSplitter, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)
from typing_extensions import Literal, Optional

from cfg import Cfg, Static, Themes
from system.filters import Filters
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import MfRemover, ProcessWorker
from system.paletes import ThemeChanger
from system.servers import Servers
from system.shared_utils import SharedUtils
from system.tasks import (HashDirSize, HashDirSizeItem, MfDataCleaner,
                          UThreadPool)
from system.utils import Utils

from ._base_widgets import (HSep, RowArrowWidget, ULineEdit, UMainWidget,
                            UMenu, UPushButton, UTextEdit, VListSpacerItem,
                            VListWidget, VListWidgetItem)
from .path_widget import PathWidget
from .win_smb import SuperWarnWindow
from .win_warn import ConfirmWindow, WarningWindow


def restart_app():
    ProcessWorker.stop_all() 
    os.execl(sys.executable, sys.executable, *sys.argv)
    QApplication.exit(0)


@dataclass(slots=True)
class CfgData:
    lng_index: int
    scaner_minutes: int


class StateWid:
    def __init__(self):
        self.was_changed = False

    def set_was_changed(self, *args):
        self.was_changed = True

    def reset_was_changed(self, *args):
        self.was_changed = False


class SettingsLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(30)


class SettingsGroup(QGroupBox):
    def __init__(self):
        """
        QGroupBox + self.layout_ (vertical layout)
        """
        super().__init__()
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(6, 0, 6, 0)
        self.layout_.setSpacing(0)


class SettingsTextEdit(SettingsGroup):
    textChanged = pyqtSignal()

    def __init__(self, title: str, placeholder: str, text: Optional[str]):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout_.setSpacing(10)

        self.title_wid = SettingsLabel(title)
        self.title_wid.setWordWrap(True)
        self.layout_.addWidget(self.title_wid)

        self.text_edit_wid = UTextEdit()
        self.text_edit_wid.setFixedHeight(100)
        self.text_edit_wid.setPlaceholderText(placeholder)
        self.text_edit_wid.textChanged.connect(self.textChanged.emit)
        self.text_edit_wid.setAcceptDrops(False)
        self.layout_.addWidget(self.text_edit_wid)

        if text:
            self.text_edit_wid.setPlainText(text)

    def get_list(self):
        return [
            i
            for i in self.text_edit_wid.toPlainText().split("\n")
            if i.strip()
        ]

    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
    

class SettingsListItem(VListWidgetItem):
    def __init__(self, url: str, parent, height = 30, text = None):
        super().__init__(parent, height, text)
        self.url = url
    

# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ


class ExportWin(UMainWidget):
    ww = 230
    hh = 290
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.export_settings[Cfg.lng_index])
        self.set_always_on_top()
        self.set_close_only()
        self.central_layout.setSpacing(5)
        self.central_layout.setContentsMargins(5, 10, 5, 5)

        urls = (
            Static.external_cfg,
            Static.external_mf,
            Static.external_filters,
            Static.external_servers,
            Static.external_db,
            Static.external_hashdir
        )

        tab_widget = QGroupBox()
        tab_widget.setFixedSize(self.ww, self.hh)
        self.central_layout.addWidget(tab_widget)

        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 10, 0, 0)
        tab_layout.setSpacing(0)

        v_list = VListWidget(self)
        v_list.itemClicked.connect(self.item_cmd)
        tab_layout.addWidget(v_list)

        for i in urls:
            text = os.path.basename(i)
            item = SettingsListItem(i, v_list, text=text)
            item.set_checkable()
            v_list.addItem(item)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        self.central_layout.addLayout(btn_layout)

        btn_layout.addStretch()

        btn_ok = UPushButton(Lng.ok[Cfg.lng_index])
        btn_ok.clicked.connect(
            lambda: self.export_files(self.get_urls())
        )
        btn_layout.addWidget(btn_ok)

        btn_cancel = UPushButton(Lng.cancel[Cfg.lng_index])
        btn_cancel.clicked.connect(self.deleteLater)
        btn_layout.addWidget(btn_cancel)

        btn_layout.addStretch()

        self.adjustSize()

    def item_cmd(self, item: VListWidgetItem):
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.Checked)
        else:
            item.setCheckState(Qt.CheckState.Unchecked)

    def get_urls(self):
        list_widget = self.findChild(VListWidget)
        items = [
            list_widget.item(i)
            for i in range(list_widget.count())
        ]
        urls = []

        for i in items:
            i: SettingsListItem
            if i.checkState() == Qt.CheckState.Checked:
                urls.append(i.url)

        # если выбрана база данных то экспортируем 
        # базу данных, кеш изображений, mf.json
        if Static.external_hashdir in urls:
            stack = [Static.external_hashdir]
            while stack:
                current_dir = stack.pop()
                for x in os.scandir(current_dir):
                    if x.is_dir():
                        stack.append(x)
                    else:
                        urls.append(x.path)
        return urls

    def export_files(self, files: list[str]):
        Cfg.json_to_app()
        Mf.json_to_app()
        Servers.json_to_app()
        Filters.json_to_app()
        
        downloads = os.path.expanduser("~/Downloads")
        filename = f"{Static.app_name}Settings.zip"
        path = os.path.join(downloads, filename)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for file in files:
                rel_path = file.replace(Static.external_files_dir, "")
                z.write(file, arcname=rel_path)
        Utils.reveal_files([path, ])
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class RebootSettings(SettingsGroup):
    cfg_changed = pyqtSignal()
    spin_max = 60
    spin_min = 0

    def __init__(self, cfg_data: CfgData):
        super().__init__()
        self.cfg_data = cfg_data

        lng_menu = UMenu(None)
        for value in (0, 1):
            action = QAction(Lng.russian[value], lng_menu)
            action.triggered.connect(lambda e, v=value: self.lang_action_cmd(v))
            lng_menu.addAction(action)

        lng_wid = RowArrowWidget(Lng.language_max[Cfg.lng_index])
        self.layout_.addWidget(lng_wid)
        self.lng_btn = UPushButton(text=Lng.russian[Cfg.lng_index])
        self.lng_btn.setFixedWidth(100)
        self.lng_btn.setMenu(lng_menu)
        lng_wid.replace_arrow_widget(self.lng_btn)

        scaner_time_wid = RowArrowWidget(Lng.search_interval[Cfg.lng_index])
        self.layout_.addWidget(scaner_time_wid)
        self.spin = QSpinBox(self)
        self.spin.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.spin.setMinimum(self.spin_min)
        self.spin.setMaximum(self.spin_max)
        self.spin.setFixedHeight(27)
        self.spin.setFixedWidth(100)
        self.spin.findChild(QLineEdit).setTextMargins(3, 0, 3, 0)
        self.spin.setSuffix(f" {Lng.minutes[Cfg.lng_index]}")
        self.spin.setValue(self.cfg_data.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        scaner_time_wid.replace_arrow_widget(self.spin)

        reset_data_wid = RowArrowWidget(Lng.erase_data[Cfg.lng_index])
        reset_data_wid.clicked.connect(self.reset_btn_cmd)
        self.layout_.addWidget(reset_data_wid)

        self.export_wid = RowArrowWidget(Lng.export_settings[Cfg.lng_index])
        self.export_wid.clicked.connect(self.export_settings)
        self.layout_.addWidget(self.export_wid)

        self.import_wid = RowArrowWidget(Lng.import_settings[Cfg.lng_index])
        self.import_wid.clicked.connect(self.import_settings)
        self.import_wid.hide_sep()
        self.layout_.addWidget(self.import_wid)
    
    def import_settings(self, *args):
        downloads = os.path.expanduser("~/Downloads")
        try:
            url = QFileDialog.getOpenFileName(directory=downloads)[0]
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return
        if url.endswith((".zip", ".ZIP")):
            zip_path = shutil.copy(
                src=url,
                dst=Static.external_files_dir
            )
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(Static.external_files_dir)

            Cfg.json_to_app()
            Mf.json_to_app()
            Filters.json_to_app()
            Servers.json_to_app()

            os.remove(zip_path)
            restart_app()

    def export_settings(self, *args):
        self.export_win = ExportWin()
        self.export_win.center_to_parent(self.window())
        self.export_win.show()

    def lang_action_cmd(self, value: int):
        self.cfg_data.lng_index = value
        self.lng_btn.setText(Lng.russian[value])
        self.cfg_changed.emit()

    def reset_btn_cmd(self, *args):
        def fin():
            self.deleteLater()
            shutil.rmtree(Static.external_files_dir)
            restart_app()

        reset_win = ConfirmWindow(Lng.erase_data_long[Cfg.lng_index])
        reset_win.center_to_parent(self.window())
        reset_win.ok_clicked.connect(fin)
        reset_win.show()

    def change_scan_time(self, value: int):
        if value == self.spin_max:
            self.spin.blockSignals(True)
            self.spin.setValue(self.spin_min + 1)
            self.spin.blockSignals(False)
            value = self.spin.minimum()
        elif value == self.spin_min:
            self.spin.blockSignals(True)
            self.spin.setValue(self.spin_max - 1)
            self.spin.blockSignals(False)
            value = self.spin.maximum()

        self.cfg_data.scaner_minutes = value
        self.cfg_changed.emit()


class SizesWin(UMainWidget):
    ww = 500
    hh = 330

    def __init__(self, size_items: list[HashDirSizeItem], parent=None):
        super().__init__(parent)
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.data_size[Cfg.lng_index])
        self.resize(self.ww, self.hh)
        self.central_layout.setSpacing(10)

        total_size = SharedUtils.get_f_size(sum(
            item.size for item in size_items
        ))
        first_row = QLabel(f"{Lng.data_size[Cfg.lng_index]}: {total_size}")
        self.central_layout.addWidget(first_row)

        total = sum(item.total_images for item in size_items)
        sec_row = QLabel(f"{Lng.images[Cfg.lng_index]}: {total}")
        self.central_layout.addWidget(sec_row)

        headers = [
            Lng.folder[Cfg.lng_index],
            Lng.file_size[Cfg.lng_index],
            Lng.images[Cfg.lng_index]
        ]
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(size_items))
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalScrollBar().setDisabled(True)
        self.table.horizontalScrollBar().hide()

        name_width = self.width() // 2
        other_width = self.width() // 4
        self.table.setColumnWidth(0, name_width)
        self.table.setColumnWidth(1, other_width)
        self.table.setColumnWidth(2, other_width)

        self.central_layout.addWidget(self.table)

        self.populate_table(size_items)
        self.setFocus()

    def populate_table(self, size_items: list[HashDirSizeItem]):
        item_flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        v_center = Qt.AlignmentFlag.AlignVCenter

        for row, item in enumerate(size_items):
            folder_item = QTableWidgetItem(item.mf.mf_alias)
            folder_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
            )
            folder_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | v_center
            )

            size_item = QTableWidgetItem(SharedUtils.get_f_size(item.size))
            size_item.setFlags(item_flags)
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | v_center
            )

            total_item = QTableWidgetItem(str(item.total_images))
            total_item.setFlags(item_flags)
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | v_center
            )

            self.table.setItem(row, 0, folder_item)
            self.table.setItem(row, 1, size_item)
            self.table.setItem(row, 2, total_item)
        
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class NonRebootSettings(SettingsGroup):
    def __init__(self):
        super().__init__()
        self.size_items = {}

        data_size_wid = RowArrowWidget(Lng.statistic[Cfg.lng_index])
        data_size_wid.clicked.connect(self.show_sizes_win)
        self.layout_.addWidget(data_size_wid)

        show_files_wid = RowArrowWidget(Lng.show_system_files[Cfg.lng_index])
        show_files_wid.clicked.connect(self.show_files_cmd)
        show_files_wid.hide_sep()
        self.layout_.addWidget(show_files_wid)

        self.get_sizes()

    def show_sizes_win(self, *args):
        self.sizes_win = SizesWin(self.size_items)
        self.sizes_win.center_to_parent(self.window())
        self.sizes_win.show()

    def get_sizes(self):
        def on_finish(items: list[HashDirSizeItem]):
            self.size_items = items
        self.hashdir_size = HashDirSize()
        self.hashdir_size.sigs.finished_.connect(on_finish)
        UThreadPool.start(self.hashdir_size)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.external_files_dir])
        except Exception as e:
            print(e)


class ThemeBtn(QWidget):
    clicked = pyqtSignal(str)
    ww = 70

    def __init__(self, theme: Literal["macintosh", "light", "dark"]):
        super().__init__()
        self.theme = theme
        self.svg = os.path.join(
            Static.internal_images,
            f"{theme}_theme.svg"
        )
        self.svg_selected = os.path.join(
            Static.internal_images,
            f"{theme}_theme_selected.svg"
        )
        text_mappings = {
            Themes.macos: Lng.macintosh_theme,
            Themes.dark: Lng.dark_theme,
            Themes.light: Lng.light_theme,
        }

        self.setFixedWidth(self.ww)

        layout_ = QVBoxLayout(self)
        layout_.setContentsMargins(0, 0, 0, 0)
        layout_.setSpacing(0)
        
        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(50, 50)
        layout_.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        label = QLabel(text_mappings[theme][Cfg.lng_index])
        layout_.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.clear_selection()

    def select(self):
        self.svg_widget.load(self.svg_selected)

    def clear_selection(self):
        self.svg_widget.load(self.svg)

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.theme)
        return super().mouseReleaseEvent(a0)


class ThemesWidget(SettingsGroup):

    def __init__(self):
        super().__init__()

        title_wid = RowArrowWidget(Lng.theme[Cfg.lng_index])
        title_wid.hide_arrow()
        self.layout_.addWidget(title_wid)

        spacer = QSpacerItem(0, 5)
        self.layout_.addSpacerItem(spacer)

        themes_wid = QWidget()
        themes_layout = QHBoxLayout(themes_wid)
        themes_layout.setContentsMargins(0, 0, 0, 0)
        themes_layout.setSpacing(5)
        themes_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout_.addWidget(themes_wid)
        
        for i in (Themes.macos, Themes.dark, Themes.light):
            btn = ThemeBtn(i)
            btn.clicked.connect(lambda theme, btn=btn: self.on_btn_clicked(theme, btn))
            themes_layout.addWidget(btn)
            if i == Cfg.theme:
                btn.select()

    def on_btn_clicked(self, theme: Literal["macintosh", "light", "dark"], btn: ThemeBtn):
        theme_btns = self.findChildren(ThemeBtn)
        if theme != Cfg.theme:
            for i in theme_btns:
                i.clear_selection()
            btn.select()
            Cfg.theme = theme
            ThemeChanger.init()


class SelectableLabel(SettingsLabel):
    txt = "\n".join([
        f"Version {Static.app_ver}",
        "Developed by Evlosh",
        "email: evlosh@gmail.com",
        "telegram: evlosh",
        ])
    def __init__(self, parent):
        super().__init__(parent)
        self.setText(self.txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = UMenu(ev)

        copy_text = QAction(parent=context_menu, text=Lng.copy[Cfg.lng_index])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lng.copy_all[Cfg.lng_index])
        select_all.triggered.connect(lambda: Utils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_menu()
        # return super().contextMenuEvent(ev)

    def copy_text_md(self):
        Utils.copy_text(self.selectedText())


class AboutWid(QGroupBox):
    icon_path = os.path.join(Static.internal_images, "icon.png")
    icon_size = 85
    opacity = 0.85

    def __init__(self):
        super().__init__()
        h_lay = QHBoxLayout(self)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(0)

        icon = QLabel()
        pixmap = QPixmap(self.icon_path)
        pixmap = Utils.qiconed_resize(pixmap, self.icon_size)
        icon.setPixmap(pixmap)
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(self.opacity) 
        icon.setGraphicsEffect(opacity_effect)
        h_lay.addWidget(icon)

        h_lay.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        h_lay.addWidget(lbl)

        h_lay.addStretch()


class GeneralSettings(QWidget, StateWid):
    changed = pyqtSignal()

    def __init__(self, cfg_data: CfgData):
        super().__init__()

        v_lay = QVBoxLayout(self)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(10)
        v_lay.setContentsMargins(0, 0, 0, 10)

        reboot_settings = RebootSettings(cfg_data)
        reboot_settings.cfg_changed.connect(self.changed.emit)
        reboot_settings.cfg_changed.connect(self.set_was_changed)
        v_lay.addWidget(reboot_settings)

        data_settings = NonRebootSettings()
        v_lay.addWidget(data_settings)

        themes = ThemesWidget()
        v_lay.addWidget(themes)

        about = AboutWid()
        v_lay.addWidget(about)

    def set_need_reset(self):
        self.need_reset_item.need_reset = True
        self.changed.emit()
        self.set_was_changed()



# ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ 



class FiltersWid(SettingsGroup, StateWid):
    changed = pyqtSignal()
    exts = (
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".psd",
        ".psb",
    )

    def __init__(self, filters_clone: list[str]):
        super().__init__()
        self.filters_clone = filters_clone

        filters_text = SettingsLabel(Lng.filters_descr[Cfg.lng_index])
        filters_text.setWordWrap(True)
        self.layout_.addWidget(filters_text)

        self.layout_.addSpacerItem(QSpacerItem(0, 5))
        self.layout_.addWidget(HSep())

        erase_filters_wid = RowArrowWidget(Lng.reset_filters[Cfg.lng_index])
        erase_filters_wid.clicked.connect(self.reset_btn_cmd)
        self.layout_.addWidget(erase_filters_wid)

        self.layout_.addSpacerItem(QSpacerItem(0, 10))

        self.filters_edit = UTextEdit()
        self.filters_edit.setFixedHeight(220)
        self.filters_edit.setPlaceholderText(Lng.filters[Cfg.lng_index])
        self.filters_edit.setPlainText("\n".join(self.filters_clone))
        self.filters_edit.textChanged.connect(self.on_text_changed)
        self.layout_.addWidget(self.filters_edit)
        
    def reset_btn_cmd(self, *args):
        def fin():
            # Filters.items = self.exts
            self.filters_edit.clear()
            self.filters_edit.insertPlainText("\n".join(self.exts))
            self.filters_win.deleteLater()
            self.changed.emit()
            self.set_was_changed()

        self.filters_win = ConfirmWindow(Lng.reset_filters_long[Cfg.lng_index])
        self.filters_win.ok_clicked.connect(fin)
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def on_text_changed(self):
        text = self.filters_edit.toPlainText().strip()
        lines = [line for line in text.split("\n") if line]
        self.filters_clone.clear()   # очищаем текущий список
        self.filters_clone.extend(lines)  # добавляем новые элементы
        self.changed.emit()
        self.set_was_changed()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ВИДЖЕТЫ ПАПОК С КОЛЛЕКЦИЯМИ ВИДЖЕТЫ ПАПОК С КОЛЛЕКЦИЯМИ 

class MfStopList(SettingsTextEdit):
    def __init__(self, mf: Mf):
        super().__init__(
            title=Lng.ignore_list_descr[Cfg.lng_index],
            placeholder=Lng.ignore_list[Cfg.lng_index],
            text="\n".join(i for i in mf.mf_stop_list),
        )
        self.mf = mf
        self.textChanged.connect(self.set_data)

    def set_data(self, *args):
        self.mf.mf_stop_list = self.get_list()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                os.path.basename(i.toLocalFile().rstrip(os.sep))
                for i in a0.mimeData().urls()
                if os.path.isdir(i.toLocalFile())
            ]
            text = "\n".join(
                (self.text_edit_wid.toPlainText(), *urls)
            ).strip()
            self.text_edit_wid.setPlainText(text)
        return super().dropEvent(a0)


class MfSave(SettingsGroup):
    clicked_ = pyqtSignal()
    def __init__(self):
        super().__init__()

        self.save_wid = RowArrowWidget(Lng.save[Cfg.lng_index])
        self.save_wid.hide_sep()
        self.layout_.addWidget(self.save_wid)

    def mouseReleaseEvent(self, event):
        self.clicked_.emit()
        return super().mouseReleaseEvent(event)

# ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ 


class MfSettings(QWidget, StateWid):
    changed = pyqtSignal()

    def __init__(self, mf: Mf, mf_list_clone: list[Mf]):
        super().__init__()
        self.mf = mf
        self.mf_list_clone = mf_list_clone

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(15)

        # Верхний ряд с названием
        name_group = SettingsGroup()
        main_lay.addWidget(name_group)

        self.name_wid = RowArrowWidget(f"{Lng.alias[Cfg.lng_index]}: {mf.mf_alias}")
        self.name_wid.hide_arrow()
        self.name_wid.hide_sep()
        name_group.layout_.addWidget(self.name_wid)

        self.path_widget = PathWidget(mf)
        self.path_widget.setFixedHeight(self.path_widget.hh)
        self.path_widget.mf_path_avaiable.connect(self.set_was_changed)
        main_lay.addWidget(self.path_widget)

        self.mf_stop_list = MfStopList(mf)
        self.mf_stop_list.textChanged.connect(self.set_was_changed)
        main_lay.addWidget(self.mf_stop_list)

        general_wid = SettingsGroup()
        main_lay.addWidget(general_wid)

        reset_wid = RowArrowWidget(Lng.reset_mf[Cfg.lng_index])
        reset_wid.clicked.connect(self.set_reset_flag)
        general_wid.layout_.addWidget(reset_wid)

        remove_wid = RowArrowWidget(Lng.remove_folder[Cfg.lng_index])
        remove_wid.clicked.connect(self.remove_cmd)
        remove_wid.hide_sep()
        general_wid.layout_.addWidget(remove_wid)

        self.mf_save = MfSave()
        self.mf_save.clicked_.connect(self.save)
        main_lay.addWidget(self.mf_save)

    def set_was_changed(self):
        self.mf_save.save_wid.show_warning()
        super().set_was_changed()

    def remove_cmd(self, *args):
        
        def poll_task():
            if not self.mf_remover.is_alive():
                for i in Mf.items:
                    if i.mf_alias == self.mf.mf_alias:
                        Mf.items.remove(i)
                        break
                if self.mf.mf_alias in Cfg.hide_digits_mf_lst:
                    Cfg.hide_digits_mf_lst.remove(self.mf.mf_alias)
                    Cfg.write_json_data()
                Mf.write_json_data()
                restart_app()
            else:
                QTimer.singleShot(1000, poll_task)

        def fin():
            for i in UMainWidget.win_list:
                i.hide()
            self.mf_remover.start()
            QTimer.singleShot(1000, poll_task)

        self.mf_remover = ProcessWorker(
            target=MfRemover.start,
            args=(self.mf.mf_alias, )
        )

        if len(self.mf_list_clone) == 1:
            win = WarningWindow(Lng.at_least_one_folder_required[Cfg.lng_index])
        else:
            win = ConfirmWindow(Lng.app_will_restarted[Cfg.lng_index])
            win.ok_clicked.connect(fin)
        win.center_to_parent(self.window())
        win.show()

    def set_reset_flag(self, *args):

        def reset_data():
            self.reset_task = MfDataCleaner(self.mf.mf_alias)
            self.reset_task.sigs.finished_.connect(restart_app)
            UThreadPool.start(self.reset_task)

        win = ConfirmWindow(Lng.app_will_restarted[Cfg.lng_index])
        win.ok_clicked.connect(reset_data)
        win.center_to_parent(self.window())
        win.show()

    def save(self, *args):

        def fin():
            self.mf.mf_paths = paths
            self.mf.mf_stop_list = stop_list

            for i in Mf.items:
                if i.mf_alias == self.mf.mf_alias:
                    i.mf_paths = paths
                    i.mf_stop_list = stop_list
                    break

            Mf.write_json_data()
            restart_app()

        def show_warn(text: str):
            win_warn = WarningWindow(text)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        stop_list = self.mf_stop_list.get_list()
        paths = []
        if self.path_widget.mf_temp_path:
            paths.append(self.path_widget.mf_temp_path)

        if not paths:
            show_warn(Lng.select_folder_path[Cfg.lng_index])
            return
        
        super_win = SuperWarnWindow()
        super_win.ok_clicked.connect(fin)
        super_win.center_to_parent(self.window())
        super_win.show()

        # win = ConfirmWindow(Lng.save_text_long[Cfg.lng_index])
        # win.ok_clicked.connect(fin)
        # win.center_to_parent(self.window())
        # win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА 

class NewFolder(QWidget, StateWid):
    icon_path = os.path.join(Static.internal_images, "warning.svg")
    changed = pyqtSignal()

    def __init__(self, mf_list_clone: list[Mf]):
        super().__init__()
        self.mf = Mf(
            mf_alias = "",
            mf_paths = [],
            mf_stop_list = [],
            mf_current_path = ""
        )
        self.mf_list_clone = mf_list_clone

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(15)

        name_wid = SettingsGroup()
        name_wid.layout_.setSpacing(5)
        main_lay.addWidget(name_wid)

        self.name_text = QLabel(Lng.folder_name[Cfg.lng_index])
        name_wid.layout_.addWidget(self.name_text)

        self.name_line_edit = ULineEdit()
        self.name_line_edit.setPlaceholderText(Lng.alias_immutable[Cfg.lng_index])
        name_wid.layout_.addWidget(self.name_line_edit)

        self.path_widget = PathWidget(self.mf)
        self.path_widget.mf_path_avaiable.connect(self.set_was_changed)
        self.path_widget.mf_path_avaiable.connect(self.set_mf_alias)
        self.path_widget.setFixedHeight(self.path_widget.hh)
        main_lay.addWidget(self.path_widget)

        self.mf_stop_list = MfStopList(self.mf)
        self.mf_stop_list.textChanged.connect(self.set_was_changed)
        main_lay.addWidget(self.mf_stop_list)

        save_group = SettingsGroup()
        main_lay.addWidget(save_group)

        self.save_wid = RowArrowWidget(Lng.save[Cfg.lng_index])
        self.save_wid.hide_sep()
        self.save_wid.clicked.connect(self.save_start)
        save_group.layout_.addWidget(self.save_wid)

    def set_mf_alias(self):
        name = os.path.basename(self.path_widget.mf_temp_path)
        if not self.name_line_edit.text():
            self.name_line_edit.setText(name)

    def set_was_changed(self):
        self.save_wid.show_warning()
        super().set_was_changed()

    def preset_new_folder(self, url: str):
        if url:
            url = os.sep + url.strip(os.sep)
            basename = os.path.basename(url)
            self.name_line_edit.setText(basename)
            self.save_wid.show_warning()
            
            self.path_widget.mf_temp_path = url
            self.path_widget.ok_path_widget()
            self.path_widget.stop_task()

    def save_fin(self, folder_name: str, paths: list, stop_list: list):
        self.mf.mf_alias = folder_name
        self.mf.mf_paths = paths
        self.mf.mf_stop_list = stop_list
        # мы добавляем новую папку менно в Mf.list_ а не в clone
        # чтобы отменить изменения из других отделов
        # и применить изменения только по новой папке
        Mf.items.append(self.mf)
        Mf.write_json_data()
        restart_app()

    def save_start(self, *args):

        def show_warn(text: str):
            win_warn = WarningWindow(text)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        pattern = r'^[A-Za-zА-Яа-яЁё0-9 ]+$'
        folder_name = self.name_line_edit.text()
        stop_list = self.mf_stop_list.get_list()
        paths = []
        if self.path_widget.mf_temp_path:
            paths.append(self.path_widget.mf_temp_path)

        if not folder_name:
            show_warn(Lng.enter_alias_warning[Cfg.lng_index])
            return

        elif any(i.mf_alias == folder_name for i in self.mf_list_clone):
            show_warn(
                f'{Lng.already_taken[Cfg.lng_index]}'
            )
            return

        elif len(folder_name) < 5 or len(folder_name) > 30:
            show_warn(f'{Lng.string_limit[Cfg.lng_index]}')
            return

        elif not re.fullmatch(pattern, folder_name):
            show_warn(f'{Lng.valid_message[Cfg.lng_index]}')
            return

        elif not paths:
            show_warn(Lng.select_folder_path[Cfg.lng_index])
            return

        win = ConfirmWindow(Lng.save_text_long[Cfg.lng_index])
        win.ok_clicked.connect(
            lambda: self.save_fin(folder_name, paths, stop_list)
        )
        win.center_to_parent(self.window())
        win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class WinSettings(UMainWidget):
    closed = pyqtSignal()
    svg_folder = os.path.join(Static.internal_images, "img_folder.svg")
    svg_filters = os.path.join(Static.internal_images, "filters.svg")
    svg_settings = os.path.join(Static.internal_images, "settings.svg")
    svg_new_folder = os.path.join(Static.internal_images, "new_folder.svg")
    svg_warn = os.path.join(Static.internal_images, "warning.svg")
    svg_size = 16

    def __init__(self, settings_item: SettingsItem):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.settings[Cfg.lng_index])
        self.setFixedSize(700, 560)

        self.cfg_data = CfgData(
            lng_index=Cfg.lng_index,
            scaner_minutes=Cfg.scaner_minutes
        )
        self.mf_list_clone = copy.deepcopy(Mf.items)
        self.filters_clone = copy.deepcopy(Filters.items)
        self.settings_item = settings_item

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setHandleWidth(14)
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        left_group = QGroupBox()
        self.splitter.addWidget(left_group)
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(1, 10, 1, 1)
        left_layout.setSpacing(0)

        self.left_menu = VListWidget()
        self.left_menu.clicked.connect(self.left_menu_click)
        self.left_menu.setIconSize(QSize(self.svg_size, self.svg_size))
        left_layout.addWidget(self.left_menu)

        main_settings_item = VListWidgetItem(
            parent=self.left_menu,
            text=Lng.general[Cfg.lng_index]
        )
        main_settings_item.setIcon(QIcon(self.svg_settings))
        self.left_menu.addItem(main_settings_item)
        
        filter_settings = VListWidgetItem(
            parent=self.left_menu,
            text=Lng.filters[Cfg.lng_index]
        )
        filter_settings.setIcon(QIcon(self.svg_filters))
        self.left_menu.addItem(filter_settings)

        new_folder = VListWidgetItem(
            parent=self.left_menu,
            text=Lng.new_folder[Cfg.lng_index]
        )
        new_folder.setIcon(QIcon(self.svg_new_folder))
        self.left_menu.addItem(new_folder)
        
        spacer = VListSpacerItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in Mf.items:
            new_folder = VListWidgetItem(self.left_menu, text=i.mf_alias)
            new_folder.setIcon(QIcon(self.svg_folder))
            self.left_menu.addItem(new_folder)

        self.right_wid = QWidget()
        self.right_lay = QVBoxLayout(self.right_wid)
        self.right_lay.setContentsMargins(0, 0, 0, 0)
        self.right_lay.setSpacing(0)
        self.splitter.addWidget(self.right_wid)

        self.right_lay.addStretch()

        self.btns_wid = QWidget()
        self.right_lay.addWidget(self.btns_wid)
        btns_lay = QHBoxLayout(self.btns_wid)
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)
        btns_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.warn_wid = QSvgWidget()
        self.warn_wid.load(self.svg_warn)
        self.warn_wid.setFixedSize(22, 22)
        pol = self.warn_wid.sizePolicy()
        pol.setRetainSizeWhenHidden(True)
        self.warn_wid.setSizePolicy(pol)
        self.warn_wid.hide()
        btns_lay.addWidget(self.warn_wid)

        self.ok_btn = UPushButton(Lng.ok[Cfg.lng_index])
        # self.ok_btn.setFixedWidth(95)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = UPushButton(Lng.cancel[Cfg.lng_index])
        # cancel_btn.setFixedWidth(95)
        cancel_btn.clicked.connect(self.deleteLater)
        btns_lay.addWidget(cancel_btn)

        self.btns_wid.adjustSize()

        self.central_layout.addSpacerItem(QSpacerItem(0, 5))

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([200, 600])

        # idx соответствует номеру строки в левом меню
        # при этом важно помнить, что номер 3 зарезервирован за пустым
        # спейсером
        if settings_item.type_ == "general":
            idx = 0
        elif settings_item.type_ == "filters":
            idx = 1
        elif settings_item.type_ == "new_folder":
            idx = 2
        elif settings_item.type_ == "edit_folder":
            for x, i in enumerate(self.mf_list_clone, start=4):
                if i.mf_alias == self.settings_item.content:
                    idx = x
                    break
        self.left_menu.setCurrentRow(idx)
        self.init_right_side(idx)

    def blink_ok_btn(self):
        # self.ok_btn.setText(Lng.restart[Cfg.lng_index])
        self.warn_wid.show()

    def init_right_side(self, idx: int):
        if idx == 0:
            self.btns_wid.show()
            r_wid = GeneralSettings(self.cfg_data)
        elif idx == 1:
            self.btns_wid.show()
            r_wid = FiltersWid(self.filters_clone)
        elif idx == 2:
            self.btns_wid.hide()
            r_wid = NewFolder(self.mf_list_clone)
            r_wid.preset_new_folder(self.settings_item.content)
        elif idx > 3:
            self.btns_wid.hide()
            item: VListWidgetItem = self.left_menu.item(idx)
            for mf in self.mf_list_clone:
                if mf.mf_alias == item.text():
                    r_wid = MfSettings(mf, self.mf_list_clone)
                    self.settings_item.type_ = "general"
                    self.settings_item.content = ""
                    break
        r_wid.changed.connect(self.blink_ok_btn)
        self.right_lay.insertWidget(0, r_wid)

    def add_mf(self, mf: Mf):
        self.mf_list_clone.append(mf)
        item = VListWidgetItem(self.left_menu, text=mf.mf_alias)
        item.setIcon(QIcon(self.svg_folder))
        item.mf = mf
        self.left_menu.addItem(item)
        self.left_menu.setCurrentItem(item)
        self.clear_right_side()
        index = self.left_menu.count() - 1
        self.init_right_side(index)
        self.blink_ok_btn()

    def clear_right_side(self):
        self.cfg_data = CfgData(
            lng_index=Cfg.lng_index,
            scaner_minutes=Cfg.scaner_minutes
        )
        self.mf_list_clone = copy.deepcopy(Mf.items)
        self.filters_clone = copy.deepcopy(Filters.items)
        self.warn_wid.hide()
        # self.ok_btn.setText(Lng.ok[Cfg.lng_index])

        wids = (GeneralSettings, MfSettings, NewFolder, FiltersWid)
        right_wid = self.right_wid.findChild(wids)
        right_wid.deleteLater()

    def left_menu_click(self, *args):
        self.clear_right_side()
        idx = self.left_menu.currentRow()
        self.init_right_side(idx)

    def ok_cmd(self):

        def validate_folders() -> bool:
            for folder in self.mf_list_clone:
                if not folder.mf_paths:
                    return folder.mf_alias
            return None

        if self.warn_wid.isHidden():
            self.deleteLater()
            return

        folder_no_paths = validate_folders()
        if folder_no_paths:
            win_warn = WarningWindow(
                f"{Lng.select_folder_path[Cfg.lng_index]} \"{folder_no_paths}\""
            )
            win_warn.center_to_parent(self.window())
            win_warn.show()
        else:
            Mf.items = self.mf_list_clone
            Mf.write_json_data()

            Filters.items = self.filters_clone
            Filters.write_json_data()

            Cfg.lng_index = self.cfg_data.lng_index
            Cfg.scaner_minutes = self.cfg_data.scaner_minutes
            Cfg.write_json_data()

            restart_app()

    def deleteLater(self):
        self.closed.emit()
        return super().deleteLater()
    
    def closeEvent(self, a0):
        self.closed.emit()
        return super().closeEvent(a0)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    
    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


class NewMfWin(UMainWidget):
    """
    Окно настроек при первой настройке приложения.
    """
    def __init__(self):
        super().__init__()
        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedWidth(450)
        self.mf_list_clone = copy.deepcopy(Mf.items)
        self.new_mf = NewFolder(mf_list_clone=self.mf_list_clone)
        # перехватываем нажатие кнопки "сохранить"
        self.new_mf.save_fin = self.new_save_fin
        self.central_layout.addWidget(self.new_mf)

    def new_save_fin(self, folder_name, paths, stop_list):
        mf = Mf(
            mf_alias=folder_name,
            mf_paths=paths,
            mf_stop_list=stop_list,
            mf_current_path=""
        )
        Mf.items.append(mf)
        Cfg.remake_external_dir()
        Cfg.make_empty_external_files()
        Mf.write_json_data()
        Cfg.write_json_data()
        Filters.write_json_data()
        restart_app()

    def closeEvent(self, a0):
        os._exit(1)
        return super().closeEvent(a0)