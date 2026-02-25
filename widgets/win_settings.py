import copy
import os
import re
import shutil
import subprocess

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QIcon
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame, QGroupBox, QLabel,
                             QLineEdit, QSpacerItem, QSpinBox, QSplitter,
                             QTableWidget, QTableWidgetItem, QWidget)

from cfg import Cfg, Static, cfg
from system.filters import Filters
from system.items import NeedResetItem, SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.paletes import ThemeChanger
from system.shared_utils import SharedUtils
from system.tasks import HashDirSize, UThreadPool
from system.utils import Utils

from ._base_widgets import (SingleActionWindow, SmallBtn, UHBoxLayout,
                            ULineEdit, UListSpacerItem, UListWidgetItem, UMenu,
                            UTextEdit, UVBoxLayout, VListWidget)
from .win_warn import WinQuestion, WinWarn

# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ 


class ULabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(30)


class UPushButton(SmallBtn):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(100)


class LangSettings(QGroupBox):
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg):
        super().__init__()
        self.json_data_copy = json_data_copy

        v_lay = UVBoxLayout()
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        first_row_lay = UHBoxLayout()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.lang_btn = UPushButton(text=Lng.russian[cfg.lng])
        self.lang_btn.clicked.connect(self.lang_btn_cmd)
        first_row_lay.addWidget(self.lang_btn)

        self.lang_label = ULabel(Lng.language_max[cfg.lng])
        first_row_lay.addWidget(self.lang_label)

        v_lay.addWidget(first_row_wid)


    def lang_btn_cmd(self, *args):
        if self.json_data_copy.lng == 0:
            self.json_data_copy.lng = 1
        else:
            self.json_data_copy.lng = 0
        self.lang_btn.setText(Lng.russian[self.json_data_copy.lng])
        self.changed.emit()


class SizesWin(SingleActionWindow):
    def __init__(self, sizes: dict[str, int], parent=None):
        super().__init__(parent)
        self.setWindowTitle(Lng.data_size[cfg.lng])
        self.resize(500, 330)

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


class DataSettings(QGroupBox):
    reset = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.v_lay = UVBoxLayout()
        self.setLayout(self.v_lay)

        first_wid = QWidget()
        first_lay = UHBoxLayout()
        first_lay.setSpacing(15)
        first_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        first_wid.setLayout(first_lay)

        self.reset_data_btn = UPushButton(Lng.reset[cfg.lng])
        self.reset_data_btn.clicked.connect(self.reset_cmd)
        first_lay.addWidget(self.reset_data_btn)

        reset_lbl = ULabel(Lng.reset_settings[cfg.lng])
        first_lay.addWidget(reset_lbl)

        self.v_lay.addWidget(first_wid)

        sec_wid = QWidget()
        sec_lay = UHBoxLayout()
        sec_lay.setSpacing(15)
        sec_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sec_wid.setLayout(sec_lay)

        self.data_size_btn = UPushButton(Lng.show[cfg.lng])
        sec_lay.addWidget(self.data_size_btn)

        self.size_lbl = ULabel(text=Lng.statistic[cfg.lng])
        sec_lay.addWidget(self.size_lbl)

        self.v_lay.addWidget(sec_wid)

        self.get_sizes()

    def reset_cmd(self):

        def fin():
            self.changed.emit()
            self.reset.emit()
            self.reset_win.deleteLater()

        self.reset_win = WinQuestion(
            Lng.attention[cfg.lng],
            Lng.reset_settings_max[cfg.lng]
        )
        self.reset_win.resize(330, 80)
        self.reset_win.ok_clicked.connect(fin)
        self.reset_win.center_to_parent(self.window())
        self.reset_win.show()

    def open_win(self, data: dict):
        self.sizes_win = SizesWin(data)
        self.sizes_win.center_to_parent(self.window())
        self.sizes_win.show()

    def get_sizes(self):
        
        def on_finish(data: dict[str, dict[int, int]]):
            self.data_size_btn.disconnect()
            self.data_size_btn.clicked.connect(lambda: self.open_win(data))

        self.hashdir_size = HashDirSize()
        self.hashdir_size.sigs.finished_.connect(on_finish)
        UThreadPool.start(self.hashdir_size)


class SimpleSettings(QGroupBox):
    def __init__(self):
        super().__init__()

        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        v_lay.addWidget(first_row_wid)
        first_row_lay = UHBoxLayout()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.show_files_btn = UPushButton(text=Lng.show[cfg.lng])
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        first_row_lay.addWidget(self.show_files_btn)

        self.lang_label = ULabel(Lng.show_system_files[cfg.lng])
        first_row_lay.addWidget(self.lang_label)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.app_support])
        except Exception as e:
            print(e)


class ScanerSettings(QGroupBox):
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg):
        super().__init__()
        self.json_data_copy = json_data_copy

        self.main_lay = UVBoxLayout()
        self.main_lay.setSpacing(5)
        self.setLayout(self.main_lay)

        sec_row = QWidget()
        self.main_lay.addWidget(sec_row)
        self.spin_lay = UHBoxLayout()
        sec_row.setLayout(self.spin_lay)
        self.spin_lay.setSpacing(15)
        self.spin_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spin = QSpinBox(self)
        self.spin.setMinimum(1)
        self.spin.setMaximum(59)
        self.spin.setFixedHeight(27)
        self.spin.findChild(QLineEdit).setTextMargins(3, 0, 3, 0)
        self.spin.setSuffix(f" {Lng.minutes[cfg.lng]}")
        self.spin.setValue(self.json_data_copy.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        self.spin_lay.addWidget(self.spin)

        label = ULabel(Lng.search_interval[cfg.lng], self)
        self.spin_lay.addWidget(label)

        self.change_spin_width()

    def change_scan_time(self, value: int):
        self.json_data_copy.scaner_minutes = value
        self.changed.emit()

    def change_spin_width(self):
        if cfg.dark_mode == 0:
            self.spin.setFixedWidth(109)
        else:
            self.spin.setFixedWidth(115)


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
        h_lay = UHBoxLayout()
        h_lay.setContentsMargins(10, 10, 10, 10)
        h_lay.setSpacing(20)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(h_lay)

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
            h_lay.addWidget(f)
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

        context_menu.show_umenu()
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


class GeneralSettings(QGroupBox):
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg, need_reset_item: NeedResetItem):
        super().__init__()
        self.need_reset_item = need_reset_item
        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(10)
        v_lay.setContentsMargins(0, 0, 0, 10)
        self.setLayout(v_lay)

        lang_reset = LangSettings(json_data_copy)
        lang_reset.changed.connect(self.changed.emit)
        v_lay.addWidget(lang_reset)

        data_settings = DataSettings()
        data_settings.reset.connect(self.set_need_reset)
        data_settings.changed.connect(self.changed.emit)
        v_lay.addWidget(data_settings)

        simple_settings = SimpleSettings()
        v_lay.addWidget(simple_settings)

        scaner_settings = ScanerSettings(json_data_copy)
        scaner_settings.changed.connect(self.changed.emit)
        v_lay.addWidget(scaner_settings)

        themes = Themes()
        themes.clicked.connect(scaner_settings.change_spin_width)
        v_lay.addWidget(themes)

        about = AboutWid()
        v_lay.addWidget(about)

    def set_need_reset(self):
        print("need teset")
        self.need_reset_item.need_reset = True

# ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ


class DropableGroupBox(QGroupBox):
    text_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedHeight(150)

        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_lay.setContentsMargins(0, 10, 0, 10)
        self.setLayout(v_lay)

        self.top_label = ULabel()
        v_lay.addWidget(self.top_label)

        self.text_edit = UTextEdit()
        self.text_edit.textChanged.connect(self.text_changed.emit)
        self.text_edit.setAcceptDrops(False)
        v_lay.addWidget(self.text_edit)

    def get_data(self):
        return [
            i
            for i in self.text_edit.toPlainText().split("\n")
            if i.strip()
        ]

    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
    

class MfPaths(DropableGroupBox):
    def __init__(self, mf: Mf):
        super().__init__()
        self.mf = mf
        self.text_changed.connect(self.set_data)
        self.text_edit.setPlaceholderText(Lng.folder_path[cfg.lng])

    def set_data(self, *args):
        self.mf.paths = self.get_data()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                i.toLocalFile().rstrip(os.sep)
                for i in a0.mimeData().urls()
                if os.path.isdir(i.toLocalFile())
            ]
            text = "\n".join((self.text_edit.toPlainText(), *urls)).strip()
            self.text_edit.setPlainText(text)
        return super().dropEvent(a0)


class StopList(DropableGroupBox):
    def __init__(self, mf: Mf):
        super().__init__()
        self.mf = mf
        self.text_changed.connect(self.set_data)
        self.text_edit.setPlaceholderText(Lng.ignore_list[cfg.lng])

    def set_data(self, *args):
        self.mf.stop_list = self.get_data()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                os.path.basename(i.toLocalFile().rstrip(os.sep))
                for i in a0.mimeData().urls()
                if os.path.isdir(i.toLocalFile())
            ]
            text = "\n".join((self.text_edit.toPlainText(), *urls)).strip()
            self.text_edit.setPlainText(text)
        return super().dropEvent(a0)


class MfAdvanced(QWidget):
    changed = pyqtSignal()

    def __init__(self, mf: Mf):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(15)
        self.setLayout(v_lay)

        self.paths_wid = MfPaths(mf)
        self.paths_wid.text_changed.connect(self.changed.emit)
        v_lay.addWidget(self.paths_wid)
        self.paths_wid.top_label.setText(
            self.insert_linebreaks(Lng.images_folder_path[cfg.lng])
        )
        text_ = "\n".join(i for i in mf.paths)
        self.paths_wid.text_edit.setPlainText(text_)

        third_row = StopList(mf)
        third_row.text_changed.connect(self.changed.emit)
        v_lay.addWidget(third_row)
        third_row.top_label.setText(Lng.ignore_list_descr[cfg.lng])
        text_ = "\n".join(i for i in mf.stop_list)
        third_row.text_edit.setPlainText(text_)

    def insert_linebreaks(self, text: str, n: int = 64) -> str:
        return '\n'.join(
            text[i:i+n]
            for i in range(0, len(text), n)
        )


class MfSettings(QGroupBox):
    remove = pyqtSignal()
    changed = pyqtSignal()
    reset_data = pyqtSignal(Mf)

    def __init__(self, mf: Mf):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(15)
        self.setLayout(v_lay)

        # Верхний ряд с названием
        first_row = QGroupBox()
        first_row.setFixedHeight(30)
        v_lay.addWidget(first_row)
        first_lay = UHBoxLayout()
        first_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        first_row.setLayout(first_lay)
        name_descr = ULabel(f"{Lng.alias[cfg.lng]}: ")
        first_lay.addWidget(name_descr)
        name_label = ULabel(mf.alias)
        first_lay.addWidget(name_label)

        # Advanced настройки
        advanced = MfAdvanced(mf)
        advanced.changed.connect(self.changed.emit)
        v_lay.addWidget(advanced)

        # QGroupBox для кнопок и описания
        btn_group = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setContentsMargins(0, 0, 0, 10)
        btn_lay.setSpacing(15)
        btn_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_group.setLayout(btn_lay)

        self.reset_btn = UPushButton(Lng.reset[cfg.lng])
        self.reset_btn.clicked.connect(
            lambda: self.show_reset_win(mf)
        )
        btn_lay.addWidget(self.reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.remove_btn = UPushButton(Lng.delete[cfg.lng])
        self.remove_btn.clicked.connect(
            lambda: self.show_remove_win()
        )
        btn_lay.addWidget(self.remove_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        v_lay.addWidget(btn_group)

    def show_finish_win(self):
        self.finish_win = WinWarn(
            Lng.attention[cfg.lng],
            f"{Lng.data_was_reset[cfg.lng]}"
        )
        self.finish_win.resize(330, 80)
        self.finish_win.center_to_parent(self.window())
        self.finish_win.show()

    def show_reset_win(self, mf: Mf):
        self.reset_win = WinQuestion(
            Lng.attention[cfg.lng],
            Lng.reset_mf_text[cfg.lng]
        )
        self.reset_win.resize(380, 95)
        self.reset_win.center_to_parent(self.window())
        self.reset_win.ok_clicked.connect(
            lambda: self.show_finish_win()
        )
        self.reset_win.ok_clicked.connect(
            lambda: self.reset_data.emit(mf)
        )
        self.reset_win.ok_clicked.connect(
            lambda: self.reset_win.deleteLater()
        )
        self.reset_win.show()

    def show_remove_win(self):
        self.remove_win = WinQuestion(
            Lng.attention[cfg.lng],
            Lng.folder_removed_text[cfg.lng]
        )
        self.remove_win.resize(330, 80)
        self.remove_win.center_to_parent(self.window())
        self.remove_win.ok_clicked.connect(
            lambda: self.remove.emit()
        )
        self.remove_win.ok_clicked.connect(
            lambda: self.remove_win.deleteLater()
        )
        self.remove_win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА 

class NewFolder(QGroupBox):
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
        # first_row.setFixedHeight(50)
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
        v_lay.addWidget(self.advanced)

        btn_wid = QWidget()
        v_lay.addWidget(btn_wid)
        btn_lay = UHBoxLayout()
        btn_lay.setContentsMargins(0, 0, 0, 10)
        btn_lay.setSpacing(15)
        btn_wid.setLayout(btn_lay)

        self.save_btn = UPushButton(Lng.save[cfg.lng])
        self.save_btn.clicked.connect(self.save)
        btn_lay.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def preset_new_folder(self, url: str):
        # name = os.path.basename(url)
        # self.name_label.setText(name)
        text_edit = self.findChildren(DropableGroupBox)[0].text_edit
        text_edit.setPlainText(url)

    def name_cmd(self):
        name = self.name_label.text().strip()
        self.mf.alias = name

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

        elif any(i.alias == self.mf.alias for i in self.mf_list):
            show_warn(
                f'{Lng.alias[cfg.lng]} "{self.mf.alias}" '
                f'{Lng.already_taken[cfg.lng].lower()}.'
            )

        elif len(self.mf.alias) > 30:
            show_warn(f'{Lng.string_limit[cfg.lng]}.')

        elif not re.fullmatch(pattern, self.mf.alias):
            show_warn(f'{Lng.valid_message[cfg.lng]}.')

        elif not self.mf.paths:
            show_warn(Lng.select_folder_path[cfg.lng], width=330)

        else:
            self.new_folder.emit(self.mf)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)



# ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ 


class FiltersWid(QGroupBox):
    changed = pyqtSignal()

    def __init__(self, filters_copy: list[str]):
        super().__init__()
        self.filters_copy = filters_copy

        self.v_lay = UVBoxLayout()
        self.v_lay.setSpacing(15)
        self.setLayout(self.v_lay)

        group = QGroupBox()
        g_lay = UVBoxLayout(group)
        g_lay.setSpacing(15)

        descr = ULabel(Lng.filters_descr[cfg.lng])
        g_lay.addWidget(descr)

        self.text_wid = UTextEdit()
        self.text_wid.setFixedHeight(220)
        self.text_wid.setPlaceholderText(Lng.filters[cfg.lng])
        self.text_wid.setPlainText("\n".join(self.filters_copy))
        self.text_wid.textChanged.connect(self.on_text_changed)
        g_lay.addWidget(self.text_wid)
        self.v_lay.addWidget(group)

        btns_wid = QWidget()
        self.v_lay.addWidget(btns_wid)
        btns_lay = UHBoxLayout()
        btns_lay.setContentsMargins(0, 0, 0, 10)
        btns_wid.setLayout(btns_lay)

        reset_btn = UPushButton(Lng.reset[cfg.lng])
        reset_btn.clicked.connect(self.reset_filters)
        btns_lay.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def reset_filters(self):

        def fin():
            self.text_wid.clear()
            self.text_wid.insertPlainText(
                "\n".join(Filters.default)
            )
            self.filters_win.deleteLater()

        self.filters_win = WinQuestion(
            Lng.attention[cfg.lng],
            Lng.filters_reset[cfg.lng]
        )
        self.filters_win.resize(330, 80)
        self.filters_win.ok_clicked.connect(fin)
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def on_text_changed(self):
        text = self.text_wid.toPlainText().strip()
        lines = [line for line in text.split("\n") if line]

        self.filters_copy.clear()   # очищаем текущий список
        self.filters_copy.extend(lines)  # добавляем новые элементы
        
        self.changed.emit()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)

# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class SettingsListItem(UListWidgetItem):
    def __init__(self, parent, height = 30, text = None):
        super().__init__(parent, height, text)
        self.mf: Mf = None


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
        self.mf_list_copy = copy.deepcopy(Mf.list_)
        self.json_data_copy = copy.deepcopy(cfg)
        self.filters_copy = copy.deepcopy(Filters.filters)
        self.need_reset_item = NeedResetItem()
        self.mf_items: list[SettingsListItem] = []
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

        main_settings_item = SettingsListItem(self.left_menu, text=Lng.general[cfg.lng])
        main_settings_item.setIcon(QIcon(self.svg_settings))
        self.left_menu.addItem(main_settings_item)
        
        filter_settings = SettingsListItem(self.left_menu, text=Lng.filters[cfg.lng])
        filter_settings.setIcon(QIcon(self.svg_filters))
        self.left_menu.addItem(filter_settings)

        new_folder = SettingsListItem(self.left_menu, text=Lng.new_folder[cfg.lng])
        new_folder.setIcon(QIcon(self.svg_new_folder))
        self.left_menu.addItem(new_folder)
        
        spacer = UListSpacerItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in Mf.list_:
            new_folder = SettingsListItem(self.left_menu, text=i.alias)
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
        btns_wid.setFixedHeight(40)
        self.right_lay.addWidget(btns_wid, alignment=Qt.AlignmentFlag.AlignBottom)
        btns_lay = UHBoxLayout()
        btns_lay.setSpacing(15)
        btns_wid.setLayout(btns_lay)
        btns_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ok_btn = UPushButton(Lng.ok[cfg.lng])
        self.ok_btn.setFixedWidth(90)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = UPushButton(Lng.cancel[cfg.lng])
        cancel_btn.setFixedWidth(90)
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

    def init_right_side(self, index: int):
        if index == 0:
            self.gen_settings = GeneralSettings(self.json_data_copy, self.need_reset_item)
            self.gen_settings.changed.connect(lambda: self.ok_btn.setText(Lng.restart[cfg.lng]))
            self.right_lay.insertWidget(0, self.gen_settings)
        elif index == 1:
            self.filters_wid = FiltersWid(self.filters_copy)
            self.filters_wid.changed.connect(lambda: self.ok_btn.setText(Lng.restart[cfg.lng]))
            self.right_lay.insertWidget(0, self.filters_wid)
        elif index == 2:
            self.new_folder = NewFolder(self.mf_list_copy)
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
            item: SettingsListItem = self.left_menu.item(index)
            mf = next(
                i
                for i in self.mf_list_copy
                if i.alias == item.mf.alias
            )
            mf_sett = MfSettings(mf)
            mf_sett.changed.connect(lambda: self.ok_btn.setText(Lng.restart[cfg.lng]))
            mf_sett.remove.connect(lambda: self.remove_mf(item))
            mf_sett.reset_data.connect(lambda mf: self.reset_data.emit(mf))
            self.right_lay.insertWidget(0, mf_sett)

        self.settings_item.type_ = "general"

    def add_mf(self, mf: Mf):
        self.mf_list_copy.append(mf)
        item = SettingsListItem(self.left_menu, text=mf.alias)
        item.setIcon(QIcon(self.svg_folder))
        item.mf = mf
        self.left_menu.addItem(item)
        self.left_menu.setCurrentItem(item)
        self.clear_right_side()
        index = self.left_menu.count() - 1
        self.init_right_side(index)
        self.ok_btn.setText(Lng.restart[cfg.lng])

    def remove_mf(self, item: SettingsListItem):

        def fin():
            for i in self.mf_list_copy:
                if i.alias == item.mf.alias:
                    self.mf_list_copy.remove(i)
                    self.left_menu.takeItem(self.left_menu.currentRow())
                    self.left_menu.setCurrentRow(0)
                    self.clear_right_side()
                    self.init_right_side(0)
                    self.ok_btn.setText(Lng.restart[cfg.lng])
                    break

        try:
            if len(self.mf_list_copy) == 1:
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
            for folder in self.mf_list_copy:
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
        

        # print(self.need_reset_item.need_reset)
        # self.deleteLater()
        # return

        if self.ok_btn.text() in Lng.restart:
            if not validate_folders():
                return
            if self.need_reset_item.need_reset:
                shutil.rmtree(Static.app_support)
            else:
                Mf.list_ = self.mf_list_copy
                Filters.filters = self.filters_copy
                for key, value in vars(self.json_data_copy).items():
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