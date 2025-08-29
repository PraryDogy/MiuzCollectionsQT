import subprocess
from copy import deepcopy

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QGroupBox, QLabel, QPushButton, QSpinBox,
                             QSplitter, QWidget)

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder

from ._base_widgets import (UHBoxLayout, UListWidgetItem, UVBoxLayout,
                            VListWidget, WinChild)
from .win_help import WinHelp


class LangReset(QGroupBox):
    changed = pyqtSignal()
    reset = pyqtSignal()

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
            self.changed.emit()
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

        self.change_theme()

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

    def change_theme(self):
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


class MainSettings(QWidget):
    changed = pyqtSignal()
    reset = pyqtSignal()

    def __init__(self, json_data_copy: JsonData):
        super().__init__()
        self.v_lay = UVBoxLayout()
        self.v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_lay.setSpacing(10)
        self.setLayout(self.v_lay)

        lang_reset = LangReset(json_data_copy)
        lang_reset.changed.connect(self.changed.emit)
        lang_reset.reset.connect(self.reset.emit)
        self.v_lay.addWidget(lang_reset)

        simple_settings = SimpleSettings()
        self.v_lay.addWidget(simple_settings)

        scaner_settings = ScanerSettings(json_data_copy)
        scaner_settings.changed.connect(self.changed.emit)
        self.v_lay.addWidget(scaner_settings)


class WinSettings(WinChild):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.main_folder_list = deepcopy(MainFolder.list_)
        self.json_data_copy = deepcopy(JsonData())
        self.changed = False

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

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([Static.MENU_LEFT_WIDTH, 600])

        self.item_clicked()

    def item_clicked(self, *args):
        for i in self.right_wid.findChildren(QWidget):
            i.deleteLater()
        if self.left_menu.currentRow() == 0:
            self.main_settings = MainSettings(self.json_data_copy)
            self.main_settings.changed.connect(self.changed_cmd)
            self.right_lay.addWidget(self.main_settings)
        else:
            main_folder_name = self.left_menu.currentItem().text()
            print(main_folder_name)
    
    def changed_cmd(self):
        self.changed = True

    def deleteLater(self):
        for k, v in self.json_data_copy.__dict__.items():
            setattr(JsonData, k, v)
        return super().deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)