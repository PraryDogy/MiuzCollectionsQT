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


class LangReset(QGroupBox):
    reset = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, json_data_copy: JsonData):
        """
        Сигналы:
        - reset_data() сброс всех настроек приложения
        - new_lang(0 или 1): system > lang > _Lang._lang_name. 
        0 это русский язык, 1 это английский
        """
        super().__init__()
        self.json_data = json_data_copy

        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        first_row_lay = UHBoxLayout()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.lang_btn = QPushButton(text=Lang._lang_name)
        self.lang_btn.setFixedWidth(115)
        self.lang_btn.clicked.connect(self.lang_btn_cmd)
        first_row_lay.addWidget(self.lang_btn)

        self.lang_label = QLabel(Lang.lang_label)
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sec_row_wid.setLayout(sec_row_lay)

        self.reset_data_btn = QPushButton(Lang.reset)
        self.reset_data_btn.setFixedWidth(115)
        self.reset_data_btn.clicked.connect(self.changed.emit)
        self.reset_data_btn.clicked.connect(self.reset.emit)
        sec_row_lay.addWidget(self.reset_data_btn)

        descr = QLabel(text=Lang.restore_db_descr)
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def lang_btn_cmd(self, *args):
        if self.lang_btn.text() == "Русский":
            self.lang_btn.setText("English")
            self.json_data.lang_ind = 1
        else:
            self.lang_btn.setText("Русский")
            self.json_data.lang_ind = 0
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

        self.show_files_btn = QPushButton(text=Lang.show_app_support)
        self.show_files_btn.setFixedWidth(115)
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        first_row_lay.addWidget(self.show_files_btn)

        self.lang_label = QLabel(Lang.show_files)
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        v_lay.addWidget(sec_row_wid)
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_wid.setLayout(sec_row_lay)

        self.help_btn = QPushButton(text=Lang.win_manual)
        self.help_btn.setFixedWidth(115)
        self.help_btn.clicked.connect(self.show_help)
        sec_row_lay.addWidget(self.help_btn)

        self.lang_label = QLabel(Lang.win_manual_descr)
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
        self.spin.setSuffix(f" {Lang.mins}")
        self.spin.setValue(self.json_data_copy.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        self.spin_lay.addWidget(self.spin)

        label = QLabel(Lang.scan_every, self)
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

        self.checkbox_lbl = QLabel(Lang.new_scaner)
        first_lay.addWidget(self.checkbox_lbl)

        if self.json_data_copy.new_scaner:
            self.checkbox.setText(Lang.disable)
        else:
            self.checkbox.setText(Lang.enable)

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
            self.checkbox.setText(Lang.enable)
        else:
            self.json_data_copy.new_scaner = True
            self.checkbox.setText(Lang.disable)
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
            Lang.theme_auto
        )
        self.dark_theme = ThemesBtn(
            os.path.join(Static.INNER_IMAGES,"dark_theme.svg"),
            Lang.theme_dark
        )
        self.light_theme = ThemesBtn(
            os.path.join(Static.INNER_IMAGES,"light_theme.svg"),
            Lang.theme_light
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
    def __init__(self, parent):
        super().__init__(parent)

        txt = "\n".join([
            f"Version {Static.APP_VER}",
            "Developed by Evlosh",
            "email: evlosh@gmail.com",
            "telegram: evlosh",
            ])
        
        self.setText(txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = UMenu(ev)

        copy_text = QAction(parent=context_menu, text=Lang.copy)
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lang.copy_all)
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


class WinSettings(WinSystem):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.main_folder_list = copy.deepcopy(MainFolder.list_)
        self.json_data_copy = copy.deepcopy(JsonData())

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.left_menu.mouseReleaseEvent = self.item_clicked
        self.splitter.addWidget(self.left_menu)

        main_settings_item = UListWidgetItem(self.left_menu, text=Lang.main)
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

        self.ok_btn = QPushButton(Lang.ok)
        self.ok_btn.setFixedWidth(90)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = QPushButton(Lang.cancel)
        cancel_btn.setFixedWidth(90)
        btns_lay.addWidget(cancel_btn)


        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([Static.MENU_LEFT_WIDTH, 600])

        self.item_clicked()

    def item_clicked(self, *args):
        for i in self.right_wid.findChildren((MainSettings, )):
            i.deleteLater()
        if self.left_menu.currentRow() == 0:
            self.main_settings = MainSettings(self.json_data_copy)
            self.main_settings.changed.connect(lambda: self.ok_btn.setText(Lang.restart_app))
            self.right_lay.insertWidget(0, self.main_settings)
        else:
            main_folder_name = self.left_menu.currentItem().text()
            print(main_folder_name)
    
    def deleteLater(self):
        # new_data = vars(self.json_data_copy)
        # if new_data:
        #     for k, v in new_data.items():
        #         setattr(JsonData, k, v)
        return super().deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)