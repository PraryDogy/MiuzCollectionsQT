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
from system.filters import Filters
from system.lang import Lng
from system.main_folder import MainFolder
from system.paletes import ThemeChanger
from system.utils import MainUtils

from ._base_widgets import (AppModalWindow, SingleActionWindow, UHBoxLayout,
                            ULineEdit, UListSpacerItem, UListWidgetItem, UMenu,
                            UTextEdit, UVBoxLayout, VListWidget, SettingsItem)
from .win_warn import WinQuestion, WinWarn

# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ 


class QLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWordWrap(True)


class LangReset(QGroupBox):
    reset = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg):
        super().__init__()
        self.json_data_copy = json_data_copy

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
        if self.json_data_copy.lng == 0:
            self.json_data_copy.lng = 1
        else:
            self.json_data_copy.lng = 0
        self.lang_btn.setText(Lng.russian[self.json_data_copy.lng])
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

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.APP_SUPPORT_DIR])
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

        context_menu.show_umenu()
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
    changed = pyqtSignal()

    def __init__(self, json_data_copy: Cfg, need_reset: list[bool]):
        super().__init__()
        self.need_reset = need_reset
        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(10)
        self.setLayout(v_lay)

        lang_reset = LangReset(json_data_copy)
        lang_reset.reset.connect(self.set_need_reset)
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

    def set_need_reset(self):
        self.need_reset[0] = True

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
        self.top_label.setWordWrap(True)
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

        self.paths_wid = MainFolderPaths(main_folder)
        self.paths_wid.text_changed.connect(self.changed.emit)
        v_lay.addWidget(self.paths_wid)
        self.paths_wid.top_label.setText(Lng.images_folder_path[Cfg.lng])
        text_ = "\n".join(i for i in main_folder.paths)
        self.paths_wid.text_edit.setPlainText(text_)

        third_row = StopList(main_folder)
        third_row.text_changed.connect(self.changed.emit)
        v_lay.addWidget(third_row)
        third_row.top_label.setText(Lng.ignore_list_descr[Cfg.lng])
        text_ = "\n".join(i for i in main_folder.stop_list)
        third_row.text_edit.setPlainText(text_)


class MainFolderSettings(QWidget):
    remove = pyqtSignal()
    changed = pyqtSignal()
    reset_data = pyqtSignal(MainFolder)

    def __init__(self, main_folder: MainFolder):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(v_lay)

        # Верхний ряд с названием
        first_row = QGroupBox()
        first_row.setFixedHeight(50)
        v_lay.addWidget(first_row)
        first_lay = UHBoxLayout()
        first_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        first_lay.setSpacing(5)
        first_row.setLayout(first_lay)
        name_descr = QLabel(Lng.alias[Cfg.lng] + ":")
        first_lay.addWidget(name_descr)
        name_label = QLabel(main_folder.name)
        first_lay.addWidget(name_label)

        # Advanced настройки
        advanced = MainFolderAdvanced(main_folder)
        advanced.changed.connect(self.changed.emit)
        v_lay.addWidget(advanced)

        # QGroupBox для кнопок и описания
        btn_group = QGroupBox()
        btn_group_lay = UVBoxLayout()
        btn_group_lay.setSpacing(10)
        btn_group_lay.setContentsMargins(0, 5, 0, 5)
        btn_group.setLayout(btn_group_lay)

        # Первая строка: кнопка "Сброс" и описание
        btn_first_row = QWidget()
        first_row_lay = UHBoxLayout()
        first_row_lay.setSpacing(15)
        first_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        btn_first_row.setLayout(first_row_lay)

        reset_btn = QPushButton(Lng.reset[Cfg.lng])
        reset_btn.clicked.connect(lambda: self.reset_data.emit(main_folder))
        reset_btn.setFixedWidth(100)
        first_row_lay.addWidget(reset_btn)

        first_desc = QLabel(Lng.reset_btn_description[Cfg.lng])
        first_row_lay.addWidget(first_desc)

        btn_group_lay.addWidget(btn_first_row)

        # Вторая строка: кнопка "Ок" и описание
        btn_second_row = QWidget()
        second_row_lay = UHBoxLayout()
        second_row_lay.setSpacing(15)
        second_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        btn_second_row.setLayout(second_row_lay)

        remove_btn = QPushButton(Lng.delete[Cfg.lng])
        remove_btn.clicked.connect(self.remove.emit)
        remove_btn.setFixedWidth(100)
        second_row_lay.addWidget(remove_btn)

        second_desc = QLabel(Lng.remove_btn_description[Cfg.lng])
        # second_desc.setWordWrap(True)
        second_row_lay.addWidget(second_desc)

        btn_group_lay.addWidget(btn_second_row)

        v_lay.addWidget(btn_group)
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
        v_lay.setSpacing(5)
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
        self.name_label.setPlaceholderText(Lng.alias_immutable[Cfg.lng])
        self.name_label.textChanged.connect(self.name_cmd)
        first_lay.addWidget(self.name_label)

        self.advanced = MainFolderAdvanced(self.main_folder)
        v_lay.addWidget(self.advanced)

        # QGroupBox для кнопки "Сохранить" и описания
        btn_group = QGroupBox()
        btn_group_lay = UHBoxLayout()
        btn_group_lay.setContentsMargins(0, 5, 0, 5)
        btn_group_lay.setSpacing(15)
        btn_group_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        btn_group.setLayout(btn_group_lay)

        add_btn = QPushButton(Lng.save[Cfg.lng])
        add_btn.clicked.connect(self.save)
        add_btn.setFixedWidth(100)
        btn_group_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        description_label = QLabel(Lng.save_btn_description[Cfg.lng])
        btn_group_lay.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignRight)

        v_lay.addWidget(btn_group)
        v_lay.addStretch()

        
    def preset_new_folder(self, url: str):
        name = os.path.basename(url)
        self.name_label.setText(name)
        text_edit = self.findChildren(DropableGroupBox)[0].text_edit
        text_edit.setPlainText(url)

    def name_cmd(self):
        name = self.name_label.text().strip()
        self.main_folder.name = name

    def save(self):        
        if not self.main_folder.name:
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                Lng.enter_alias_warning[Cfg.lng]
                )
            self.win_warn.center_to_parent(self.window())
            self.win_warn.show()
        elif any(i.name == self.main_folder.name for i in self.main_folder_list):
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                f"{Lng.alias[Cfg.lng]} \"{self.main_folder.name}\" {Lng.already_taken[Cfg.lng].lower()}."
                )
            self.win_warn.center_to_parent(self.window())
            self.win_warn.show()
        elif not self.main_folder.paths:
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                Lng.select_folder_path[Cfg.lng]
                )
            self.win_warn.center_to_parent(self.window())
            self.win_warn.show()
        else:
            self.new_folder.emit(self.main_folder)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)



# ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ ФИЛЬТРЫ 


class FiltersWid(QWidget):
    changed = pyqtSignal()

    def __init__(self, filters_copy: list[str]):
        super().__init__()
        self.filters_copy = filters_copy

        self.v_lay = UVBoxLayout()
        self.v_lay.setSpacing(15)
        self.setLayout(self.v_lay)

        group = QGroupBox()
        g_lay = UVBoxLayout(group)
        g_lay.setContentsMargins(0, 5, 0, 5)
        g_lay.setSpacing(15)

        descr = QLabel(Lng.filters_descr[Cfg.lng])
        descr.setWordWrap(True)
        g_lay.addWidget(descr)

        self.text_wid = UTextEdit()
        self.text_wid.setFixedHeight(220)
        self.text_wid.setPlaceholderText(Lng.filters[Cfg.lng])
        self.text_wid.setPlainText("\n".join(self.filters_copy))
        self.text_wid.textChanged.connect(self.on_text_changed)
        g_lay.addWidget(self.text_wid)

        self.v_lay.addWidget(group)
                
        self.v_lay.addStretch(1)
        
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
        self.main_folder: MainFolder = None


class WinSettings(SingleActionWindow):
    closed = pyqtSignal()
    reset_data = pyqtSignal(MainFolder)

    def __init__(self, settings_item: SettingsItem):
        super().__init__()
        self.setWindowTitle(Lng.settings[Cfg.lng])
        self.setMinimumHeight(520)
        self.main_folder_list_copy = copy.deepcopy(MainFolder.list_)
        self.json_data_copy = copy.deepcopy(Cfg())
        self.filters_copy = copy.deepcopy(Filters.filters)
        self.need_reset = [False, ]
        self.main_folder_items: list[SettingsListItem] = []
        self.settings_item = settings_item

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.left_menu.clicked.connect(self.left_menu_click)
        self.splitter.addWidget(self.left_menu)

        main_settings_item = SettingsListItem(self.left_menu, text=Lng.general[Cfg.lng])
        self.left_menu.addItem(main_settings_item)
        
        filter_settings = SettingsListItem(self.left_menu, text=Lng.filters[Cfg.lng])
        self.left_menu.addItem(filter_settings)

        item = SettingsListItem(self.left_menu, text=Lng.new_folder[Cfg.lng])
        self.left_menu.addItem(item)
        
        spacer = UListSpacerItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in MainFolder.list_:
            if i.curr_path:
                true_name = os.path.basename(i.curr_path)
            else:
                true_name = os.path.basename(i.paths[0])
            alias = i.name
            text = f"{true_name} ({alias})"
            item = SettingsListItem(self.left_menu, text=text)
            item.main_folder = i
            self.left_menu.addItem(item)
            self.main_folder_items.append(item)

        self.right_wid = QWidget()
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
        self.splitter.setSizes([200, 600])

        mapping = {
            self.settings_item.type_general: 0,
            self.settings_item.type_filters: 1,
            self.settings_item.type_new_folder: 2,
        }

        for key, idx in mapping.items():
            if key == self.settings_item.action_type:
                self.left_menu.setCurrentRow(idx)
                self.init_right_side(idx)
                break
        else:
            for i in self.main_folder_items:
                if i.main_folder == self.settings_item.content:
                    index = self.left_menu.row(i)
                    self.left_menu.setCurrentRow(index)
                    self.init_right_side(index)
                    break

    def init_right_side(self, index: int):
        if index == 0:
            self.gen_settings = GeneralSettings(self.json_data_copy, self.need_reset)
            self.gen_settings.changed.connect(lambda: self.ok_btn.setText(Lng.restart[Cfg.lng]))
            self.right_lay.insertWidget(0, self.gen_settings)
        elif index == 1:
            self.filters_wid = FiltersWid(self.filters_copy)
            self.filters_wid.changed.connect(lambda: self.ok_btn.setText(Lng.restart[Cfg.lng]))
            self.right_lay.insertWidget(0, self.filters_wid)
        elif index == 2:
            self.new_folder = NewFolder(self.main_folder_list_copy)
            self.new_folder.new_folder.connect(self.add_main_folder)
            self.right_lay.insertWidget(0, self.new_folder)
            if self.settings_item.action_type == self.settings_item.type_general:
                self.new_folder.preset_new_folder("")
            else:
                self.new_folder.preset_new_folder(self.settings_item.content)
        else:
            # Находим в копии списка MainFolder объект с нужным псевдонимом,
            # чтобы передать его в дочерний виджет MainFolderSettings.
            # Изменения, внесённые в дочернем виджете, будут напрямую
            # применяться к этому объекту в копии списка.
            item: SettingsListItem = self.left_menu.item(index)
            main_folder = next(
                i
                for i in self.main_folder_list_copy
                if i.name == item.main_folder.name
            )
            main_folder_sett = MainFolderSettings(main_folder)
            main_folder_sett.changed.connect(lambda: self.ok_btn.setText(Lng.restart[Cfg.lng]))
            main_folder_sett.remove.connect(lambda: self.remove_main_folder(item))
            main_folder_sett.reset_data.connect(self.reset_data.emit)
            self.right_lay.insertWidget(0, main_folder_sett)

        self.settings_item.action_type = self.settings_item.type_general

    def add_main_folder(self, main_folder: MainFolder):
        self.main_folder_list_copy.append(main_folder)
        text = f"{os.path.basename(main_folder.curr_path)} ({main_folder.name})"
        item = SettingsListItem(self.left_menu, text=text)
        item.main_folder = main_folder
        self.left_menu.addItem(item)
        self.left_menu.setCurrentItem(item)
        self.clear_right_side()
        index = self.left_menu.count() - 1
        self.init_right_side(index)
        self.ok_btn.setText(Lng.restart[Cfg.lng])

    def remove_main_folder(self, item: SettingsListItem):

        def fin():
            for i in self.main_folder_list_copy:
                if i.name == item.main_folder.name:
                    self.main_folder_list_copy.remove(i)
                    self.left_menu.takeItem(self.left_menu.currentRow())
                    self.left_menu.setCurrentRow(0)
                    self.clear_right_side()
                    self.init_right_side(0)
                    self.ok_btn.setText(Lng.restart[Cfg.lng])
                    break

        try:
            if len(self.main_folder_list_copy) == 1:
                self.win_warn = WinWarn(
                    Lng.attention[Cfg.lng],
                    Lng.at_least_one_folder_required[Cfg.lng],
                )
                self.win_warn.center_to_parent(self)
                self.win_warn.show()
            else:
                self.win_question = WinQuestion(
                    Lng.attention[Cfg.lng],
                    Lng.confirm_delete_folder[Cfg.lng],
                )
                self.win_question.center_to_parent(self)
                self.win_question.ok_clicked.connect(fin)
                self.win_question.ok_clicked.connect(self.win_question.deleteLater)
                self.win_question.show()

        except Exception as e:
            print("win settings > ошибка удаления main folder по кнопке удалить", e)

    def clear_right_side(self):
        wids = (GeneralSettings, MainFolderSettings, NewFolder, FiltersWid)
        right_wid = self.right_wid.findChild(wids)
        right_wid.deleteLater()

    def left_menu_click(self, *args):
        self.clear_right_side()
        index = self.left_menu.currentRow()
        self.init_right_side(index)

    def ok_cmd(self):

        def validate_folders() -> bool:
            """Check that all folders have paths, show warning if not."""
            for folder in self.main_folder_list_copy:
                if not folder.paths:
                    self.win_warn = WinWarn(
                        Lng.attention[Cfg.lng],
                        f"{Lng.select_folder_path[Cfg.lng]} \"{folder.name}\""
                    )
                    self.win_warn.center_to_parent(self.window())
                    self.win_warn.show()
                    return False
            return True

        if self.ok_btn.text() in Lng.restart:
            if not validate_folders():
                return
            if self.need_reset[0]:
                shutil.rmtree(Static.APP_SUPPORT_DIR)
            else:
                MainFolder.list_ = self.main_folder_list_copy
                Filters.filters = self.filters_copy
                for key, value in vars(self.json_data_copy).items():
                    setattr(Cfg, key, value)
                MainFolder.write_json_data()
                Filters.write_json_data()
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
    