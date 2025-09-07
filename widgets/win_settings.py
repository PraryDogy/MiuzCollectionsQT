import copy
import os
import shutil
import subprocess

from PyQt5.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QFrame,
                             QGroupBox, QLabel, QPushButton, QSpacerItem,
                             QSpinBox, QSplitter, QTabWidget, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.main_folder import MainFolder
from system.paletes import ThemeChanger
from system.utils import MainUtils

from ._base_widgets import (UHBoxLayout, ULineEdit, UListSpaserItem,
                            UListWidgetItem, UMenu, UTextEdit, UVBoxLayout,
                            VListWidget, WinChild, WinSystem)
from .win_help import WinHelp
from .win_warn import WinQuestion, WinWarn

# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ 


class LangReset(QGroupBox):
    reset = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg):
        super().__init__()
        self.json_data = json_data_copy

        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        first_row_lay = UHBoxLayout()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.lang_btn = QPushButton(text=Lng.russian[Cfg.lng])
        self.lang_btn.setFixedWidth(115)
        self.lang_btn.clicked.connect(self.lang_btn_cmd)
        first_row_lay.addWidget(self.lang_btn)

        self.lang_label = QLabel(Lng.language[Cfg.lng])
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sec_row_wid.setLayout(sec_row_lay)

        self.reset_data_btn = QPushButton(Lng.reset[Cfg.lng])
        self.reset_data_btn.setFixedWidth(115)
        self.reset_data_btn.clicked.connect(self.changed.emit)
        self.reset_data_btn.clicked.connect(self.reset.emit)
        sec_row_lay.addWidget(self.reset_data_btn)

        descr = QLabel(text=Lng.reset_settings[Cfg.lng])
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def lang_btn_cmd(self, *args):
        if self.json_data.lng == 0:
            self.json_data.lng = 1
        else:
            self.json_data.lng = 0
        self.lang_btn.setText(Lng.russian[self.json_data.lng])
        self.changed.emit()


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

        self.show_files_btn = QPushButton(text=Lng.show[Cfg.lng])
        self.show_files_btn.setFixedWidth(115)
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        first_row_lay.addWidget(self.show_files_btn)

        self.lang_label = QLabel(Lng.show_system_files[Cfg.lng])
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        v_lay.addWidget(sec_row_wid)
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_wid.setLayout(sec_row_lay)

        self.help_btn = QPushButton(text=Lng.help_[Cfg.lng])
        self.help_btn.setFixedWidth(115)
        self.help_btn.clicked.connect(self.show_help)
        sec_row_lay.addWidget(self.help_btn)

        self.lang_label = QLabel(Lng.show_help_window[Cfg.lng])
        sec_row_lay.addWidget(self.lang_label)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.APP_SUPPORT_DIR])
        except Exception as e:
            print(e)

    def show_help(self, *args):
        self.help_win = WinHelp()
        self.help_win.center_relative_parent(self.window())
        self.help_win.show()


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
        self.spin.setMaximum(60)
        self.spin.setSuffix(f" {Lng.minutes[Cfg.lng]}")
        self.spin.setValue(self.json_data_copy.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        self.spin_lay.addWidget(self.spin)

        label = QLabel(Lng.search_interval[Cfg.lng], self)
        self.spin_lay.addWidget(label)

        self.theme_changed()

        first_row = QWidget()
        self.main_lay.addWidget(first_row)
        first_lay = UHBoxLayout()
        first_lay.setSpacing(15)
        first_row.setLayout(first_lay)

        self.checkbox = QPushButton()
        self.checkbox.clicked.connect(self.change_new_scaner)
        self.checkbox.setFixedWidth(115)
        first_lay.addWidget(self.checkbox)

        self.checkbox_lbl = QLabel(Lng.fast_image_search[Cfg.lng])
        first_lay.addWidget(self.checkbox_lbl)

        if self.json_data_copy.new_scaner:
            self.checkbox.setText(Lng.disable[Cfg.lng])
        else:
            self.checkbox.setText(Lng.enable[Cfg.lng])

        self.checkbox.setChecked(True)

    def theme_changed(self):
        if self.json_data_copy.dark_mode == 0:
            self.spin_lay.setContentsMargins(5, 0, 0, 0)
            self.spin.setFixedWidth(104)
        else:
            self.spin_lay.setContentsMargins(0, 0, 0, 0)
            self.spin.setFixedWidth(115)

    def change_scan_time(self, value: int):
        self.json_data_copy.scaner_minutes = value
        self.changed.emit()

    def change_new_scaner(self):
        if self.json_data_copy.new_scaner:
            self.json_data_copy.new_scaner = False
            self.checkbox.setText(Lng.enable[Cfg.lng])
        else:
            self.json_data_copy.new_scaner = True
            self.checkbox.setText(Lng.disable[Cfg.lng])
        self.changed.emit()


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

        label = QLabel(label_text)
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
    theme_changed = pyqtSignal()
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
            Lng.theme_auto[Cfg.lng]
        )
        self.dark_theme = ThemesBtn(
            self.svg_theme_dark,
            Lng.theme_dark[Cfg.lng]
        )
        self.light_theme = ThemesBtn(
            self.svg_theme_light,
            Lng.theme_light[Cfg.lng]
        )

        for f in (self.system_theme, self.dark_theme, self.light_theme):
            h_lay.addWidget(f)
            self.frames.append(f)
            f.clicked.connect(self.on_frame_clicked)

        if Cfg.dark_mode == 0:
            self.set_selected(self.system_theme)
        elif Cfg.dark_mode == 1:
            self.set_selected(self.dark_theme)
        elif Cfg.dark_mode == 2:
            self.set_selected(self.light_theme)

    def on_frame_clicked(self):
        sender: ThemesBtn = self.sender()
        self.set_selected(sender)

        if sender == self.system_theme:
            Cfg.dark_mode = 0
        elif sender == self.dark_theme:
            Cfg.dark_mode = 1
        elif sender == self.light_theme:
            Cfg.dark_mode = 2

        ThemeChanger.init()
        self.theme_changed.emit()

    def set_selected(self, selected_frame: ThemesBtn):
        for f in self.frames:
            f.selected(f is selected_frame)


class SelectableLabel(QLabel):
    txt = "\n".join([
        f"Version {Static.APP_VER}",
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

        copy_text = QAction(parent=context_menu, text=Lng.copy[Cfg.lng])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lng.copy_all[Cfg.lng])
        select_all.triggered.connect(lambda: MainUtils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_()
        return super().contextMenuEvent(ev)

    def copy_text_md(self):
        MainUtils.copy_text(self.selectedText())


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
    reset = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(10)
        self.setLayout(v_lay)

        lang_reset = LangReset(json_data_copy)
        lang_reset.reset.connect(self.reset.emit)
        lang_reset.changed.connect(self.changed.emit)
        v_lay.addWidget(lang_reset)

        simple_settings = SimpleSettings()
        v_lay.addWidget(simple_settings)

        scaner_settings = ScanerSettings(json_data_copy)
        scaner_settings.changed.connect(self.changed.emit)
        v_lay.addWidget(scaner_settings)

        themes = Themes()
        themes.theme_changed.connect(scaner_settings.theme_changed)
        v_lay.addWidget(themes)

        about = AboutWid()
        v_lay.addWidget(about)


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

        self.top_label = QLabel()
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
    

class MainFolderPaths(DropableGroupBox):
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.text_changed.connect(self.set_data)
        self.text_edit.setPlaceholderText(Lng.folder_path[Cfg.lng])

    def set_data(self, *args):
        self.main_folder.paths = self.get_data()

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
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.text_changed.connect(self.set_data)
        self.text_edit.setPlaceholderText(Lng.ignore_list[Cfg.lng])

    def set_data(self, *args):
        self.main_folder.stop_list = self.get_data()

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


class MainFolderAdvanced(QWidget):
    changed = pyqtSignal()

    def __init__(self, main_folder: MainFolder):
        super().__init__()
        v_lay = UVBoxLayout()
        self.setLayout(v_lay)

        sec_row = MainFolderPaths(main_folder)
        sec_row.text_changed.connect(self.changed.emit)
        v_lay.addWidget(sec_row)
        sec_row.top_label.setText(Lng.collections_folder_path[Cfg.lng])
        text_ = "\n".join(i for i in main_folder.paths)
        sec_row.text_edit.setPlainText(text_)

        third_row = StopList(main_folder)
        third_row.text_changed.connect(self.changed.emit)
        v_lay.addWidget(third_row)
        third_row.top_label.setText(Lng.ignore_list_descr[Cfg.lng])
        text_ = "\n".join(i for i in main_folder.stop_list)
        third_row.text_edit.setPlainText(text_)


class MainFolderSettings(QWidget):
    remove = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, main_folder: MainFolder):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(15)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(v_lay)

        first_row = QGroupBox()
        first_row.setFixedHeight(50)
        v_lay.addWidget(first_row)
        first_lay = UHBoxLayout()
        first_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        first_lay.setSpacing(5)
        first_row.setLayout(first_lay)
        name_descr = QLabel(Lng.folder_name[Cfg.lng] + ":")
        first_lay.addWidget(name_descr)
        name_label = QLabel(main_folder.name)
        first_lay.addWidget(name_label)

        advanced = MainFolderAdvanced(main_folder)
        advanced.changed.connect(self.changed.emit)
        v_lay.addWidget(advanced)

        remove_btn = QPushButton(Lng.delete[Cfg.lng])
        remove_btn.clicked.connect(self.remove.emit)
        remove_btn.setFixedWidth(100)

        btn_lay = UHBoxLayout()
        btn_lay.addStretch()
        btn_lay.addWidget(remove_btn)
        btn_lay.addStretch()
        v_lay.addLayout(btn_lay)
        
        v_lay.addStretch()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА 


class NewFolder(QWidget):
    new_folder = pyqtSignal(MainFolder)

    def __init__(self, main_folder_list: list[MainFolder]):
        super().__init__()
        self.main_folder = MainFolder("", [], [])
        self.main_folder_list = main_folder_list

        v_lay = UVBoxLayout()
        v_lay.setSpacing(15)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(v_lay)

        first_row = QGroupBox()
        first_row.setFixedHeight(50)
        v_lay.addWidget(first_row)
        first_lay = UVBoxLayout()
        first_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        first_lay.setSpacing(5)
        first_row.setLayout(first_lay)
        self.name_label = ULineEdit()
        self.name_label.setPlaceholderText(Lng.folder_name_immutable[Cfg.lng])
        self.name_label.textChanged.connect(self.name_cmd)
        first_lay.addWidget(self.name_label)

        self.advanced = MainFolderAdvanced(self.main_folder)
        v_lay.addWidget(self.advanced)

        add_btn = QPushButton(Lng.save[Cfg.lng])
        add_btn.clicked.connect(self.save)
        add_btn.setFixedWidth(100)

        btn_lay = UHBoxLayout()
        btn_lay.addStretch()
        btn_lay.addWidget(add_btn)
        btn_lay.addStretch()
        v_lay.addLayout(btn_lay)
        
        v_lay.addStretch()

    def name_cmd(self):
        name = self.name_label.text().strip()
        self.main_folder.name = name

    def save(self):        
        if not self.main_folder.name:
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                Lng.enter_folder_name[Cfg.lng]
                )
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()
        elif any(i.name == self.main_folder.name for i in self.main_folder_list):
            t = (
                f"{Lng.folder_name_error[Cfg.lng]}.",
                f"{Lng.name[Cfg.lng]} \"{self.main_folder.name}\" {Lng.name_taken[Cfg.lng].lower()}."
                )
            t = "\n".join(t)
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                t
                )
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()
        elif not self.main_folder.paths:
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                Lng.select_folder_path[Cfg.lng]
                )
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()
        else:
            self.new_folder.emit(self.main_folder)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class WinSettings(WinSystem):
    left_side_width = 210
    closed = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle(Lng.settings[Cfg.lng])
        self.main_folder_list = copy.deepcopy(MainFolder.list_)
        self.json_data_copy = copy.deepcopy(Cfg())
        self.need_reset = False

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.left_menu.clicked.connect(self.left_menu_click)
        self.splitter.addWidget(self.left_menu)

        main_settings_item = UListWidgetItem(self.left_menu, text=Lng.general[Cfg.lng])
        self.left_menu.addItem(main_settings_item)

        item = UListWidgetItem(self.left_menu, text=Lng.new_folder[Cfg.lng])
        self.left_menu.addItem(item)
        
        spacer = UListSpaserItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in MainFolder.list_:
            item = UListWidgetItem(self.left_menu, text=i.name)
            self.left_menu.addItem(item)

        self.left_menu.setCurrentRow(0)

        self.right_wid = QWidget()
        self.right_wid.setFixedWidth(450)
        self.right_lay = UVBoxLayout()
        self.right_wid.setLayout(self.right_lay)
        self.splitter.addWidget(self.right_wid)

        btns_wid = QWidget()
        btns_wid.setFixedHeight(40)
        self.right_lay.addWidget(btns_wid, alignment=Qt.AlignmentFlag.AlignBottom)
        btns_lay = UHBoxLayout()
        btns_lay.setSpacing(15)
        btns_wid.setLayout(btns_lay)
        btns_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ok_btn = QPushButton(Lng.ok[Cfg.lng])
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(100)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = QPushButton(Lng.cancel[Cfg.lng])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(100)
        btns_lay.addWidget(cancel_btn)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([self.left_side_width, 600])

        self.init_right_side()

    def init_right_side(self, *args):
        ind = self.left_menu.currentRow()

        if ind == 0:
            self.gen_settings = GeneralSettings(self.json_data_copy)
            self.gen_settings.reset.connect(lambda: setattr(self, "need_reset", True))
            self.gen_settings.changed.connect(lambda: self.ok_btn.setText(Lng.restart[Cfg.lng]))
            self.right_lay.insertWidget(0, self.gen_settings)
        elif ind == 1:
            self.new_folder = NewFolder(self.main_folder_list)
            self.new_folder.new_folder.connect(self.add_main_folder)
            self.right_lay.insertWidget(0, self.new_folder)
        else:
            main_folder = [
                x
                for x in self.main_folder_list
                if x.name == self.left_menu.currentItem().text()
                ]
            
            if len(main_folder) == 1:
                item = self.left_menu.currentItem()
                main_folder_sett = MainFolderSettings(main_folder[0])
                main_folder_sett.changed.connect(lambda: self.ok_btn.setText(Lng.restart[Cfg.lng]))
                main_folder_sett.remove.connect(lambda: self.remove_main_folder(main_folder[0], item))
                self.right_lay.insertWidget(0, main_folder_sett)
            else:
                self.left_menu.setCurrentRow(0)
                self.init_right_side()

    def add_main_folder(self, main_folder: MainFolder):
        self.main_folder_list.append(main_folder)
        item = UListWidgetItem(self.left_menu, text=main_folder.name)
        self.left_menu.addItem(item)
        self.left_menu.setCurrentItem(item)
        self.clear_right_side()
        self.init_right_side()
        self.ok_btn.setText(Lng.restart[Cfg.lng])

    def remove_main_folder(self, main_folder: MainFolder, item: UListWidgetItem):

        def fin():
            self.main_folder_list.remove(main_folder)
            self.left_menu.takeItem(self.left_menu.currentRow())
            self.left_menu.setCurrentRow(0)
            self.clear_right_side()
            self.init_right_side()
            self.ok_btn.setText(Lng.restart[Cfg.lng])

        try:
            if len(self.main_folder_list) == 1:
                self.win_warn = WinWarn(
                    Lng.attention[Cfg.lng],
                    Lng.at_least_one_folder_required[Cfg.lng],
                )
                self.win_warn.center_relative_parent(self)
                self.win_warn.show()
            else:
                self.win_question = WinQuestion(
                    Lng.attention[Cfg.lng],
                    Lng.confirm_delete_folder[Cfg.lng],
                )
                self.win_question.center_relative_parent(self)
                self.win_question.ok_clicked.connect(fin)
                self.win_question.ok_clicked.connect(self.win_question.deleteLater)
                self.win_question.show()

        except Exception as e:
            print("win settings > ошибка удаления main folder по кнопке удалить", e)

    def clear_right_side(self):
        wids = (GeneralSettings, MainFolderSettings, NewFolder)
        for i in self.right_wid.findChildren(wids):
            i.deleteLater()

    def left_menu_click(self, *args):
        self.clear_right_side()
        self.init_right_side()

    def ok_cmd(self):
        if self.need_reset:
            shutil.rmtree(Static.APP_SUPPORT_DIR)
            QApplication.quit()
            MainUtils.start_new_app()

        elif self.ok_btn.text() == Lng.restart[Cfg.lng]:
            for i in self.main_folder_list:
                if not i.paths:
                    self.win_warn = WinWarn(
                        Lng.attention[Cfg.lng],
                        f"{Lng.select_folder_path[Cfg.lng]} \"{i.name}\""
                        )
                    self.win_warn.center_relative_parent(self.window())
                    self.win_warn.show()
                    return
            MainFolder.list_ = self.main_folder_list
            for k, v in vars(self.json_data_copy).items():
                setattr(Cfg, k, v)
            MainFolder.write_json_data()
            Cfg.write_json_data()
            QApplication.quit()
            MainUtils.start_new_app()

        else:
            self.deleteLater()

    def deleteLater(self):
        self.closed.emit()
        return super().deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)