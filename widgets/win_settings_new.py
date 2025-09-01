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

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.paletes import ThemeChanger
from system.utils import MainUtils

from ._base_widgets import (UHBoxLayout, ULineEdit, UListWidgetItem, UMenu,
                            UTextEdit, UVBoxLayout, VListWidget, WinChild,
                            WinSystem)
from .win_help import WinHelp

# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ 


class LangReset(QGroupBox):
    reset = pyqtSignal()
    changed = pyqtSignal()
    lang = (
        ("Русский", "English"),
        ("Язык", "Language"),
        ("Сбросить", "Reset"),
        ("Сбросить настройки", "Reset settings"),
    )

    def __init__(self, json_data_copy: JsonData):
        super().__init__()
        self.json_data = json_data_copy

        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        first_row_lay = UHBoxLayout()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.lang_btn = QPushButton(text=self.lang[0][JsonData.lang])
        self.lang_btn.setFixedWidth(115)
        self.lang_btn.clicked.connect(self.lang_btn_cmd)
        first_row_lay.addWidget(self.lang_btn)

        self.lang_label = QLabel(self.lang[1][JsonData.lang])
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sec_row_wid.setLayout(sec_row_lay)

        self.reset_data_btn = QPushButton(self.lang[2][JsonData.lang])
        self.reset_data_btn.setFixedWidth(115)
        self.reset_data_btn.clicked.connect(self.changed.emit)
        self.reset_data_btn.clicked.connect(self.reset.emit)
        sec_row_lay.addWidget(self.reset_data_btn)

        descr = QLabel(text=self.lang[1][JsonData.lang])
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def lang_btn_cmd(self, *args):
        if self.lang_btn.text() == self.lang[0][0]: 
            self.lang_btn.setText(self.lang[0][1])
            self.json_data.lang = 1
        else:
            self.lang_btn.setText(self.lang[0][0])
            self.json_data.lang = 0
        self.changed.emit()


class SimpleSettings(QGroupBox):
    lang = (
        ("Показать", "Show"),
        ("Показать системные файлы в Finder", "Show system files in Finder"),
        ("Помощь", "Help"),
        ("Показать окно справки", "Show help window"),
    )

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

        self.show_files_btn = QPushButton(text=self.lang[0][JsonData.lang])
        self.show_files_btn.setFixedWidth(115)
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        first_row_lay.addWidget(self.show_files_btn)

        self.lang_label = QLabel(self.lang[1][JsonData.lang])
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        v_lay.addWidget(sec_row_wid)
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_wid.setLayout(sec_row_lay)

        self.help_btn = QPushButton(text=self.lang[2][JsonData.lang])
        self.help_btn.setFixedWidth(115)
        self.help_btn.clicked.connect(self.show_help)
        sec_row_lay.addWidget(self.help_btn)

        self.lang_label = QLabel(self.lang[3][JsonData.lang])
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
    lang = (
        ("минут", "minutes"),
        ("Интервал поиска новых изображений", "Interval for checking new images"),
        ("Быстрый поиск изображений (бета)", "Fast image search (beta)"),
        ("Выключить", "Disable"),
        ("Включить", "Enable"),
    )

    def __init__(self, json_data_copy: JsonData):
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
        self.spin.setSuffix(f" {self.lang[0][JsonData.lang]}")
        self.spin.setValue(self.json_data_copy.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        self.spin_lay.addWidget(self.spin)

        label = QLabel(self.lang[1][JsonData.lang], self)
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

        self.checkbox_lbl = QLabel(self.lang[2][JsonData.lang])
        first_lay.addWidget(self.checkbox_lbl)

        if self.json_data_copy.new_scaner:
            self.checkbox.setText(self.lang[3][JsonData.lang])
        else:
            self.checkbox.setText(self.lang[4][JsonData.lang])

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
            self.checkbox.setText(self.lang[4][JsonData.lang])
        else:
            self.json_data_copy.new_scaner = True
            self.checkbox.setText(self.lang[3][JsonData.lang])
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
    lang = (
        ("Авто", "Auto"),
        ("Темная", "Dark"),
        ("Светлая", "Light"),
    )

    def __init__(self):
        super().__init__()
        h_lay = UHBoxLayout()
        h_lay.setContentsMargins(10, 10, 10, 10)
        h_lay.setSpacing(20)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(h_lay)

        self.frames = []

        self.system_theme = ThemesBtn(
            os.path.join(Static.INNER_IMAGES, "system_theme.svg"),
            self.lang[0][JsonData.lang]
        )
        self.dark_theme = ThemesBtn(
            os.path.join(Static.INNER_IMAGES,"dark_theme.svg"),
            self.lang[1][JsonData.lang]
        )
        self.light_theme = ThemesBtn(
            os.path.join(Static.INNER_IMAGES,"light_theme.svg"),
            self.lang[2][JsonData.lang]
        )

        for f in (self.system_theme, self.dark_theme, self.light_theme):
            h_lay.addWidget(f)
            self.frames.append(f)
            f.clicked.connect(self.on_frame_clicked)

        if JsonData.dark_mode == 0:
            self.set_selected(self.system_theme)
        elif JsonData.dark_mode == 1:
            self.set_selected(self.dark_theme)
        elif JsonData.dark_mode == 2:
            self.set_selected(self.light_theme)

    def on_frame_clicked(self):
        sender: ThemesBtn = self.sender()
        self.set_selected(sender)

        if sender == self.system_theme:
            JsonData.dark_mode = 0
        elif sender == self.dark_theme:
            JsonData.dark_mode = 1
        elif sender == self.light_theme:
            JsonData.dark_mode = 2

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
    lang = (
        ("Копировать", "Copy"),
        ("Копировать все", "Copy all"),
    )

    def __init__(self, parent):
        super().__init__(parent)
        self.setText(self.txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = UMenu(ev)

        copy_text = QAction(parent=context_menu, text=self.lang[0][JsonData.lang])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=self.lang[1][JsonData.lang])
        select_all.triggered.connect(lambda: MainUtils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_()
        return super().contextMenuEvent(ev)

    def copy_text_md(self):
        MainUtils.copy_text(self.selectedText())


class AboutWid(QGroupBox):
    icon_svg = os.path.join(Static.INNER_IMAGES, "icon.svg")

    def __init__(self):
        super().__init__()
        h_lay = UHBoxLayout()
        self.setLayout(h_lay)

        icon = QSvgWidget(self.icon_svg)
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(85, 85)
        h_lay.addWidget(icon)

        h_lay.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        h_lay.addWidget(lbl)


class MainSettings(QWidget):
    reset = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, json_data_copy: JsonData):
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
        ]

    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
    

class MainFolderPaths(DropableGroupBox):
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.text_changed.connect(self.set_data)

    def set_data(self, *args):
        self.main_folder.paths = self.get_data()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                i.toLocalFile()
                for i in a0.mimeData().urls()
                if os.path.isdir(i.toLocalFile())
            ]
            text = "\n".join((self.text_edit.toPlainText(), *urls))
            self.text_edit.setPlainText(text)
        return super().dropEvent(a0)


class StopList(DropableGroupBox):
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.text_changed.connect(self.set_data)

    def set_data(self, *args):
        self.main_folder.stop_list = self.get_data()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                os.path.basename(i.toLocalFile().rstrip(os.sep))
                for i in a0.mimeData().urls()
                if os.path.isdir(i.toLocalFile())
            ]
            text = "\n".join((self.text_edit.toPlainText(), *urls))
            self.text_edit.setPlainText(text)
        return super().dropEvent(a0)


class MainFolderSettings(QWidget):
    remove = pyqtSignal()
    changed = pyqtSignal()
    lang = (
        ("Имя папки", "Folder name"),
        (
            "Путь к папке с коллекциями: перетащите сюда папку или укажите\n"
            "путь с новой строки.",
            "Path to the collections folder: drag a folder here or enter a path\n"
            "on a new line."
        ),
        (
            "Игнор лист: перетащите сюда папку или укажите имя с новой\n"
            "строки.",
            "Ignore list: drag a folder here or enter a name on a new line."
        ),
        ("Удалить", "Delete"),
    )

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
        name_descr = QLabel(self.lang[0][JsonData.lang] + ":")
        first_lay.addWidget(name_descr)
        name_label = QLabel(main_folder.name)
        first_lay.addWidget(name_label)

        sec_row = MainFolderPaths(main_folder)
        sec_row.text_changed.connect(self.changed.emit)
        v_lay.addWidget(sec_row)
        sec_row.top_label.setText(self.lang[1][JsonData.lang])
        text_ = "\n".join(i for i in main_folder.paths)
        sec_row.text_edit.setPlainText(text_)

        third_row = StopList(main_folder)
        third_row.text_changed.connect(self.changed.emit)
        v_lay.addWidget(third_row)
        third_row.top_label.setText(self.lang[2][JsonData.lang])
        text_ = "\n".join(i for i in main_folder.stop_list)
        third_row.text_edit.setPlainText(text_)

        remove_btn = QPushButton(self.lang[3][JsonData.lang])
        remove_btn.clicked.connect(self.remove.emit)
        remove_btn.setFixedWidth(100)

        btn_lay = UHBoxLayout()
        btn_lay.addStretch()
        btn_lay.addWidget(remove_btn)
        btn_lay.addStretch()
        v_lay.addLayout(btn_lay)

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class WinSettings(WinSystem):
    lang = (
        ("Настройки", "Settings"),
        ("Основные", "General"),
        ("Ок", "Ok"),
        ("Отмена", "Cancel"),
        ("Перезапуск", "Restart"),
    )
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle(self.lang[0][JsonData.lang])
        self.main_folder_list = copy.deepcopy(MainFolder.list_)
        self.json_data_copy = copy.deepcopy(JsonData())
        self.need_reset = False

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.left_menu.mouseReleaseEvent = self.init_right_side
        self.splitter.addWidget(self.left_menu)

        main_settings_item = UListWidgetItem(self.left_menu, text=self.lang[1][JsonData.lang])
        self.left_menu.addItem(main_settings_item)

        for i in MainFolder.list_:
            item = UListWidgetItem(self.left_menu, text=i.name)
            self.left_menu.addItem(item)

        self.left_menu.setCurrentRow(0)

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

        self.ok_btn = QPushButton(self.lang[2][JsonData.lang])
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(100)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = QPushButton(self.lang[3][JsonData.lang])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(100)
        btns_lay.addWidget(cancel_btn)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([Static.MENU_LEFT_WIDTH, 600])

        self.init_right_side()

    def init_right_side(self, *args):
        self.clear_right_side()

        if self.left_menu.currentRow() == 0:
            self.main_settings = MainSettings(self.json_data_copy)
            self.main_settings.reset.connect(lambda: setattr(self, "need_reset", True))
            self.main_settings.changed.connect(lambda: self.ok_btn.setText(self.lang[4][JsonData.lang]))
            self.right_lay.insertWidget(0, self.main_settings)
        else:
            main_folder = next(
                (x
                 for x in self.main_folder_list
                 if x.name == self.left_menu.currentItem().text()
                )
            )
            if main_folder:
                item = self.left_menu.currentItem()
                main_folder_sett = MainFolderSettings(main_folder)
                main_folder_sett.changed.connect(lambda: self.ok_btn.setText(self.lang[4][JsonData.lang]))
                main_folder_sett.remove.connect(lambda: self.remove_main_folder(main_folder, item))
                self.right_lay.insertWidget(0, main_folder_sett)

    def remove_main_folder(self, main_folder: MainFolder, item: UListWidgetItem):
        try:
            self.main_folder_list.remove(main_folder)
            self.left_menu.takeItem(self.left_menu.currentRow())
            self.left_menu.setCurrentRow(0)
            self.clear_right_side()
            self.init_right_side()
            self.ok_btn.setText(self.lang[4][JsonData.lang])
        except Exception:
            print("win settings > ошибка удаления main folder по кнопке удалить")

    def clear_right_side(self):
        for i in self.right_wid.findChildren((MainSettings, MainFolderSettings)):
            i.deleteLater()

    def ok_cmd(self):
        new_json_data = vars(self.json_data_copy)

        for i in self.main_folder_list:
            print(i.name)
            # print(i.paths)
            print(i.stop_list)
            print()


        # if self.need_reset:
        #     shutil.rmtree(Static.APP_SUPPORT_DIR)
        #     QApplication.quit()
        #     MainUtils.start_new_app()

        # else:
        #     for k, v in new_json_data.items():
        #         setattr(JsonData, k, v)
        #     MainFolder.write_json_data()
        #     JsonData.write_json_data()
        #     QApplication.quit()
        #     MainUtils.start_new_app()



    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)