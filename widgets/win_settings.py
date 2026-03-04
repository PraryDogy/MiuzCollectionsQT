import copy
import os
import re
import shutil
import subprocess

from PyQt5.QtCore import QRegExp, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QIcon
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsOpacityEffect, QGroupBox, QLabel,
                             QLineEdit, QSpacerItem, QSpinBox, QSplitter,
                             QTableWidget, QTableWidgetItem, QWidget)
from typing_extensions import Optional

from cfg import Cfg, Static, cfg
from system.filters import Filters
from system.items import NeedResetItem, SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.paletes import ThemeChanger
from system.shared_utils import SharedUtils
from system.tasks import HashDirSize, MfDataCleaner, UThreadPool
from system.utils import Utils

from ._base_widgets import (SingleActionWindow, SmallBtn, UHBoxLayout,
                            ULineEdit, UListSpacerItem, UListWidgetItem, UMenu,
                            UTextEdit, UVBoxLayout, VListWidget)
from .win_warn import WinQuestion, WinWarn


def restart_app():
    QApplication.quit()
    Utils.start_new_app()


class WhatChange:
    def __init__(self):
        self.removed_mf_list: list[Mf] = []
        self.erased_mf_list: list[Mf] = []


class ULabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(30)


class UPushButton(SmallBtn):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(100)


class USep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: rgba(128, 128, 128, 0.2)")
        self.setFixedHeight(1)


class GroupLay(UVBoxLayout):
    mrg = 2
    spc = 5
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setContentsMargins(self.mrg, self.mrg, self.mrg, self.mrg)
        self.setSpacing(self.spc)


class GroupChild(QWidget):
    hh = 30

    def __init__(self):
        super().__init__()
        self.setFixedHeight(self.hh)


class SvgArrow(QSvgWidget):
    clicked = pyqtSignal()
    img = "./images/next.svg"
    size_ = 16

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.load(self.img)
        self.setFixedSize(self.size_, self.size_)

    def mouseReleaseEvent(self, a0):
        self.clicked.emit()
        return super().mouseReleaseEvent(a0)


class TextEditWidget(QGroupBox):
    text_changed = pyqtSignal()

    def __init__(self, title: str, placeholder: str, text: Optional[str]):
        super().__init__()
        self.setAcceptDrops(True)

        group_lay = GroupLay()
        self.setLayout(group_lay)

        self.title_wid = ULabel(title)
        self.title_wid.setWordWrap(True)
        group_lay.addWidget(self.title_wid)

        self.text_edit_wid = UTextEdit()
        self.text_edit_wid.setPlaceholderText(placeholder)
        self.text_edit_wid.textChanged.connect(self.text_changed.emit)
        self.text_edit_wid.setAcceptDrops(False)
        group_lay.addWidget(self.text_edit_wid)

        if text:
            self.text_edit_wid.setPlainText(text)

    def get_lined_text(self):
        return [
            i
            for i in self.text_edit_wid.toPlainText().split("\n")
            if i.strip()
        ]

    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
    


# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ



class RebootSettings(QGroupBox):
    cfg_changed = pyqtSignal()
    spin_max = 60
    spin_min = 0

    def __init__(self, cfg_clone: Cfg, what_change: WhatChange):
        super().__init__()
        self.cfg_clone = cfg_clone
        self.what_change = what_change

        group_lay = GroupLay()
        self.setLayout(group_lay)

        lng_wid = GroupChild()
        lng_lay = UHBoxLayout()
        lng_wid.setLayout(lng_lay)
        group_lay.addWidget(lng_wid)

        self.lng_text = ULabel(Lng.language_max[cfg.lng])
        lng_lay.addWidget(self.lng_text)

        lng_lay.addStretch()

        self.lng_menu = UMenu(None)
        for value in (0, 1):
            action = QAction(Lng.russian[value], self.lng_menu)
            action.triggered.connect(lambda e, v=value: self.lang_action_cmd(v))
            self.lng_menu.addAction(action)

        self.lng_btn = UPushButton(text=Lng.russian[cfg.lng])
        self.lng_btn.setFixedWidth(109)
        self.lng_btn.setMenu(self.lng_menu)
        lng_lay.addWidget(self.lng_btn)

        group_lay.addWidget(USep())

        scaner_time_wid = GroupChild()
        scaner_timer_lay = UHBoxLayout()
        scaner_time_wid.setLayout(scaner_timer_lay)
        group_lay.addWidget(scaner_time_wid)

        scaner_time_text = ULabel(Lng.search_interval[cfg.lng], self)
        scaner_timer_lay.addWidget(scaner_time_text)

        scaner_timer_lay.addStretch()

        self.spin = QSpinBox(self)
        self.spin.setMinimum(self.spin_min)
        self.spin.setMaximum(self.spin_max)
        self.spin.setFixedHeight(27)
        self.spin.setFixedWidth(100)
        self.spin.findChild(QLineEdit).setTextMargins(3, 0, 3, 0)
        self.spin.setSuffix(f" {Lng.minutes[cfg.lng]}")
        self.spin.setValue(self.cfg_clone.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        scaner_timer_lay.addWidget(self.spin)

        group_lay.addWidget(USep())

        reset_data_wid = GroupChild()
        reset_data_wid.mouseReleaseEvent = self.reset_btn_cmd
        reset_data_lay = UHBoxLayout()
        reset_data_wid.setLayout(reset_data_lay)
        group_lay.addWidget(reset_data_wid)

        reset_data_text = ULabel(Lng.erase_data[cfg.lng])
        reset_data_lay.addWidget(reset_data_text)

        reset_data_lay.addStretch()

        self.reset_data_btn = SvgArrow()
        reset_data_lay.addWidget(self.reset_data_btn)

    def show_win_warn(self, text: str, size: int):
        win = WinQuestion(Lng.attention[cfg.lng], text)
        win.resize(330, size)
        win.center_to_parent(self.window())
        return win

    def lang_action_cmd(self, value: int):
        self.cfg_clone.lng = value
        self.lng_btn.setText(Lng.russian[value])
        self.cfg_changed.emit()

    def reset_btn_cmd(self, *args):
        def fin():
            self.deleteLater()
            shutil.rmtree(Static.app_support)
            restart_app()
        reset_win = self.show_win_warn(Lng.erase_data_long[cfg.lng], 115)
        reset_win.text_label.setFixedHeight(85)
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

        self.cfg_clone.scaner_minutes = value
        self.cfg_changed.emit()


class SizesWin(SingleActionWindow):
    ww = 500
    hh = 330

    def __init__(self, sizes: dict[str, int], parent=None):
        super().__init__(parent)
        self.setWindowTitle(Lng.data_size[cfg.lng])
        self.resize(self.ww, self.hh)

        central = QWidget()
        self.setCentralWidget(central)
        layout = UVBoxLayout()
        central.setLayout(layout)

        info_widget = QWidget()
        info_layout = UVBoxLayout(info_widget)
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(5)

        total_size = SharedUtils.get_f_size(sum(i['size'] for i in sizes.values()))
        first_row = QLabel(f"{Lng.data_size[cfg.lng]}: {total_size}")
        info_layout.addWidget(first_row)

        total = sum(i["total"] for i in sizes.values())
        sec_row = QLabel(f"{Lng.images[cfg.lng]}: {total}")
        info_layout.addWidget(sec_row)

        layout.addWidget(info_widget)

        headers = [Lng.folder[cfg.lng], Lng.file_size[cfg.lng], Lng.images[cfg.lng]]
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(sizes))
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalScrollBar().setDisabled(True)
        self.table.horizontalScrollBar().hide()

        name_width = self.width() // 2
        other_width = self.width() // 4
        self.table.setColumnWidth(0, name_width)
        self.table.setColumnWidth(1, other_width)
        self.table.setColumnWidth(2, other_width)

        layout.addWidget(self.table)

        self.populate_table(sizes)
        self.setFocus()

    def populate_table(self, sizes: dict[str, dict]):
        item_flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        v_center = Qt.AlignmentFlag.AlignVCenter

        for row, (folder, data) in enumerate(sizes.items()):
            folder_item = QTableWidgetItem(folder)
            folder_item.setFlags(
                Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
            )
            folder_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | v_center
            )

            size_item = QTableWidgetItem(SharedUtils.get_f_size(data["size"]))
            size_item.setFlags(item_flags)
            size_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | v_center
            )

            total_item = QTableWidgetItem(str(data["total"]))
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


class NonRebootSettings(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(80)
        self.data = {}

        group_lay = GroupLay()
        self.setLayout(group_lay)

        data_size_wid = GroupChild()
        data_size_wid.mouseReleaseEvent = self.show_sizes_win
        data_size_lay = UHBoxLayout()
        data_size_wid.setLayout(data_size_lay)
        group_lay.addWidget(data_size_wid)

        data_size_text = ULabel(text=Lng.statistic[cfg.lng])
        data_size_lay.addWidget(data_size_text)

        data_size_lay.addStretch()

        data_size_btn = SvgArrow()
        data_size_lay.addWidget(data_size_btn)

        group_lay.addWidget(USep())

        show_files_wid = GroupChild()
        show_files_wid.mouseReleaseEvent = self.show_files_cmd
        show_files_lay = UHBoxLayout()
        show_files_wid.setLayout(show_files_lay)
        group_lay.addWidget(show_files_wid)

        show_files_text = ULabel(Lng.show_system_files[cfg.lng])
        show_files_lay.addWidget(show_files_text)

        show_files_btn = SvgArrow(text=Lng.show[cfg.lng])
        show_files_lay.addWidget(show_files_btn)

        self.get_sizes()

    def show_sizes_win(self, *args):
        self.sizes_win = SizesWin(self.data)
        self.sizes_win.center_to_parent(self.window())
        self.sizes_win.show()

    def get_sizes(self):
        def on_finish(data: dict):
            self.data = data
        self.hashdir_size = HashDirSize()
        self.hashdir_size.sigs.finished_.connect(on_finish)
        UThreadPool.start(self.hashdir_size)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.app_support])
        except Exception as e:
            print(e)


class ThemesBtn(QFrame):
    clicked = pyqtSignal()

    def __init__(self, svg_path: str, label_text: str):
        super().__init__()
        v_lay = UVBoxLayout()
        self.setLayout(v_lay)

        self.svg_container = QFrame()
        self.svg_container.setObjectName("svg_container")
        self.svg_container.setStyleSheet(self.regular_style())
        v_lay.addWidget(self.svg_container)

        svg_lay = UVBoxLayout()
        self.svg_container.setLayout(svg_lay)

        self.svg_widget = QSvgWidget(svg_path)
        self.svg_widget.setFixedSize(50, 50)
        svg_lay.addWidget(self.svg_widget)

        label = ULabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        v_lay.addWidget(label)

    def regular_style(self):
        return """
            #svg_container {
                border: 2px solid transparent;
                border-radius: 10px;
            }
        """

    def border_style(self):
        return """
            #svg_container {
                border: 2px solid #007aff;
                border-radius: 10px;
            }
        """

    def selected(self, enable=True):
        if enable:
            self.svg_container.setStyleSheet(
                self.border_style()
            )
        else:
            self.svg_container.setStyleSheet(
                self.regular_style()
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class Themes(QGroupBox):
    clicked = pyqtSignal()
    svg_theme_system = "./images/system_theme.svg"
    svg_theme_dark = "./images/dark_theme.svg"
    svg_theme_light = "./images/light_theme.svg"

    def __init__(self):
        super().__init__()
        self.setFixedHeight(120)
        group_lay = GroupLay()
        self.setLayout(group_lay)

        title_wid = GroupChild()
        title_lay = UHBoxLayout()
        title_wid.setLayout(title_lay)
        group_lay.addWidget(title_wid)

        title_text = ULabel("Тема")
        title_lay.addWidget(title_text)

        group_lay.addWidget(USep())

        themes_wid = QWidget()
        themes_lay = UHBoxLayout()
        themes_lay.setSpacing(20)
        themes_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        themes_wid.setLayout(themes_lay)
        group_lay.addWidget(themes_wid)

        self.frames = []

        self.system_theme = ThemesBtn(
            self.svg_theme_system,
            Lng.theme_auto[cfg.lng]
        )
        self.dark_theme = ThemesBtn(
            self.svg_theme_dark,
            Lng.theme_dark[cfg.lng]
        )
        self.light_theme = ThemesBtn(
            self.svg_theme_light,
            Lng.theme_light[cfg.lng]
        )

        for f in (self.system_theme, self.dark_theme, self.light_theme):
            themes_lay.addWidget(f)
            self.frames.append(f)
            f.clicked.connect(self.on_frame_clicked)

        if cfg.dark_mode == 0:
            self.set_selected(self.system_theme)
        elif cfg.dark_mode == 1:
            self.set_selected(self.dark_theme)
        elif cfg.dark_mode == 2:
            self.set_selected(self.light_theme)

    def on_frame_clicked(self):
        sender: ThemesBtn = self.sender()
        self.set_selected(sender)

        if sender == self.system_theme:
            cfg.dark_mode = 0
        elif sender == self.dark_theme:
            cfg.dark_mode = 1
        elif sender == self.light_theme:
            cfg.dark_mode = 2

        ThemeChanger.init()
        self.clicked.emit()

    def set_selected(self, selected_frame: ThemesBtn):
        for f in self.frames:
            f.selected(f is selected_frame)


class SelectableLabel(ULabel):
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

        copy_text = QAction(parent=context_menu, text=Lng.copy[cfg.lng])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lng.copy_all[cfg.lng])
        select_all.triggered.connect(lambda: Utils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_menu()
        return super().contextMenuEvent(ev)

    def copy_text_md(self):
        Utils.copy_text(self.selectedText())


class AboutWid(QGroupBox):
    svg_icon = "./images/icon.svg"

    def __init__(self):
        super().__init__()
        h_lay = UHBoxLayout()
        self.setLayout(h_lay)

        icon = QSvgWidget(self.svg_icon)
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(85, 85)
        h_lay.addWidget(icon)

        h_lay.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        h_lay.addWidget(lbl)


class GeneralSettings(QWidget):
    changed = pyqtSignal()

    def __init__(self, cfg_clone: Cfg, what_change: WhatChange):
        super().__init__()

        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(10)
        v_lay.setContentsMargins(0, 0, 0, 10)
        self.setLayout(v_lay)

        reboot_settings = RebootSettings(cfg_clone, what_change)
        reboot_settings.cfg_changed.connect(self.changed.emit)
        v_lay.addWidget(reboot_settings)

        data_settings = NonRebootSettings()
        v_lay.addWidget(data_settings)

        themes = Themes()
        v_lay.addWidget(themes)

        about = AboutWid()
        v_lay.addWidget(about)

    def set_need_reset(self):
        self.need_reset_item.need_reset = True
        self.changed.emit()



# ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ 



class FiltersWid(QGroupBox):
    changed = pyqtSignal()

    def __init__(self, filters_clone: list[str]):
        super().__init__()
        self.filters_clone = filters_clone

        group_lay = GroupLay()
        group_lay.setSpacing(5)
        self.setLayout(group_lay)

        filters_text = ULabel(Lng.filters_descr[cfg.lng])
        filters_text.setWordWrap(True)
        group_lay.addWidget(filters_text)

        self.filters_edit = UTextEdit()
        self.filters_edit.setFixedHeight(220)
        self.filters_edit.setPlaceholderText(Lng.filters[cfg.lng])
        self.filters_edit.setPlainText("\n".join(self.filters_clone))
        self.filters_edit.textChanged.connect(self.on_text_changed)
        group_lay.addWidget(self.filters_edit)

        btns_wid = QWidget()
        btns_lay = UHBoxLayout()
        btns_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btns_lay.setSpacing(10)
        btns_wid.setLayout(btns_lay)
        group_lay.addWidget(btns_wid)

        self.save_btn = UPushButton(Lng.save[cfg.lng])
        self.save_btn.clicked.connect(self.save_btn_cmd)
        btns_lay.addWidget(self.save_btn)

        self.reset_btn = UPushButton(Lng.reset[cfg.lng])
        self.reset_btn.clicked.connect(self.reset_btn_cmd)
        btns_lay.addWidget(self.reset_btn)

        self.save_btn.setDisabled(True)
        
    def reset_btn_cmd(self):
        def fin():
            self.filters_edit.clear()
            self.filters_edit.insertPlainText(
                "\n".join(Filters.default)
            )
            self.filters_win.deleteLater()
            self.reset_btn.setDisabled(True)
            self.save_btn.setDisabled(False)

        self.filters_win = WinQuestion(
            Lng.attention[cfg.lng],
            Lng.filters_reset[cfg.lng]
        )
        self.filters_win.resize(330, 80)
        self.filters_win.ok_clicked.connect(fin)
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def on_text_changed(self):
        text = self.filters_edit.toPlainText().strip()
        lines = [line for line in text.split("\n") if line]
        self.filters_clone.clear()   # очищаем текущий список
        self.filters_clone.extend(lines)  # добавляем новые элементы
        self.reset_btn.setDisabled(False)
        self.save_btn.setDisabled(False)

    def save_btn_cmd(self, *args):
        self.save_btn.setDisabled(True)
        self.changed.emit()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛ


class MfPaths(TextEditWidget):
    def __init__(self, mf: Mf):
        super().__init__(
            title=Lng.images_folder_path[cfg.lng],
            placeholder=Lng.folder_path[cfg.lng],
            text="\n".join(i for i in mf.paths),
        )
        self.mf = mf
        self.text_changed.connect(self.set_data)

    def set_data(self, *args):
        self.mf.paths = self.get_lined_text()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                i.toLocalFile().rstrip(os.sep)
                for i in a0.mimeData().urls()
                if os.path.isdir(i.toLocalFile())
            ]
            text = "\n".join(
                (self.text_edit_wid.toPlainText(), *urls)
            ).strip()
            self.text_edit_wid.setPlainText(text)
        return super().dropEvent(a0)


class MfStopList(TextEditWidget):
    def __init__(self, mf: Mf):
        super().__init__(
            title=Lng.ignore_list_descr[cfg.lng],
            placeholder=Lng.ignore_list[cfg.lng],
            text="\n".join(i for i in mf.stop_list),
        )
        self.mf = mf
        self.text_changed.connect(self.set_data)

    def set_data(self, *args):
        self.mf.stop_list = self.get_lined_text()

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


class MfSettings(QWidget):
    changed = pyqtSignal()

    def __init__(self, target_mf: Mf):
        super().__init__()
        self.target_mf = target_mf

        main_lay = UVBoxLayout()
        main_lay.setSpacing(15)
        self.setLayout(main_lay)

        # Верхний ряд с названием
        self.name_wid = QGroupBox()
        name_lay = GroupLay()
        self.name_wid.setLayout(name_lay)
        main_lay.addWidget(self.name_wid)
        name_text = ULabel(f"{Lng.alias[cfg.lng]}: {target_mf.alias}")
        name_text.setFixedHeight(GroupChild.hh)
        name_lay.addWidget(name_text)

        mf_paths = MfPaths(target_mf)
        mf_paths.text_changed.connect(self.changed.emit)
        main_lay.addWidget(mf_paths)

        mf_stop_list = MfStopList(target_mf)
        mf_stop_list.text_changed.connect(self.changed.emit)
        main_lay.addWidget(mf_stop_list)

        general_wid = QGroupBox()
        general_lay = GroupLay()
        general_wid.setLayout(general_lay)
        main_lay.addWidget(general_wid)

        reset_wid = GroupChild()
        reset_wid.mouseReleaseEvent = self.set_reset_flag
        reset_lay = UHBoxLayout()
        reset_wid.setLayout(reset_lay)
        general_lay.addWidget(reset_wid)
        reset_text = ULabel(text=Lng.reset_mf[cfg.lng])
        reset_lay.addWidget(reset_text)
        reset_lay.addStretch()
        reset_btn = SvgArrow()
        reset_lay.addWidget(reset_btn)

        general_lay.addWidget(USep())

        remove_wid = GroupChild()
        remove_wid.mouseReleaseEvent = self.set_remove_flag
        remove_lay = UHBoxLayout()
        remove_wid.setLayout(remove_lay)
        general_lay.addWidget(remove_wid)
        remove_text = ULabel(text=Lng.remove_folder[cfg.lng])
        remove_lay.addWidget(remove_text)
        remove_lay.addStretch()
        remove_btn = SvgArrow()
        remove_lay.addWidget(remove_btn)

        main_lay.addSpacerItem(QSpacerItem(0, 15))


    def show_warn(self, message, width=380):
        win_warn = WinQuestion(
            Lng.attention[cfg.lng],
            message
        )
        win_warn.resize(width, 80)
        win_warn.center_to_parent(self.window())
        return win_warn

    def set_remove_flag(self, *args):
        def fin():
            for i in Mf.list_:
                if i.alias == self.target_mf.alias:
                    Mf.list_.remove(i)
                    break
            Mf.write_json_data()
            restart_app()

        win = self.show_warn(Lng.remove_folder_long[cfg.lng])
        win.ok_clicked.connect(fin)
        win.show()

    def set_reset_flag(self, *args):

        def reset_data():
            self.reset_task = MfDataCleaner(self.target_mf.alias)
            self.reset_task.sigs.finished_.connect(restart_app)
            UThreadPool.start(self.reset_task)

        win = self.show_warn(Lng.reset_mf_long[cfg.lng])
        win.ok_clicked.connect(reset_data)
        win.show()

    def save(self):
        self.changed.emit()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА 

class NewFolder(QWidget):
    new_folder = pyqtSignal(Mf)
    svg_warning = "./images/warning.svg"

    def __init__(self, mf_list: list[Mf]):
        super().__init__()
        self.mf = Mf("", [], [])
        self.mf_list = mf_list

        v_lay = UVBoxLayout()
        v_lay.setSpacing(15)
        self.setLayout(v_lay)

        first_row = QGroupBox()
        v_lay.addWidget(first_row)
        first_lay = UVBoxLayout()
        first_lay.setSpacing(10)
        first_lay.setContentsMargins(0, 3, 0, 3)
        first_row.setLayout(first_lay)

        self.name_folder = QLabel(Lng.folder_name[cfg.lng])
        first_lay.addWidget(self.name_folder)

        self.name_label = ULineEdit()
        self.name_label.setPlaceholderText(Lng.alias_immutable[cfg.lng])
        self.name_label.textChanged.connect(self.name_cmd)
        first_lay.addWidget(self.name_label)

        self.advanced = MfAdvanced(self.mf)
        self.advanced.changed.connect(self.toggle_save_btn)
        v_lay.addWidget(self.advanced)

        btn_wid = QWidget()
        v_lay.addWidget(btn_wid)
        btn_lay = UHBoxLayout()
        btn_lay.setContentsMargins(0, 0, 0, 10)
        btn_lay.setSpacing(15)
        btn_wid.setLayout(btn_lay)

        self.save_btn = UPushButton(Lng.save[cfg.lng])
        self.save_btn.setDisabled(True)
        self.save_btn.clicked.connect(self.save)
        btn_lay.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def preset_new_folder(self, url: str):
        text_edit = self.findChildren(TextEditWidget)[0].text_edit_wid
        text_edit.setPlainText(url)

    def name_cmd(self):
        name = self.name_label.text().strip()
        self.mf.alias = name

    def toggle_save_btn(self):
        if self.name_label.text() and self.advanced.mf_paths.get_lined_text():
            self.save_btn.setDisabled(False)

    def save(self):
        pattern = r'^[A-Za-zА-Яа-яЁё0-9 ]+$'

        def show_warn(message, width=380):
            self.win_warn = WinWarn(
                Lng.attention[cfg.lng],
                message
            )
            self.win_warn.resize(width, 80)
            self.win_warn.center_to_parent(self.window())
            self.win_warn.show()

        if not self.mf.alias:
            show_warn(Lng.enter_alias_warning[cfg.lng])
            return

        elif any(i.alias == self.mf.alias for i in self.mf_list):
            show_warn(
                f'{Lng.alias[cfg.lng]} "{self.mf.alias}" '
                f'{Lng.already_taken[cfg.lng].lower()}'
            )
            return

        elif len(self.mf.alias) > 30:
            show_warn(f'{Lng.string_limit[cfg.lng]}')
            return

        elif not re.fullmatch(pattern, self.mf.alias):
            show_warn(f'{Lng.valid_message[cfg.lng]}')
            return

        elif not self.mf.paths:
            show_warn(Lng.select_folder_path[cfg.lng], width=330)
            return

        name = None
        for i in self.mf_list:
            for x in i.paths:
                if x in self.mf.paths:
                    name = i.alias
        if name:
            show_warn(f"{Lng.folder_path_exists[cfg.lng]} {name}", width=330)
            return

        self.new_folder.emit(self.mf)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class WinSettings(SingleActionWindow):
    closed = pyqtSignal()
    reset_data = pyqtSignal(Mf)
    svg_folder = "./images/img_folder.svg"
    svg_filters = "./images/filters.svg"
    svg_settings = "./images/settings.svg"
    svg_new_folder = "./images/new_folder.svg"
    svg_size = 16

    def __init__(self, settings_item: SettingsItem):
        super().__init__()
        self.setWindowTitle(Lng.settings[cfg.lng])
        self.setFixedSize(700, 560)

        self.what_change = WhatChange()
        self.cfg_clone = copy.deepcopy(cfg)
        self.mf_list_clone = copy.deepcopy(Mf.list_)
        self.filters_clone = copy.deepcopy(Filters.filters)

        # удалить бы
        self.need_reset_item = NeedResetItem()
        self.mf_items: list[UListWidgetItem] = []
        self.settings_item = settings_item

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setHandleWidth(14)
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.left_menu.clicked.connect(self.left_menu_click)
        self.left_menu.setIconSize(QSize(self.svg_size, self.svg_size))
        self.splitter.addWidget(self.left_menu)

        main_settings_item = UListWidgetItem(self.left_menu, text=Lng.general[cfg.lng])
        main_settings_item.setIcon(QIcon(self.svg_settings))
        self.left_menu.addItem(main_settings_item)
        
        filter_settings = UListWidgetItem(self.left_menu, text=Lng.filters[cfg.lng])
        filter_settings.setIcon(QIcon(self.svg_filters))
        self.left_menu.addItem(filter_settings)

        new_folder = UListWidgetItem(self.left_menu, text=Lng.new_folder[cfg.lng])
        new_folder.setIcon(QIcon(self.svg_new_folder))
        self.left_menu.addItem(new_folder)
        
        spacer = UListSpacerItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in Mf.list_:
            new_folder = UListWidgetItem(self.left_menu, text=i.alias)
            new_folder.mf = i
            new_folder.setIcon(QIcon(self.svg_folder))
            self.left_menu.addItem(new_folder)
            self.mf_items.append(new_folder)

        self.right_wid = QWidget()
        self.right_lay = UVBoxLayout()
        self.right_wid.setLayout(self.right_lay)
        self.splitter.addWidget(self.right_wid)

        self.right_lay.addStretch()

        btns_wid = QWidget()
        btns_wid.setFixedHeight(26)
        self.right_lay.addWidget(btns_wid)
        btns_lay = UHBoxLayout()
        btns_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btns_lay.setSpacing(10)
        btns_wid.setLayout(btns_lay)

        self.warn_svg = QSvgWidget()
        self.warn_svg.setParent(btns_wid)
        self.warn_svg.setFixedSize(22, 22)
        self.warn_svg.load("./images/warning.svg")
        pol = self.warn_svg.sizePolicy()
        pol.setRetainSizeWhenHidden(True)
        self.warn_svg.setSizePolicy(pol)
        btns_lay.addWidget(self.warn_svg)
        self.warn_svg.hide()

        self.ok_btn = UPushButton(Lng.ok[cfg.lng])
        self.ok_btn.setFixedWidth(95)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = UPushButton(Lng.cancel[cfg.lng])
        cancel_btn.setFixedWidth(95)
        cancel_btn.clicked.connect(self.deleteLater)
        btns_lay.addWidget(cancel_btn)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([200, 600])

        # ссылаемся на SettingsItem.action_type
        mapping = {
            "general": 0,
            "filters": 1,
            "new_folder": 2,
        }

        if settings_item.type_ in mapping:
            idx = mapping[settings_item.type_]
            self.left_menu.setCurrentRow(idx)
            self.init_right_side(idx)
        else:
            for i in self.mf_items:
                if i.mf == self.settings_item.content:
                    index = self.left_menu.row(i)
                    self.left_menu.setCurrentRow(index)
                    self.init_right_side(index)
                    break

    def blink_ok_btn(self):
        self.ok_btn.setText(Lng.restart[cfg.lng])
        self.warn_svg.show()

    def init_right_side(self, index: int):
        if index == 0:
            self.gen_settings = GeneralSettings(self.cfg_clone, self.what_change)
            self.gen_settings.changed.connect(self.blink_ok_btn)
            self.right_lay.insertWidget(0, self.gen_settings)
        elif index == 1:
            self.filters_wid = FiltersWid(self.filters_clone)
            self.filters_wid.changed.connect(self.blink_ok_btn)
            self.right_lay.insertWidget(0, self.filters_wid)
        elif index == 2:
            self.new_folder = NewFolder(self.mf_list_clone)
            self.new_folder.new_folder.connect(self.add_mf)
            self.right_lay.insertWidget(0, self.new_folder)
            if self.settings_item.type_ == "general":
                self.new_folder.preset_new_folder("")
            else:
                self.new_folder.preset_new_folder(self.settings_item.content)
        else:
            # Находим в копии списка Mf объект с нужным именем,
            # чтобы передать его в дочерний виджет MfSettings.
            # Изменения, внесённые в дочернем виджете, будут напрямую
            # применяться к этому объекту в копии списка.
            item: UListWidgetItem = self.left_menu.item(index)
            mf = next(
                i
                for i in self.mf_list_clone
                if i.alias == item.text()
            )
            mf_sett = MfSettings(mf)
            mf_sett.changed.connect(self.blink_ok_btn)
            self.right_lay.insertWidget(0, mf_sett)

        self.settings_item.type_ = "general"

    def add_mf(self, mf: Mf):
        self.mf_list_clone.append(mf)
        item = UListWidgetItem(self.left_menu, text=mf.alias)
        item.setIcon(QIcon(self.svg_folder))
        item.mf = mf
        self.left_menu.addItem(item)
        self.left_menu.setCurrentItem(item)
        self.clear_right_side()
        index = self.left_menu.count() - 1
        self.init_right_side(index)
        self.blink_ok_btn()

    def remove_mf(self, item: UListWidgetItem):

        def fin():
            for i in self.mf_list_clone:
                if i.alias == item.text():
                    self.mf_list_clone.remove(i)
                    self.left_menu.takeItem(self.left_menu.currentRow())
                    self.left_menu.setCurrentRow(0)
                    self.clear_right_side()
                    self.init_right_side(0)
                    self.blink_ok_btn()
                    break

        try:
            if len(self.mf_list_clone) == 1:
                self.win_warn = WinWarn(
                    Lng.attention[cfg.lng],
                    Lng.at_least_one_folder_required[cfg.lng],
                )
                self.win_warn.resize(360, 80)
                self.win_warn.center_to_parent(self)
                self.win_warn.show()
            else:
                fin()

        except Exception as e:
            print("win settings > ошибка удаления main folder по кнопке удалить", e)

    def clear_right_side(self):
        wids = (GeneralSettings, MfSettings, NewFolder, FiltersWid)
        right_wid = self.right_wid.findChild(wids)
        right_wid.deleteLater()

    def left_menu_click(self, *args):
        self.clear_right_side()
        index = self.left_menu.currentRow()
        self.init_right_side(index)

    def ok_cmd(self):

        def validate_folders() -> bool:
            """Check that all folders have paths, show warning if not."""
            for folder in self.mf_list_clone:
                if not folder.paths:
                    self.win_warn = WinWarn(
                        Lng.attention[cfg.lng],
                        f"{Lng.select_folder_path[cfg.lng]} \"{folder.alias}\""
                    )
                    self.win_warn.resize(330, 80)
                    self.win_warn.center_to_parent(self.window())
                    self.win_warn.show()
                    return False
            return True

        if self.ok_btn.text() in Lng.restart:
            if not validate_folders():
                return
            if self.need_reset_item.need_reset:
                shutil.rmtree(Static.app_support)
            else:
                Mf.list_ = self.mf_list_clone
                Filters.filters = self.filters_clone
                for key, value in vars(self.cfg_clone).items():
                    setattr(cfg, key, value)
                Mf.write_json_data()
                Filters.write_json_data()
                cfg.write_json_data()
            QApplication.quit()
            Utils.start_new_app()
        else:
            self.deleteLater()

    def deleteLater(self):
        self.closed.emit()
        return super().deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    
    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)