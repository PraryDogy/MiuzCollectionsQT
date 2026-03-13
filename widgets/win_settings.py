import copy
import os
import re
import shutil
import subprocess
import sys

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QIcon
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame, QGroupBox, QLabel,
                             QLineEdit, QSpacerItem, QSpinBox, QSplitter,
                             QTableWidget, QTableWidgetItem, QWidget)
from typing_extensions import Optional

from cfg import Cfg, Static
from system.filters import Filters
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker
from system.paletes import ThemeChanger
from system.servers import Servers
from system.shared_utils import SharedUtils
from system.tasks import HashDirSize, MfDataCleaner, UThreadPool
from system.utils import Utils

from ._base_widgets import (HSep, SingleActionWindow, SmallBtn, UHBoxLayout,
                            ULineEdit, UListSpacerItem, UListWidgetItem, UMenu,
                            UTextEdit, UVBoxLayout, VListWidget)
from .win_warn import ConfirmWindow, WarningWindow


def restart_app():
    ProcessWorker.stop_all()
    QApplication.quit()
    os.execl(sys.executable, sys.executable, *sys.argv)


class ULabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumWidth(30)


class UPushButton(SmallBtn):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(100)


class GroupWid(QGroupBox):
    def __init__(self):
        """
        QGroupBox + self.layout_ (vertical layout)
        """
        super().__init__()
        self.layout_ = UVBoxLayout()
        self.layout_.setContentsMargins(6, 2, 6, 2)
        self.layout_.setSpacing(2)
        self.setLayout(self.layout_)


class GroupChild(QWidget):
    hh = 30
    def __init__(self):
        """
        QWidget fixed height + horizontal layout
        """
        super().__init__()
        self.setFixedHeight(self.hh)
        self.layout_ = UHBoxLayout()
        self.setLayout(self.layout_)


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
    

class SvgWarning(QSvgWidget):
    img = "./images/warning.svg"
    size_ = 22
    def __init__(self):
        super().__init__()
        self.setFixedSize(self.size_, self.size_)
        self.load(self.img)
        pol = self.sizePolicy()
        pol.setRetainSizeWhenHidden(True)
        self.setSizePolicy(pol)


class TextEditWidget(GroupWid):
    textChanged = pyqtSignal()

    def __init__(self, title: str, placeholder: str, text: Optional[str]):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout_.setSpacing(10)

        self.title_wid = ULabel(title)
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
    


# ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ ОСНОВНЫЕ НАСТРОЙКИ



class RebootSettings(GroupWid):
    cfg_changed = pyqtSignal()
    spin_max = 60
    spin_min = 0

    def __init__(self, cfg_clone: Cfg):
        super().__init__()
        self.cfg_clone = cfg_clone

        lng_wid = GroupChild()
        self.layout_.addWidget(lng_wid)

        self.lng_text = ULabel(Lng.language_max[Cfg.lng])
        lng_wid.layout_.addWidget(self.lng_text)

        lng_wid.layout_.addStretch()

        self.lng_menu = UMenu(None)
        for value in (0, 1):
            action = QAction(Lng.russian[value], self.lng_menu)
            action.triggered.connect(lambda e, v=value: self.lang_action_cmd(v))
            self.lng_menu.addAction(action)

        self.lng_btn = UPushButton(text=Lng.russian[Cfg.lng])
        self.lng_btn.setFixedWidth(109)
        self.lng_btn.setMenu(self.lng_menu)
        lng_wid.layout_.addWidget(self.lng_btn)

        self.layout_.addWidget(HSep())

        scaner_time_wid = GroupChild()
        self.layout_.addWidget(scaner_time_wid)

        scaner_time_text = ULabel(Lng.search_interval[Cfg.lng], self)
        scaner_time_wid.layout_.addWidget(scaner_time_text)

        scaner_time_wid.layout_.addStretch()

        self.spin = QSpinBox(self)
        self.spin.setMinimum(self.spin_min)
        self.spin.setMaximum(self.spin_max)
        self.spin.setFixedHeight(27)
        self.spin.setFixedWidth(100)
        self.spin.findChild(QLineEdit).setTextMargins(3, 0, 3, 0)
        self.spin.setSuffix(f" {Lng.minutes[Cfg.lng]}")
        self.spin.setValue(self.cfg_clone.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        scaner_time_wid.layout_.addWidget(self.spin)

        self.layout_.addWidget(HSep())

        reset_data_wid = GroupChild()
        reset_data_wid.mouseReleaseEvent = self.reset_btn_cmd
        self.layout_.addWidget(reset_data_wid)

        reset_data_text = ULabel(Lng.erase_data[Cfg.lng])
        reset_data_wid.layout_.addWidget(reset_data_text)

        reset_data_wid.layout_.addStretch()

        self.reset_data_btn = SvgArrow()
        reset_data_wid.layout_.addWidget(self.reset_data_btn)

    def lang_action_cmd(self, value: int):
        self.cfg_clone.lng = value
        self.lng_btn.setText(Lng.russian[value])
        self.cfg_changed.emit()

    def reset_btn_cmd(self, *args):
        def fin():
            self.deleteLater()
            shutil.rmtree(Static.external_files_dir)
            restart_app()

        reset_win = ConfirmWindow(Lng.erase_data_long[Cfg.lng])
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

        self.cfg_clone.scaner_minutes = value
        self.cfg_changed.emit()


class SizesWin(SingleActionWindow):
    ww = 500
    hh = 330

    def __init__(self, sizes: dict[str, int], parent=None):
        super().__init__(parent)
        self.setWindowTitle(Lng.data_size[Cfg.lng])
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
        first_row = QLabel(f"{Lng.data_size[Cfg.lng]}: {total_size}")
        info_layout.addWidget(first_row)

        total = sum(i["total"] for i in sizes.values())
        sec_row = QLabel(f"{Lng.images[Cfg.lng]}: {total}")
        info_layout.addWidget(sec_row)

        layout.addWidget(info_widget)

        headers = [Lng.folder[Cfg.lng], Lng.file_size[Cfg.lng], Lng.images[Cfg.lng]]
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


class NonRebootSettings(GroupWid):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(80)
        self.data = {}

        data_size_wid = GroupChild()
        data_size_wid.mouseReleaseEvent = self.show_sizes_win
        self.layout_.addWidget(data_size_wid)

        data_size_text = ULabel(text=Lng.statistic[Cfg.lng])
        data_size_wid.layout_.addWidget(data_size_text)

        data_size_wid.layout_.addStretch()

        data_size_btn = SvgArrow()
        data_size_wid.layout_.addWidget(data_size_btn)

        self.layout_.addWidget(HSep())

        show_files_wid = GroupChild()
        show_files_wid.mouseReleaseEvent = self.show_files_cmd
        self.layout_.addWidget(show_files_wid)

        show_files_text = ULabel(Lng.show_system_files[Cfg.lng])
        show_files_wid.layout_.addWidget(show_files_text)

        show_files_btn = SvgArrow(text=Lng.show[Cfg.lng])
        show_files_wid.layout_.addWidget(show_files_btn)

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
            subprocess.Popen(["open", Static.external_files_dir])
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


class Themes(GroupWid):
    clicked = pyqtSignal()
    svg_theme_system = "./images/system_theme.svg"
    svg_theme_dark = "./images/dark_theme.svg"
    svg_theme_light = "./images/light_theme.svg"

    def __init__(self):
        super().__init__()
        # self.setFixedHeight(120)

        title_wid = GroupChild()
        self.layout_.addWidget(title_wid)

        title_text = ULabel("Тема")
        title_wid.layout_.addWidget(title_text)

        self.layout_.addWidget(HSep())
        self.layout_.addSpacerItem(QSpacerItem(0, 10))

        themes_wid = GroupChild()
        themes_wid.setFixedHeight(80)
        themes_wid.layout_.setSpacing(20)
        themes_wid.layout_.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout_.addWidget(themes_wid)

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
            themes_wid.layout_.addWidget(f)
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

        copy_text = QAction(parent=context_menu, text=Lng.copy[Cfg.lng])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lng.copy_all[Cfg.lng])
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

    def __init__(self, cfg_clone: Cfg):
        super().__init__()

        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(10)
        v_lay.setContentsMargins(0, 0, 0, 10)
        self.setLayout(v_lay)

        reboot_settings = RebootSettings(cfg_clone)
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



class FiltersWid(GroupWid):
    changed = pyqtSignal()

    def __init__(self, filters_clone: list[str]):
        super().__init__()
        self.filters_clone = filters_clone

        filters_text = ULabel(Lng.filters_descr[Cfg.lng])
        filters_text.setWordWrap(True)
        self.layout_.addWidget(filters_text)

        self.layout_.addSpacerItem(QSpacerItem(0, 5))
        self.layout_.addWidget(HSep())

        erase_filters_wid = GroupChild()
        erase_filters_wid.setFixedHeight(40)
        erase_filters_wid.mouseReleaseEvent = self.reset_btn_cmd
        self.layout_.addWidget(erase_filters_wid)

        erase_filters_text = QLabel(Lng.reset_filters[Cfg.lng])
        erase_filters_wid.layout_.addWidget(erase_filters_text)

        erase_filters_wid.layout_.addStretch()

        self.reset_btn = SvgArrow()
        erase_filters_wid.layout_.addWidget(self.reset_btn)

        self.layout_.addWidget(HSep())
        self.layout_.addSpacerItem(QSpacerItem(0, 10))

        self.filters_edit = UTextEdit()
        self.filters_edit.setFixedHeight(220)
        self.filters_edit.setPlaceholderText(Lng.filters[Cfg.lng])
        self.filters_edit.setPlainText("\n".join(self.filters_clone))
        self.filters_edit.textChanged.connect(self.on_text_changed)
        self.layout_.addWidget(self.filters_edit)
        
    def reset_btn_cmd(self, *args):
        def fin():
            self.filters_edit.clear()
            self.filters_edit.insertPlainText(
                "\n".join(Filters.default_filters)
            )
            self.filters_win.deleteLater()
            self.changed.emit

        self.filters_win = ConfirmWindow(Lng.reset_filters_long[Cfg.lng])
        self.filters_win.ok_clicked.connect(fin)
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def on_text_changed(self):
        text = self.filters_edit.toPlainText().strip()
        lines = [line for line in text.split("\n") if line]
        self.filters_clone.clear()   # очищаем текущий список
        self.filters_clone.extend(lines)  # добавляем новые элементы
        self.changed.emit()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ВИДЖЕТЫ ПАПОК С КОЛЛЕКЦИЯМИ ВИДЖЕТЫ ПАПОК С КОЛЛЕКЦИЯМИ 

class MfPaths(TextEditWidget):
    def __init__(self, mf: Mf):
        super().__init__(
            title=Lng.images_folder_path[Cfg.lng],
            placeholder=Lng.folder_path[Cfg.lng],
            text="\n".join(i for i in mf.mf_paths),
        )
        self.mf = mf
        self.textChanged.connect(self.set_data)

    def set_data(self, *args):
        self.mf.mf_paths = self.get_list()

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
            title=Lng.ignore_list_descr[Cfg.lng],
            placeholder=Lng.ignore_list[Cfg.lng],
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


class MfSave(GroupWid):
    clicked_ = pyqtSignal()
    def __init__(self):
        super().__init__()        

        save_wid_child = GroupChild()
        self.layout_.addWidget(save_wid_child)

        save_text = ULabel(Lng.save[Cfg.lng])
        save_wid_child.layout_.addWidget(save_text)

        save_wid_child.layout_.addSpacerItem(QSpacerItem(10, 0))

        self.warning_svg = SvgWarning()
        self.warning_svg.setFixedSize(14, 14)
        save_wid_child.layout_.addWidget(self.warning_svg)
        self.warning_svg.hide()

        save_wid_child.layout_.addStretch()

        save_btn = SvgArrow()
        save_wid_child.layout_.addWidget(save_btn)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_.emit()
        return super().mouseReleaseEvent(event)


# ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ ПАПКА С КОЛЛЕКЦИЯМИ 


class MfSettings(QWidget):
    changed = pyqtSignal()

    def __init__(self, mf: Mf, mf_list_clone: list[Mf]):
        super().__init__()
        self.mf = mf
        self.mf_list_clone = mf_list_clone

        main_lay = UVBoxLayout()
        main_lay.setSpacing(15)
        self.setLayout(main_lay)

        # Верхний ряд с названием
        self.name_wid = GroupWid()
        main_lay.addWidget(self.name_wid)
        name_text = ULabel(f"{Lng.alias[Cfg.lng]}: {mf.mf_alias}")
        name_text.setFixedHeight(GroupChild.hh)
        self.name_wid.layout_.addWidget(name_text)

        self.mf_paths = MfPaths(mf)
        self.mf_paths.textChanged.connect(
            lambda: self.mf_save.warning_svg.show()
        )
        main_lay.addWidget(self.mf_paths)

        self.mf_stop_list = MfStopList(mf)
        self.mf_stop_list.textChanged.connect(
            lambda: self.mf_save.warning_svg.show()
        )
        main_lay.addWidget(self.mf_stop_list)

        self.mf_save = MfSave()
        self.mf_save.clicked_.connect(self.save)
        main_lay.addWidget(self.mf_save)

        general_wid = GroupWid()
        main_lay.addWidget(general_wid)

        reset_wid = GroupChild()
        reset_wid.mouseReleaseEvent = self.set_reset_flag
        general_wid.layout_.addWidget(reset_wid)

        reset_text = ULabel(text=Lng.reset_mf[Cfg.lng])
        reset_wid.layout_.addWidget(reset_text)

        reset_wid.layout_.addStretch()

        reset_btn = SvgArrow()
        reset_wid.layout_.addWidget(reset_btn)

        general_wid.layout_.addWidget(HSep())

        remove_wid = GroupChild()
        remove_wid.mouseReleaseEvent = self.remove_cmd
        general_wid.layout_.addWidget(remove_wid)

        remove_text = ULabel(text=Lng.remove_folder[Cfg.lng])
        remove_wid.layout_.addWidget(remove_text)
        remove_wid.layout_.addStretch()
        remove_btn = SvgArrow()
        remove_wid.layout_.addWidget(remove_btn)

        main_lay.addSpacerItem(QSpacerItem(0, 15))

    def remove_cmd(self, *args):

        def fin():
            for i in Mf.mf_list:
                if i.mf_alias == self.mf.mf_alias:
                    Mf.mf_list.remove(i)
                    break
            Mf.write_json_data()
            restart_app()

        if len(self.mf_list_clone) == 1:
            win = WarningWindow(Lng.at_least_one_folder_required[Cfg.lng])
        else:
            win = ConfirmWindow(Lng.remove_folder_long[Cfg.lng])
            win.ok_clicked.connect(fin)
        win.center_to_parent(self.window())
        win.show()

    def set_reset_flag(self, *args):

        def reset_data():
            self.reset_task = MfDataCleaner(self.mf.mf_alias)
            self.reset_task.sigs.finished_.connect(restart_app)
            UThreadPool.start(self.reset_task)

        win = ConfirmWindow(Lng.reset_mf_long[Cfg.lng])
        win.ok_clicked.connect(reset_data)
        win.center_to_parent(self.window())
        win.show()

    def save(self, *args):

        def fin():
            self.mf.mf_paths = paths
            self.mf.mf_stop_list = stop_list

            for i in Mf.mf_list:
                if i.mf_alias == self.mf.mf_alias:
                    i.mf_paths = paths
                    i.mf_stop_list = stop_list
                    break

            Mf.write_json_data()
            restart_app()

        paths = self.mf_paths.get_list()
        stop_list = self.mf_stop_list.get_list()

        def show_warn(text: str):
            win_warn = WarningWindow(text)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        if not paths:
            show_warn(Lng.select_folder_path[Cfg.lng])
            return

        win = ConfirmWindow(Lng.save_text_long[Cfg.lng])
        win.ok_clicked.connect(fin)
        win.center_to_parent(self.window())
        win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА НОВАЯ ПАПКА 

class NewFolder(QWidget):
    svg_warning = "./images/warning.svg"
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

        main_lay = UVBoxLayout()
        main_lay.setSpacing(15)
        self.setLayout(main_lay)

        name_wid = GroupWid()
        main_lay.addWidget(name_wid)

        self.name_text = QLabel(Lng.folder_name[Cfg.lng])
        name_wid.layout_.addWidget(self.name_text)

        self.name_line_edit = ULineEdit()
        self.name_line_edit.setPlaceholderText(Lng.alias_immutable[Cfg.lng])
        name_wid.layout_.addWidget(self.name_line_edit)

        self.mf_paths = MfPaths(self.mf)
        main_lay.addWidget(self.mf_paths)

        self.mf_stop_list = MfStopList(self.mf)
        main_lay.addWidget(self.mf_stop_list)

        save_wid = GroupWid()
        save_wid.mouseReleaseEvent = self.save_start
        main_lay.addWidget(save_wid)
        
        save_wid_child = GroupChild()
        save_wid.layout_.addWidget(save_wid_child)

        save_text = ULabel(Lng.save[Cfg.lng])
        save_wid_child.layout_.addWidget(save_text)

        save_wid_child.layout_.addSpacerItem(QSpacerItem(10, 0))

        self.warning_svg = SvgWarning()
        self.warning_svg.setFixedSize(14, 14)
        save_wid_child.layout_.addWidget(self.warning_svg)
        self.warning_svg.hide()

        save_wid_child.layout_.addStretch()

        save_btn = SvgArrow()
        save_wid_child.layout_.addWidget(save_btn)

        QTimer.singleShot(100, self.text_changed)

    def text_changed(self):
        for i in (self.name_line_edit, self.mf_paths, self.mf_stop_list):
            i.textChanged.connect(self.warning_svg.show)
        
    def preset_new_folder(self, url: str):
        if url:
            url = os.sep + url.strip(os.sep)
            basename = os.path.basename(url)
            self.name_line_edit.setText(basename)
            self.warning_svg.show()
        self.mf_paths.text_edit_wid.setPlainText(url)

    def save_fin(self, folder_name: str, paths: list, stop_list: list):
        self.mf.mf_alias = folder_name
        self.mf.mf_paths = paths
        self.mf.mf_stop_list = stop_list
        # мы добавляем новую папку менно в Mf.list_ а не в clone
        # чтобы отменить изменения из других отделов
        # и применить изменения только по новой папке
        Mf.mf_list.append(self.mf)
        Mf.write_json_data()
        restart_app()

    def save_start(self, *args):

        pattern = r'^[A-Za-zА-Яа-яЁё0-9 ]+$'
        folder_name = self.name_line_edit.text()
        paths = self.mf_paths.get_list()
        stop_list = self.mf_stop_list.get_list()

        def show_warn(text: str):
            win_warn = WarningWindow(text)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        if not folder_name:
            show_warn(Lng.enter_alias_warning[Cfg.lng])
            return

        elif any(i.mf_alias == folder_name for i in self.mf_list_clone):
            show_warn(
                f'{Lng.alias[Cfg.lng]} "{folder_name}" '
                f'{Lng.already_taken[Cfg.lng].lower()}'
            )
            return

        elif len(folder_name) < 5 or len(folder_name) > 30:
            show_warn(f'{Lng.string_limit[Cfg.lng]}')
            return

        elif not re.fullmatch(pattern, folder_name):
            show_warn(f'{Lng.valid_message[Cfg.lng]}')
            return

        elif not paths:
            show_warn(Lng.select_folder_path[Cfg.lng])
            return

        win = ConfirmWindow(Lng.save_text_long[Cfg.lng])
        win.ok_clicked.connect(
            self.save_fin(folder_name, paths, stop_list)
        )
        win.center_to_parent(self.window())
        win.show()

    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)


# ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК ОКНО НАСТРОЕК 


class WinSettings(SingleActionWindow):
    closed = pyqtSignal()
    svg_folder = "./images/img_folder.svg"
    svg_filters = "./images/filters.svg"
    svg_settings = "./images/settings.svg"
    svg_new_folder = "./images/new_folder.svg"
    svg_size = 16

    def __init__(self, settings_item: SettingsItem):
        super().__init__()
        self.setWindowTitle(Lng.settings[Cfg.lng])
        self.setFixedSize(700, 560)

        self.cfg_clone = copy.deepcopy(cfg)
        self.mf_list_clone = copy.deepcopy(Mf.mf_list)
        self.filters_clone = copy.deepcopy(Filters.filter_list)
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

        main_settings_item = UListWidgetItem(
            parent=self.left_menu,
            text=Lng.general[Cfg.lng]
        )
        main_settings_item.setIcon(QIcon(self.svg_settings))
        self.left_menu.addItem(main_settings_item)
        
        filter_settings = UListWidgetItem(
            parent=self.left_menu,
            text=Lng.filters[Cfg.lng]
        )
        filter_settings.setIcon(QIcon(self.svg_filters))
        self.left_menu.addItem(filter_settings)

        new_folder = UListWidgetItem(
            parent=self.left_menu,
            text=Lng.new_folder[Cfg.lng]
        )
        new_folder.setIcon(QIcon(self.svg_new_folder))
        self.left_menu.addItem(new_folder)
        
        spacer = UListSpacerItem(self.left_menu)
        self.left_menu.addItem(spacer)

        for i in Mf.mf_list:
            new_folder = UListWidgetItem(self.left_menu, text=i.mf_alias)
            new_folder.setIcon(QIcon(self.svg_folder))
            self.left_menu.addItem(new_folder)

        self.right_wid = QWidget()
        self.right_lay = UVBoxLayout()
        self.right_wid.setLayout(self.right_lay)
        self.splitter.addWidget(self.right_wid)

        self.right_lay.addStretch()

        self.btns_wid = QWidget()
        self.btns_wid.setFixedHeight(26)
        self.right_lay.addWidget(self.btns_wid)
        btns_lay = UHBoxLayout()
        btns_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btns_lay.setSpacing(10)
        self.btns_wid.setLayout(btns_lay)

        self.warn_svg = SvgWarning()
        btns_lay.addWidget(self.warn_svg)
        self.warn_svg.hide()

        self.ok_btn = UPushButton(Lng.ok[Cfg.lng])
        self.ok_btn.setFixedWidth(95)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_lay.addWidget(self.ok_btn)

        cancel_btn = UPushButton(Lng.cancel[Cfg.lng])
        cancel_btn.setFixedWidth(95)
        cancel_btn.clicked.connect(self.deleteLater)
        btns_lay.addWidget(cancel_btn)

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
        self.ok_btn.setText(Lng.restart[Cfg.lng])
        self.warn_svg.show()

    def init_right_side(self, idx: int):
        if idx == 0:
            self.btns_wid.show()
            r_wid = GeneralSettings(self.cfg_clone)
        elif idx == 1:
            self.btns_wid.show()
            r_wid = FiltersWid(self.filters_clone)
        elif idx == 2:
            self.btns_wid.hide()
            r_wid = NewFolder(self.mf_list_clone)
            r_wid.preset_new_folder(self.settings_item.content)
        elif idx > 3:
            self.btns_wid.hide()
            item: UListWidgetItem = self.left_menu.item(idx)
            for mf in self.mf_list_clone:
                if mf.mf_alias == item.text():
                    r_wid = MfSettings(mf, self.mf_list_clone)
                    break
        r_wid.changed.connect(self.blink_ok_btn)
        self.right_lay.insertWidget(0, r_wid)

    def add_mf(self, mf: Mf):
        self.mf_list_clone.append(mf)
        item = UListWidgetItem(self.left_menu, text=mf.mf_alias)
        item.setIcon(QIcon(self.svg_folder))
        item.mf = mf
        self.left_menu.addItem(item)
        self.left_menu.setCurrentItem(item)
        self.clear_right_side()
        index = self.left_menu.count() - 1
        self.init_right_side(index)
        self.blink_ok_btn()

    def clear_right_side(self):
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

        if self.warn_svg.isHidden():
            self.deleteLater()
            return

        folder_no_paths = validate_folders()
        if folder_no_paths:
            win_warn = WarningWindow(
                f"{Lng.select_folder_path[Cfg.lng]} \"{folder_no_paths}\""
            )
            win_warn.center_to_parent(self.window())
            win_warn.show()
        else:
            Mf.mf_list = self.mf_list_clone
            Mf.write_json_data()

            Filters.filter_list = self.filters_clone
            Filters.write_json_data()

            Cfg.lng = self.cfg_clone.lng
            Cfg.scaner_minutes = self.cfg_clone.scaner_minutes
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


class SingleSettings(SingleActionWindow):
    """
    Окно настроек при первой настройке приложения.
    """
    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 500)
        self.mf_list_clone = copy.deepcopy(Mf.mf_list)
        self.new_mf = NewFolder(mf_list_clone=self.mf_list_clone)
        # перехватываем нажатие кнопки "сохранить"
        self.new_mf.save_fin = self.new_save_fin
        self.central_layout.addWidget(self.new_mf)
        self.central_layout.addSpacerItem(QSpacerItem(0, 15))

    def new_save_fin(self, folder_name, paths, stop_list):
        mf = Mf(
            mf_alias=folder_name,
            mf_paths=paths,
            mf_stop_list=stop_list,
            mf_current_path=""
        )
        Mf.mf_list.append(mf)
        Cfg.make_external_empty_files()
        Mf.write_json_data()
        Cfg.write_json_data()
        Filters.write_json_data()
        Servers.write_json_data()
        restart_app()

    def closeEvent(self, a0):
        os._exit(1)
        return super().closeEvent(a0)