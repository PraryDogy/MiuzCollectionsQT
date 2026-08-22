import os
import shutil
import subprocess
import sys

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QContextMenuEvent, QIcon, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QGraphicsOpacityEffect, QHBoxLayout,
                             QLabel, QLineEdit, QSpacerItem, QSplitter,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QWidget)
from typing_extensions import Literal

from cfg import JsonData, Static, Themes
from system.filters import Filters
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import MfRemover, ProcessWorker
from system.paletes import ThemeChanger
from system.shared_utils import SharedUtils
from system.tasks import (HashDirSize, HashDirSizeItem, MfDataCleaner,
                          UThreadPool)
from system.utils import Utils

from ._base_widgets import (ConfirmWindow, HSep, MfAliasWidget, MfPathWidget,
                            MfStopListWidget, RowArrowWidget,
                            SaveRowArrowWidget, SuperConfirmWindow, UGroupBox,
                            UMainWidget, UMenu, UPushButton, USpinBox,
                            UTextEditDark, VListSpacerItem, VListWidget,
                            VListWidgetItem, WarningWindow)


def restart_app():
    ProcessWorker.stop_all() 
    os.execl(sys.executable, sys.executable, *sys.argv)
    QApplication.exit(0)


class LabelMinWidth(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(30)


class RebootableSettings(UGroupBox):
    changed = pyqtSignal()
    lang_changed = pyqtSignal()
    spin_max = 60
    spin_min = 0
    rus_flag = Static.COMMON_ICONS / "rus_flag.svg"
    eng_flag = Static.COMMON_ICONS / "eng_flag.svg"
    eraser_svg = Static.COMMON_ICONS / "eraser.svg"
    clock_svg = Static.COMMON_ICONS / "clock.svg"
    language_svg = Static.COMMON_ICONS / "language.svg"

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*RowArrowWidget.group_margings)
        main_layout.setSpacing(RowArrowWidget.group_spacing)

        self.scaner_minutes = JsonData.scaner_minutes
        self.lng_index = JsonData.lng_index
        self.lng_icons = (
            QIcon(self.rus_flag),
            QIcon(self.eng_flag)
        )

        lng_menu = UMenu(None)
        for value in (0, 1):
            action = QAction(Lng.russian[value], lng_menu)
            action.setIcon(self.lng_icons[value])
            action.setIconVisibleInMenu(True)
            action.triggered.connect(lambda e, v=value: self.change_language(v))
            lng_menu.addAction(action)

        lng_wid = RowArrowWidget(Lng.language_max[JsonData.lng_index])
        lng_wid.set_left_icon(self.language_svg)
        main_layout.addWidget(lng_wid)
        self.lng_btn = UPushButton(text=Lng.russian[JsonData.lng_index])
        self.lng_btn.setIcon(self.lng_icons[JsonData.lng_index])
        self.lng_btn.setFixedWidth(100)
        self.lng_btn.setMenu(lng_menu)
        lng_wid.replace_arrow_widget(self.lng_btn)
        # чтобы кнопка меню не теряла стиль
        lng_wid.setFixedHeight(RowArrowWidget.hh + 6)

        main_layout.addWidget(HSep())

        scaner_time_wid = RowArrowWidget(Lng.search_interval[JsonData.lng_index])
        scaner_time_wid.set_left_icon(self.clock_svg)
        # регулировка высоты ради кастомного спинбокса
        scaner_time_wid.setFixedHeight(scaner_time_wid.height() + 1)
        main_layout.addWidget(scaner_time_wid)
        self.spin = USpinBox(self)
        self.spin.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.spin.setMinimum(self.spin_min)
        self.spin.setMaximum(self.spin_max)
        self.spin.findChild(QLineEdit).setTextMargins(3, 0, 3, 0)
        self.spin.setSuffix(f" {Lng.minutes[JsonData.lng_index]}")
        self.spin.setValue(JsonData.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        scaner_time_wid.replace_arrow_widget(self.spin)

        main_layout.addWidget(HSep())

        reset_data_wid = RowArrowWidget(Lng.erase_data[JsonData.lng_index])
        reset_data_wid.set_left_icon(self.eraser_svg)
        reset_data_wid.clicked.connect(self.erase_all_data)
        main_layout.addWidget(reset_data_wid)

    def change_language(self, value: int):
        self.lng_btn.setText(Lng.russian[value])
        self.lng_btn.setIcon(self.lng_icons[value])
        self.lng_index = value
        self.changed.emit()
        self.lang_changed.emit()

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
        self.scaner_minutes = value
        self.changed.emit()

    def erase_all_data(self, *args):

        def fin():
            self.hide()
            shutil.rmtree(Static.APP_DATA_DIR, ignore_errors=True)
            restart_app()

        reset_win = ConfirmWindow(Lng.erase_data_long[JsonData.lng_index], 320, 110)
        reset_win.center_to_parent(self.window())
        reset_win.ok_clicked.connect(fin)
        reset_win.show()


class SizesWin(UMainWidget):
    ww = 500
    hh = 330

    def __init__(self, size_items: list[HashDirSizeItem], parent=None):
        super().__init__(parent)
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.data_size[JsonData.lng_index])
        self.resize(self.ww, self.hh)
        self.central_layout.setSpacing(10)

        total_size = SharedUtils.get_f_size(sum(
            item.size for item in size_items
        ))
        first_row = QLabel(f"{Lng.data_size[JsonData.lng_index]}: {total_size}")
        self.central_layout.addWidget(first_row)

        total = sum(item.total_images for item in size_items)
        sec_row = QLabel(f"{Lng.images[JsonData.lng_index]}: {total}")
        self.central_layout.addWidget(sec_row)

        headers = [
            Lng.folder[JsonData.lng_index],
            Lng.file_size[JsonData.lng_index],
            Lng.images[JsonData.lng_index]
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


class NonRebootableSettings(UGroupBox):
    finder_svg = Static.COMMON_ICONS / "finder.svg"
    hdd_svg = Static.COMMON_ICONS / "hdd.svg"

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*RowArrowWidget.group_margings)
        main_layout.setSpacing(RowArrowWidget.group_spacing)

        self.size_items = {}

        data_size_wid = RowArrowWidget(Lng.statistic[JsonData.lng_index])
        data_size_wid.set_left_icon(self.hdd_svg)
        data_size_wid.clicked.connect(self.show_sizes_win)
        main_layout.addWidget(data_size_wid)

        main_layout.addWidget(HSep())

        show_files_wid = RowArrowWidget(Lng.show_system_files[JsonData.lng_index])
        show_files_wid.set_left_icon(self.finder_svg)
        show_files_wid.clicked.connect(self.show_files_cmd)
        main_layout.addWidget(show_files_wid)

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
            subprocess.Popen(["open", Static.APP_DATA_DIR])
        except Exception as e:
            print(e)


class ThemeBtn(QWidget):
    clicked = pyqtSignal(str)
    ww = 70

    def __init__(self, theme: Literal["light", "dark"]):
        super().__init__()
        self.theme = theme
        self.svg = os.path.join(
            Static.COMMON_ICONS,
            f"{theme}_theme.svg"
        )
        self.svg_selected = os.path.join(
            Static.COMMON_ICONS,
            f"{theme}_theme_selected.svg"
        )
        text_mappings = {
            Themes.dark: Lng.dark_theme,
            Themes.light: Lng.light_theme,
        }

        self.setFixedWidth(self.ww)

        layout_ = QVBoxLayout(self)
        layout_.setContentsMargins(0, 0, 0, 0)
        layout_.setSpacing(5)
        
        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(40, 40)
        layout_.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        label = QLabel(text_mappings[theme][JsonData.lng_index])
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


class ThemesWidget(UGroupBox):
    theme_svg = Static.COMMON_ICONS / "theme.svg"

    def __init__(self):
        super().__init__()
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(*RowArrowWidget.group_margings)
        main_lay.setSpacing(RowArrowWidget.group_spacing)

        title_wid = RowArrowWidget(Lng.theme[JsonData.lng_index])
        title_wid.set_left_icon(self.theme_svg)
        title_wid.hide_arrow()
        main_lay.addWidget(title_wid)

        main_lay.addWidget(HSep())
        main_lay.addSpacing(5)

        themes_wid = QWidget()
        themes_layout = QHBoxLayout(themes_wid)
        themes_layout.setContentsMargins(0, 0, 0, 0)
        themes_layout.setSpacing(5)
        themes_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_lay.addWidget(themes_wid)
        
        for i in (Themes.dark, Themes.light):
            btn = ThemeBtn(i)
            btn.clicked.connect(lambda theme, btn=btn: self.on_btn_clicked(theme, btn))
            themes_layout.addWidget(btn)
            if i == JsonData.theme:
                btn.select()

    def on_btn_clicked(self, theme: Literal["light", "dark"], btn: ThemeBtn):
        theme_btns = self.findChildren(ThemeBtn)
        if theme != JsonData.theme:
            for i in theme_btns:
                i.clear_selection()
            btn.select()
            JsonData.theme = theme
            ThemeChanger.init()


class AboutWidLabel(LabelMinWidth):
    txt = "\n".join([
        f"Version {Static.APP_VERSION}",
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

        copy_text = QAction(parent=context_menu, text=Lng.copy[JsonData.lng_index])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lng.copy_all[JsonData.lng_index])
        select_all.triggered.connect(lambda: Utils.pyqt_copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_menu()
        # return super().contextMenuEvent(ev)

    def copy_text_md(self):
        Utils.pyqt_copy_text(self.selectedText())


class AboutWid(UGroupBox):
    icon_path = Static.APP_ICONS / "icon.png"
    icon_size = 85
    opacity = 0.85

    def __init__(self):
        super().__init__()
        h_lay = QHBoxLayout(self)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(0)

        icon = QLabel()
        pixmap = QPixmap(self.icon_path)
        pixmap = Utils.pyqt_qiconed_resize(pixmap, self.icon_size)
        icon.setPixmap(pixmap)
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(self.opacity) 
        icon.setGraphicsEffect(opacity_effect)
        h_lay.addWidget(icon)

        h_lay.addSpacerItem(QSpacerItem(0, 20))

        lbl = AboutWidLabel(self)
        h_lay.addWidget(lbl)

        h_lay.addStretch()

        if not self.icon_path.exists():
            print("win settings about wid, icon.png not exists")


class GeneralSettings(QWidget):
    lang_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        v_lay = QVBoxLayout(self)
        v_lay.setSpacing(10)
        v_lay.setContentsMargins(0, 0, 0, 0)

        self.rebootable_settings = RebootableSettings()
        self.rebootable_settings.changed.connect(
            lambda: self.save_wid.show_warning()
        )
        self.rebootable_settings.lang_changed.connect(
            lambda: self.lang_changed.emit()
        )
        v_lay.addWidget(self.rebootable_settings)

        non_rebootable_settings = NonRebootableSettings()
        v_lay.addWidget(non_rebootable_settings)

        themes = ThemesWidget()
        v_lay.addWidget(themes)

        about = AboutWid()
        v_lay.addWidget(about)

        save_container = UGroupBox()
        v_lay.addWidget(save_container)
        save_container_lay = QVBoxLayout(save_container)
        save_container_lay.setContentsMargins(*RowArrowWidget.group_margings)
        save_container_lay.setSpacing(RowArrowWidget.group_spacing)

        self.save_wid = SaveRowArrowWidget(JsonData.lng_index)
        self.save_wid.clicked.connect(
            lambda: self.save_settings_cmd()
        )
        save_container_lay.addWidget(self.save_wid)

        v_lay.addStretch()

    def save_settings_cmd(self):

        def fin():
            JsonData.scaner_minutes = self.rebootable_settings.scaner_minutes
            JsonData.lng_index = self.rebootable_settings.lng_index
            JsonData.write_json_data()
            restart_app()

        win = ConfirmWindow(
            Lng.app_will_restarted[JsonData.lng_index], 300, 90
        )
        win.ok_clicked.connect(fin)
        win.center_to_parent(self.window())
        win.show()


class FiltersWid(QWidget):
    changed = pyqtSignal()
    reset_svg = Static.COMMON_ICONS / "reset.svg"

    def __init__(self):
        super().__init__()
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(10)

        first_container = UGroupBox()
        main_lay.addWidget(first_container)
        first_container_layout = QVBoxLayout(first_container)
        first_container_layout.setContentsMargins(5, 2, 5, 2)
        first_container_layout.setSpacing(10)
        
        filters_text = LabelMinWidth(Lng.filters_descr[JsonData.lng_index])
        filters_text.setWordWrap(True)
        first_container_layout.addWidget(filters_text)

        self.filters_edit = UTextEditDark()
        self.filters_edit.setFixedHeight(220)
        self.filters_edit.setPlaceholderText(Lng.filters[JsonData.lng_index])
        self.filters_edit.setPlainText("\n".join(Filters.items))
        self.filters_edit.textChanged.connect(
            lambda: self.save_wid.show_warning()
        )
        first_container_layout.addWidget(self.filters_edit)

        second_container = UGroupBox()
        main_lay.addWidget(second_container)
        second_container_layout = QVBoxLayout(second_container)
        second_container_layout.setContentsMargins(*RowArrowWidget.group_margings)
        second_container_layout.setSpacing(RowArrowWidget.group_spacing)

        erase_filters_wid = RowArrowWidget(Lng.reset_filters[JsonData.lng_index])
        erase_filters_wid.set_left_icon(self.reset_svg)
        erase_filters_wid.clicked.connect(self.reset_filters_cmd)
        second_container_layout.addWidget(erase_filters_wid)

        second_container_layout.addWidget(HSep())

        self.save_wid = SaveRowArrowWidget(JsonData.lng_index)
        self.save_wid.clicked.connect(lambda: self.save_filters_cmd())
        second_container_layout.addWidget(self.save_wid)

        main_lay.addStretch()
        
    def reset_filters_cmd(self):

        def fin():
            Filters.items = Static.DEFAULT_FILTERS
            Filters.write_json_data()
            restart_app()

        self.filters_win = ConfirmWindow(
            Lng.reset_filters_long[JsonData.lng_index], 290, 90
        )
        self.filters_win.ok_clicked.connect(fin)
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def save_filters_cmd(self):

        def fin():
            Filters.items = [
                line.strip() 
                for line in self.filters_edit.toPlainText().split("\n") 
                if line.strip()
            ]
            Filters.write_json_data()
            restart_app()

        win = ConfirmWindow(
            Lng.app_will_restarted[JsonData.lng_index], 300, 90
        )
        win.ok_clicked.connect(fin)
        win.center_to_parent(self.window())
        win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


class MfSettings(QWidget):
    repair_svg = Static.COMMON_ICONS / "repair.svg"
    trash_svg = Static.COMMON_ICONS / "trash.svg"

    def __init__(self, mf_index: int):
        super().__init__()

        #  Получаем объект Mf по индексу
        self.mf = Mf.items[mf_index]

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(10)

        # Верхний ряд с названием
        name_group = UGroupBox()
        main_lay.addWidget(name_group)
        name_group_lay = QVBoxLayout(name_group)
        name_group_lay.setContentsMargins(*RowArrowWidget.group_margings)
        name_group_lay.setSpacing(RowArrowWidget.group_spacing)

        self.name_wid = RowArrowWidget(
            text=f"{Lng.alias[JsonData.lng_index]}: {self.mf.mf_alias}"
        )
        self.name_wid.hide_arrow()
        name_group_lay.addWidget(self.name_wid)

        self.path_widget = MfPathWidget(
            lng_index=JsonData.lng_index,
            mf_path=self.mf.mf_current_path
        )
        self.path_widget.changed.connect(
            lambda: self.mf_save_widget.show_warning()
        )
        main_lay.addWidget(self.path_widget)

        self.mf_stop_list = MfStopListWidget(
            lng_index=JsonData.lng_index,
            mf_stop_list=self.mf.mf_stop_list
        )
        self.mf_stop_list.text_edit.textChanged.connect(
            lambda: self.mf_save_widget.show_warning()
        )
        main_lay.addWidget(self.mf_stop_list)

        general_wid = UGroupBox()
        main_lay.addWidget(general_wid)
        general_wid_lay = QVBoxLayout(general_wid)
        general_wid_lay.setContentsMargins(*RowArrowWidget.group_margings)
        general_wid_lay.setSpacing(RowArrowWidget.group_spacing)

        repair_widget = RowArrowWidget(Lng.repair_mf[JsonData.lng_index])
        repair_widget.set_left_icon(self.repair_svg)
        repair_widget.clicked.connect(self.repair_mf)
        general_wid_lay.addWidget(repair_widget)

        general_wid_lay.addWidget(HSep())

        remove_wid = RowArrowWidget(Lng.remove_folder[JsonData.lng_index])
        remove_wid.set_left_icon(self.trash_svg)
        remove_wid.clicked.connect(self.remove_mf)
        general_wid_lay.addWidget(remove_wid)

        general_wid_lay.addWidget(HSep())

        self.mf_save_widget = SaveRowArrowWidget(JsonData.lng_index)
        self.mf_save_widget.clicked.connect(self.save_mf_settings)
        general_wid_lay.addWidget(self.mf_save_widget)

        main_lay.addStretch()

    def remove_mf(self, *args):
        
        def poll_task():
            if not self.mf_remover.is_alive():
                for i in Mf.items:
                    if i.mf_alias == self.mf.mf_alias:
                        Mf.items.remove(i)
                        break
                if self.mf.mf_alias in JsonData.hide_digits_mf_lst:
                    JsonData.hide_digits_mf_lst.remove(self.mf.mf_alias)
                    JsonData.write_json_data()
                Mf.write_json_data()
                restart_app()
            else:
                QTimer.singleShot(1000, poll_task)

        def start_mf_remover():
            for i in UMainWidget.win_list:
                i.hide()
            self.mf_remover.start()
            QTimer.singleShot(1000, poll_task)

        self.mf_remover = ProcessWorker(
            target=MfRemover.start,
            args=(self.mf.mf_alias, )
        )

        if len(Mf.items) == 1:
            win = WarningWindow(
                Lng.at_least_one_folder_required[JsonData.lng_index],
                280, 90
            )
            win.ok_clicked.connect(win.deleteLater)
        else:
            win = ConfirmWindow(
                Lng.app_will_restarted[JsonData.lng_index], 300, 90
            )
            win.ok_clicked.connect(start_mf_remover)
        win.center_to_parent(self.window())
        win.show()

    def repair_mf(self, *args):
        def reset_data():
            self.reset_task = MfDataCleaner(self.mf.mf_alias)
            self.reset_task.sigs.finished_.connect(restart_app)
            UThreadPool.start(self.reset_task)

        win = ConfirmWindow(
            Lng.app_will_restarted[JsonData.lng_index], 300, 90
        )
        win.ok_clicked.connect(reset_data)
        win.center_to_parent(self.window())
        win.show()

    def save_mf_settings(self):

        def final():
            current_mf = None
            for i in Mf.items:
                if i.mf_alias == self.mf.mf_alias:
                    current_mf = i
                    break
            mf_stop_list = self.mf_stop_list.text_edit.toPlainText().split("\n")
            current_mf.mf_paths = [self.path_widget.mf_path, ]
            current_mf.mf_current_path = self.path_widget.mf_path
            current_mf.mf_stop_list = mf_stop_list
            Mf.write_json_data()
            restart_app()

        mf_path = self.path_widget.validate()
        if mf_path:
            super_win = SuperConfirmWindow(
                Lng.confirm_mf_path[JsonData.lng_index],
                310, 105
            )
            super_win.center_to_parent(self.window())
            super_win.ok_clicked.connect(final)
            super_win.show()
        else:
            win_warn = WarningWindow(
                Lng.select_folder_path[JsonData.lng_index],
                270, 80
            )
            win_warn.center_to_parent(self.window())
            win_warn.ok_clicked.connect(win_warn.deleteLater)
            win_warn.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА 

class NewMfSettings(QWidget):
    yellow_warning_svg = Static.COMMON_ICONS / "yellow_warning.svg"

    def __init__(self, mf_path: str = None):
        super().__init__()
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(10)

        self.mf_alias_widget = MfAliasWidget(JsonData.lng_index)
        self.mf_alias_widget.changed.connect(
            lambda: self.mf_save_widget.show_warning()
        )
        main_lay.addWidget(self.mf_alias_widget)

        self.mf_path_widget = MfPathWidget(
            lng_index=JsonData.lng_index,
            mf_path=mf_path
        )
        self.mf_path_widget.changed.connect(
            lambda: self.mf_path_widget_changed()
        )
        main_lay.addWidget(self.mf_path_widget)

        self.mf_stop_list = MfStopListWidget(
            lng_index=JsonData.lng_index,
            mf_stop_list=[]
        )
        self.mf_stop_list.text_edit.textChanged.connect(
            lambda: self.mf_save_widget.show_warning()
        )
        main_lay.addWidget(self.mf_stop_list)

        save_group = UGroupBox()
        main_lay.addWidget(save_group)
        save_group_container = QVBoxLayout(save_group)
        save_group_container.setContentsMargins(*RowArrowWidget.group_margings)
        save_group_container.setSpacing(RowArrowWidget.group_spacing)

        self.mf_save_widget = SaveRowArrowWidget(JsonData.lng_index)
        self.mf_save_widget.clicked.connect(self.save_mf_settings)
        save_group_container.addWidget(self.mf_save_widget)

        main_lay.addStretch()

        if mf_path:
            self.mf_path_widget_changed()

    def mf_path_widget_changed(self):
        basename = os.path.basename(self.mf_path_widget.mf_path).capitalize()
        self.mf_alias_widget.line_edit.setText(basename)
        self.mf_save_widget.show_warning()

    def save_mf_settings(self):

        def save_mf(mf_alias, mf_path, mf_stop_list):
            mf = Mf(
                mf_alias=mf_alias,
                mf_paths=[mf_path, ],
                mf_stop_list=mf_stop_list,
                mf_current_path=mf_path
            )
            Mf.items.append(mf)
            Mf.write_json_data()
            restart_app()

        def get_mf_alias():
            mf_alias = self.mf_alias_widget.validate()
            if not mf_alias:
                return None
            for i in Mf.items:
                if i.mf_alias == mf_alias:
                    win_warn = WarningWindow(
                        Lng.alias_already_exists[JsonData.lng_index],
                        270, 80
                    )
                    win_warn.center_to_parent(self.window())
                    win_warn.ok_clicked.connect(win_warn.deleteLater)
                    win_warn.show()
                    return None
            return mf_alias

        mf_path = self.mf_path_widget.validate()
        mf_alias = get_mf_alias()
        mf_stop_list = self.mf_stop_list.text_edit.toPlainText().split("\n")

        if mf_path and mf_alias:
            super_win = SuperConfirmWindow(
                Lng.confirm_mf_path[JsonData.lng_index],
                310, 105
            )
            super_win.ok_clicked.connect(
                lambda: save_mf(mf_alias, mf_path, mf_stop_list)
            )
            super_win.center_to_parent(self.window())
            super_win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class WinSettings(UMainWidget):
    closed = pyqtSignal()
    
    image_folder_svg = Static.COMMON_ICONS / "image_folder.svg"
    new_folder_svg = Static.COMMON_ICONS / "new_folder.svg"
    filters_svg = Static.COMMON_ICONS / "filters.svg"
    settings_svg = Static.COMMON_ICONS / "settings.svg"
    yellow_warning_svg = Static.COMMON_ICONS / "yellow_warning.svg"

    ww = 700
    hh = 560

    def __init__(self, settings_item: SettingsItem):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.settings[JsonData.lng_index])
        self.setFixedSize(self.ww, self.hh)

        self.settings_item = settings_item

        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter()
        self.splitter.setHandleWidth(15)
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        left_group = UGroupBox()
        self.splitter.addWidget(left_group)
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(1, 10, 1, 1)
        left_layout.setSpacing(0)

        self.left_menu = VListWidget()
        self.left_menu.clicked.connect(self.left_menu_click)
        left_layout.addWidget(self.left_menu)

        main_settings_item = VListWidgetItem(
            parent=self.left_menu,
            text=Lng.general[JsonData.lng_index]
        )
        main_settings_item.setIcon(QIcon(self.settings_svg))
        self.left_menu.addItem(main_settings_item)
        
        filter_settings = VListWidgetItem(
            parent=self.left_menu,
            text=Lng.filters[JsonData.lng_index]
        )
        filter_settings.setIcon(QIcon(self.filters_svg))
        self.left_menu.addItem(filter_settings)

        new_folder = VListWidgetItem(
            parent=self.left_menu,
            text=Lng.new_folder[JsonData.lng_index]
        )
        new_folder.setIcon(QIcon(self.new_folder_svg))
        self.left_menu.addItem(new_folder)
        
        spacer = VListSpacerItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in Mf.items:
            new_folder = VListWidgetItem(self.left_menu, text=i.mf_alias)
            new_folder.setIcon(QIcon(self.image_folder_svg))
            self.left_menu.addItem(new_folder)

        self.right_wid = QWidget()
        self.right_lay = QVBoxLayout(self.right_wid)
        self.right_lay.setContentsMargins(0, 0, 0, 0)
        self.right_lay.setSpacing(0)
        self.splitter.addWidget(self.right_wid)
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
            for x, i in enumerate(Mf.items, start=4):
                if i.mf_alias == self.settings_item.content:
                    idx = x
                    break
        self.left_menu.setCurrentRow(idx)
        self.init_right_side(idx)

    def init_right_side(self, idx: int):
        if idx == 0:
            r_wid = GeneralSettings()
            # r_wid.lang_changed.connect(lambda: self.left_menu_click())
        elif idx == 1:
            r_wid = FiltersWid()
        elif idx == 2:
            if self.settings_item.type_ == "new_folder":
                r_wid = NewMfSettings(self.settings_item.content)
                self.settings_item.type_ = "general"
                self.settings_item.content = ""
            else:
                r_wid = NewMfSettings()
        elif idx > 3:
            item: VListWidgetItem = self.left_menu.item(idx)
            for index, mf in enumerate(Mf.items):
                if mf.mf_alias == item.text():
                    r_wid = MfSettings(index)
                    self.settings_item.type_ = "general"
                    self.settings_item.content = ""
                    break
        self.right_lay.insertWidget(0, r_wid)

    def clear_right_side(self):
        wids = (GeneralSettings, MfSettings, NewMfSettings, FiltersWid)
        right_wid = self.right_wid.findChild(wids)
        right_wid.deleteLater()

    def left_menu_click(self, *args):
        self.clear_right_side()
        idx = self.left_menu.currentRow()
        self.init_right_side(idx)

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