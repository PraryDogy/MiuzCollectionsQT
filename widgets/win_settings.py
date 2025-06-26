import os
import shutil
import subprocess

from PyQt5.QtCore import QModelIndex, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QSpacerItem, QSpinBox, QTabWidget, QWidget)

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.paletes import ThemeChanger
from system.utils import MainUtils
from ._base_widgets import (UHBoxLayout, ULineEdit, UMenu, UTextEdit,
                            UVBoxLayout, WinSystem)

LIST_ITEM_H = 25
ICON_SVG = os.path.join(Static.images_dir, "icon.svg")


class RebootableSettings(QGroupBox):
    reset_data = pyqtSignal()
    new_lang = pyqtSignal(int)

    def __init__(self):
        """
        Сигналы:
        - reset_data() сброс всех настроек приложения
        - new_lang(0 или 1): system > lang > _Lang._lang_name. 
        0 это русский язык, 1 это английский
        """
        super().__init__()

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
        self.reset_data_btn.clicked.connect(lambda: self.reset_data.emit())
        sec_row_lay.addWidget(self.reset_data_btn)

        descr = QLabel(text=Lang.restore_db_descr)
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def lang_btn_cmd(self, *args):
        if self.lang_btn.text() == "Русский":
            _lang_name = "English" 
            self.lang_btn.setText(_lang_name)
            self.new_lang.emit(1) # соответствует system > lang > _lang_name
        else:
            _lang_name = "Русский"
            self.lang_btn.setText(_lang_name)
            self.new_lang.emit(0)  # соответствует system > lang > _lang_name


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

        sec_row_wid = QWidget()
        v_lay.addWidget(sec_row_wid)
        sec_row_lay = UHBoxLayout()
        sec_row_lay.setSpacing(15)
        sec_row_wid.setLayout(sec_row_lay)

        self.show_files_btn = QPushButton(text=Lang.show_app_support)
        self.show_files_btn.setFixedWidth(115)
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        sec_row_lay.addWidget(self.show_files_btn)

        self.lang_label = QLabel(Lang.show_files)
        sec_row_lay.addWidget(self.lang_label)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.APP_SUPPORT_DIR])
        except Exception as e:
            print(e)


class AddRowWindow(WinSystem):
    finished_ = pyqtSignal(str)

    def __init__(self):
        """
        Сигналы: finished_(str), возвращает текст из поля ввода
        """
        super().__init__()
        self.setFixedSize(300, 80)
        self.setWindowTitle(Lang.paste_text)
        self.central_layout.setSpacing(10)

        self.text_edit = ULineEdit()
        self.text_edit.setPlaceholderText(Lang.paste_text)
        self.central_layout.addWidget(self.text_edit)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = UHBoxLayout()
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        h_lay.addStretch()

        ok_btn = QPushButton(text=Lang.ok)
        ok_btn.clicked.connect(self.ok_cmd)
        ok_btn.setFixedWidth(90)
        h_lay.addWidget(ok_btn)

        can_btn = QPushButton(text=Lang.cancel)
        can_btn.clicked.connect(self.close)
        can_btn.setFixedWidth(90)
        h_lay.addWidget(can_btn)

        h_lay.addStretch()

    def ok_cmd(self):
        text = self.text_edit.text().replace("\n", "").strip()
        if text:
            self.finished_.emit(text)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd()
        return super().keyPressEvent(a0)


class MainFolderItemsWid(QListWidget):
    main_folder_changed = pyqtSignal()

    def __init__(self, main_folder_copy: MainFolder, is_stop_list: bool):
        """
        Сигналы:
        - main_folder_changed (): сигнал об изменении копии объекта MainFolder. Сигнал означает,
        что нужно обновить соответствующий объект MainFolder в списке MainFolder.list_.

        Описание:
        - Виджет работает с копией объекта MainFolder, а не с оригиналом. Это необходимо для того,
        чтобы изменения в объекте применялись только после нажатия "ОК" в окне настроек.
        Если пользователь нажимает "Отмена", оригинальный MainFolder остаётся без изменений.
        """
        super().__init__()
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.contextMenuEvent = self.list_item_context

        self.main_folder_copy = main_folder_copy
        self.is_stop_list = is_stop_list

        if self.is_stop_list:
            items = self.main_folder_copy.stop_list
        else:
            items = self.main_folder_copy.paths

        for i in items:
            item_ = QListWidgetItem(i)
            item_.setSizeHint(QSize(self.width(), LIST_ITEM_H))
            item_.item_name = i
            self.addItem(item_)

    def list_item_context(self, ev):
        menu = UMenu(event=ev)

        add_item = QAction(parent=menu, text=Lang.add_)
        add_item.triggered.connect(self.open_add_row_window)
        menu.addAction(add_item)

        wid = self.itemAt(ev.pos())
        if wid:
            del_item = QAction(parent=menu, text=Lang.del_)
            del_item.triggered.connect(self.del_item_cmd)
            menu.addAction(del_item)

            copy_text = QAction(parent=menu, text=Lang.copy)
            cmd = lambda: MainUtils.copy_text(wid.text())
            copy_text.triggered.connect(cmd)
            menu.addAction(copy_text)

        menu.show_menu()

    def mouseReleaseEvent(self, e):
        wid = self.itemAt(e.pos())
        if not wid:
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
        return super().mouseReleaseEvent(e)

    def del_item_cmd(self):
        selected_item = self.currentItem()
        row = self.row(selected_item)
        row_text = selected_item.text()

        if self.is_stop_list:
            self.main_folder_copy.stop_list.remove(row_text)
        else:
            self.main_folder_copy.paths.remove(row_text)

        self.takeItem(row)
        self.main_folder_changed.emit()

    def open_add_row_window(self):
        win = AddRowWindow()
        win.finished_.connect(self.add_row_fin)
        win.center_relative_parent(self.window())
        win.show()

    def add_row_fin(self, text: str):
        item_ = QListWidgetItem(text)
        item_.setSizeHint(QSize(self.width(), LIST_ITEM_H))
        item_.item_name = text
        self.addItem(item_)
        if self.is_stop_list:
            self.main_folder_copy.stop_list.append(text)
        else:
            self.main_folder_copy.paths.append(text)
        self.main_folder_changed.emit()


class EditMainFoldersWid(QTabWidget):
    main_folder_changed = pyqtSignal(object)

    def __init__(self):
        """
        Сигналы:
        - main_folder_changed (object): сигнал об изменении копии объекта MainFolder. Сигнал означает,
        что нужно обновить соответствующий объект MainFolder в списке MainFolder.list_.

        Описание:
        - Виджет работает с копией объекта MainFolder, а не с оригиналом. Это необходимо для того,
        чтобы изменения в объекте применялись только после нажатия "ОК" в окне настроек.
        Если пользователь нажимает "Отмена", оригинальный MainFolder остаётся без изменений.
        """
        super().__init__()
        self.stop_colls_wid: dict[int, UTextEdit] = {}
        self.coll_folders_wid: dict[int, UTextEdit] = {}

        for x in MainFolder.list_:
            main_folder_copy = x.get_instance_copy()
            wid = self.tab_ui(main_folder_copy)
            self.addTab(wid, main_folder_copy.name)

    def tab_ui(self, main_folder_copy: MainFolder):
        wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        wid.setLayout(v_lay)

        h_wid_one = QWidget()
        v_lay.addWidget(h_wid_one)
        h_lay_one = UHBoxLayout()
        h_lay_one.setSpacing(15)
        h_wid_one.setLayout(h_lay_one)

        add_stop_coll_btn = QPushButton(Lang.add_)
        add_stop_coll_btn.setFixedWidth(115)
        h_lay_one.addWidget(add_stop_coll_btn)

        stop_colls_lbl = QLabel(Lang.sett_stopcolls)
        h_lay_one.addWidget(stop_colls_lbl)

        stop_colls_list = MainFolderItemsWid(main_folder_copy, True)
        cmd = lambda: self.main_folder_changed.emit(main_folder_copy)
        stop_colls_list.main_folder_changed.connect(cmd)
        v_lay.addWidget(stop_colls_list)

        h_wid_two = QWidget()
        v_lay.addWidget(h_wid_two)
        h_lay_two = UHBoxLayout()
        h_lay_two.setSpacing(15)
        h_wid_two.setLayout(h_lay_two)

        add_btn_two = QPushButton(Lang.add_)
        add_btn_two.setFixedWidth(115)
        h_lay_two.addWidget(add_btn_two)

        coll_folders_label = QLabel(Lang.where_to_look_coll_folder)
        h_lay_two.addWidget(coll_folders_label)

        coll_folders_list = MainFolderItemsWid(main_folder_copy, False)
        cmd = lambda: self.main_folder_changed.emit(main_folder_copy)
        coll_folders_list.main_folder_changed.connect(cmd)
        v_lay.addWidget(coll_folders_list)

        return wid


class AddMainFolderWin(WinSystem):
    new_main_folder = pyqtSignal(object)

    def __init__(self):
        """
        Сигналы: new_main_folder(MainFolder)
        """
        super().__init__()

        self.setWindowTitle(Lang.add_main_folder_title)

        self.setFixedSize(450, 400)
        self.central_layout.setSpacing(10)

        descr_widget = QLabel(Lang.add_main_folder_descr)
        self.central_layout.addWidget(descr_widget)

        self.name_wid = ULineEdit()
        self.name_wid.setPlaceholderText(Lang.set_name_main_folder)
        self.central_layout.addWidget(self.name_wid)


        h_wid_one = QWidget()
        self.central_layout.addWidget(h_wid_one)
        h_lay_one = UHBoxLayout()
        h_lay_one.setSpacing(15)
        h_wid_one.setLayout(h_lay_one)

        add_btn_one = QPushButton(Lang.add_)
        add_btn_one.setFixedWidth(115)
        h_lay_one.addWidget(add_btn_one)

        stop_colls_lbl = QLabel(Lang.sett_stopcolls)
        h_lay_one.addWidget(stop_colls_lbl)

        stop_list_wid = StopList(None, None)
        add_btn_one.clicked.connect(stop_list_wid.add_item_cmd)
        self.central_layout.addWidget(stop_list_wid)

        h_wid_two = QWidget()
        self.central_layout.addWidget(h_wid_two)
        h_lay_two = UHBoxLayout()
        h_lay_two.setSpacing(15)
        h_wid_two.setLayout(h_lay_two)

        add_btn_two = QPushButton(Lang.add_)
        add_btn_two.setFixedWidth(115)
        h_lay_two.addWidget(add_btn_two)

        coll_folders_label = QLabel(Lang.where_to_look_coll_folder)
        h_lay_two.addWidget(coll_folders_label)

        stop_list_wid = MainFoldersPaths(None, None)
        add_btn_two.clicked.connect(stop_list_wid.add_item_cmd)
        self.central_layout.addWidget(stop_list_wid)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = UHBoxLayout()
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        h_lay.addStretch()

        ok_btn = QPushButton(Lang.ok)
        ok_btn.clicked.connect(self.ok_cmd)
        ok_btn.setFixedWidth(90)
        h_lay.addWidget(ok_btn)

        cancel_btn = QPushButton(Lang.cancel)
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setFixedWidth(90)
        h_lay.addWidget(cancel_btn)

        h_lay.addStretch()

        self.central_layout.addWidget

    def ok_cmd(self):
        name_of_main_folder = self.findChild(ULineEdit).text()
        main_folders_paths = self.findChild(MainFoldersPaths).get_items()
        stop_list = self.findChild(StopList).get_items()

        if name_of_main_folder and main_folders_paths:

            new_main_folder = MainFolder(
                name=name_of_main_folder,
                paths=main_folders_paths,
                stop_list=stop_list
            )

            self.new_main_folder.emit(new_main_folder)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd()
        return super().keyPressEvent(a0)
    

class RemoveMainFolderWin(WinSystem):
    del_main_folder = pyqtSignal(object)

    def __init__(self):
        """
        Сигналы: del_main_folder(MainFolder)
        """
        super().__init__()
        self.setWindowTitle(Lang.delete_main_folder)

        self.setFixedSize(330, 300)
        self.central_layout.setSpacing(5)

        list_widget = QListWidget(self)
        list_widget.horizontalScrollBar().setDisabled(True)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.central_layout.addWidget(list_widget)

        for main_folder in MainFolder.list_:
            item = QListWidgetItem(list_widget)
            item.setSizeHint(QSize(self.width(), LIST_ITEM_H))
            label = QLabel(main_folder.name)
            label.setStyleSheet("padding-left: 2px;")
            list_widget.addItem(item)
            list_widget.setItemWidget(item, label)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_lay = UHBoxLayout()
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        h_lay.addStretch()
        self.ok_btn = QPushButton(text=Lang.ok)
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(90)
        h_lay.addWidget(self.ok_btn)

        cancel_btn = QPushButton(text=Lang.cancel)
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.close)
        h_lay.addWidget(cancel_btn)
        h_lay.addStretch()

    def ok_cmd(self):
        list_widget: QListWidget = self.findChild(QListWidget)

        if not list_widget.selectedItems():
            return

        selected_item = list_widget.currentItem()
        if selected_item:
            label: QLabel = list_widget.itemWidget(selected_item)
            text = label.text()
            for main_folder in MainFolder.list_:
                if main_folder.name == text:
                    self.del_main_folder.emit(main_folder)
                    self.deleteLater()
                    break

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd()
        return super().keyPressEvent(a0)


class MainFolderWid(QGroupBox):
    new_main_folder = pyqtSignal(object)
    del_main_folder = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row = QWidget()
        v_lay.addWidget(first_row)

        h_lay = UHBoxLayout()
        h_lay.setSpacing(15)
        first_row.setLayout(h_lay)

        add_btn = QPushButton(Lang.add_)
        add_btn.mouseReleaseEvent = self.add_btn_cmd
        add_btn.setFixedWidth(115)
        h_lay.addWidget(add_btn)

        descr = QLabel(Lang.add_main_folder)
        h_lay.addWidget(descr)

        second_row = QWidget()
        v_lay.addWidget(second_row)

        second_lay = UHBoxLayout()
        second_lay.setSpacing(15)
        second_row.setLayout(second_lay)

        remove_btn = QPushButton(Lang.delete)
        remove_btn.clicked.connect(self.remove_btn_cmd)
        remove_btn.setFixedWidth(115)
        second_lay.addWidget(remove_btn)

        remove_descr = QLabel(Lang.delete_main_folder)
        second_lay.addWidget(remove_descr)

    def add_btn_cmd(self, *args):
        self.win = AddMainFolderWin()
        self.win.new_main_folder.connect(lambda main_folder: self.new_main_folder.emit(main_folder))
        self.win.center_relative_parent(parent=self.window())
        self.win.show()

    def remove_btn_cmd(self, *args):
        self.win = RemoveMainFolderWin()
        self.win.del_main_folder.connect(lambda main_folder: self.del_main_folder.emit(main_folder))
        self.win.center_relative_parent(parent=self.window())
        self.win.show()


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

        context_menu.show_menu()
        return super().contextMenuEvent(ev)

    def copy_text_md(self):
        MainUtils.copy_text(self.selectedText())


class AboutWin(QGroupBox):
    def __init__(self):
        super().__init__()
        h_lay = UHBoxLayout()
        self.setLayout(h_lay)

        icon = QSvgWidget(ICON_SVG)
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(85, 85)
        h_lay.addWidget(icon)

        h_lay.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        h_lay.addWidget(lbl)


class SvgFrame(QFrame):
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

        self.system_theme = SvgFrame(
            os.path.join(Static.images_dir, "system_theme.svg"),
            Lang.theme_auto
        )
        self.dark_theme = SvgFrame(
            os.path.join(Static.images_dir,"dark_theme.svg"),
            Lang.theme_dark
        )
        self.light_theme = SvgFrame(
            os.path.join(Static.images_dir,"light_theme.svg"),
            Lang.theme_light
        )

        for f in (self.system_theme, self.dark_theme, self.light_theme):
            h_lay.addWidget(f)
            self.frames.append(f)
            f.clicked.connect(self.on_frame_clicked)

        if JsonData.dark_mode is None:
            self.set_selected(self.system_theme)
        elif JsonData.dark_mode:
            self.set_selected(self.dark_theme)
        else:
            self.set_selected(self.light_theme)

    def on_frame_clicked(self):
        sender: SvgFrame = self.sender()
        self.set_selected(sender)

        if sender == self.system_theme:
            JsonData.dark_mode = None
        elif sender == self.dark_theme:
            JsonData.dark_mode = True
        elif sender == self.light_theme:
            JsonData.dark_mode = False

        ThemeChanger.init()
        self.theme_changed.emit()

    def set_selected(self, selected_frame: SvgFrame):
        for f in self.frames:
            f.selected(f is selected_frame)


class ScanTimeWid(QGroupBox):
    new_scan_time = pyqtSignal(int)

    def __init__(self):
        """
        Сигналы: new_scan_time(int)
        """
        super().__init__()

        layout = UHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        label = QLabel(Lang.scan_every, self)
        layout.addWidget(label)

        self.spin = QSpinBox(self)
        self.spin.setFixedWidth(90)
        self.spin.setMinimum(1)
        self.spin.setMaximum(60)
        self.spin.setSuffix(f" {Lang.mins}")
        self.spin.setValue(JsonData.scaner_minutes)
        self.spin.valueChanged.connect(self.change_scan_time)
        layout.addWidget(self.spin)

    def change_scan_time(self, value: int):
        self.new_scan_time.emit(value)


class WinSettings(WinSystem):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lang.settings)
        self.new_main_folders: list[MainFolder] = []
        self.del_main_folders: list[MainFolder] = []
        self.changed_main_folders: set[MainFolder] = set()
        self.reset_data = False
        self.new_lang = None
        self.scan_time = None

        self.init_ui()
        self.first_tab()
        self.second_tab()
        self.btns_wid()
        self.setFixedWidth(420)

    def reset_data_cmd(self):
        self.reset_data = True
        self.set_apply_btn()

    def new_lang_cmd(self, value: int):
        self.new_lang = value
        self.set_apply_btn()

    def add_new_main_folder(self, main_folder: MainFolder):
        self.new_main_folders.append(main_folder)
        self.set_apply_btn()

    def del_new_main_folder(self, main_folder: MainFolder):
        self.del_main_folders.append(main_folder)
        self.set_apply_btn()

    def set_scan_time(self, value: int):
        self.scan_time = value
        self.set_apply_btn()

    def main_folder_changed_cmd(self, main_folder_copy: MainFolder):
        self.changed_main_folders.add(main_folder_copy)
        self.set_apply_btn()

    def set_apply_btn(self):
        self.ok_btn.setText(Lang.apply)

    def init_ui(self):
        self.tabs_wid = QTabWidget()
        self.tabs_wid.tabBarClicked.connect(lambda: self.setFocus())
        self.central_layout.addWidget(self.tabs_wid)
        self.central_layout.setContentsMargins(5, 10, 5, 5)
        self.central_layout.setSpacing(10)

    def first_tab(self):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        rebootable_sett = RebootableSettings()
        rebootable_sett.new_lang.connect(lambda value: self.new_lang_cmd(value))
        rebootable_sett.reset_data.connect(lambda: self.reset_data_cmd())
        v_lay.addWidget(rebootable_sett)

        simple_settings = SimpleSettings()
        v_lay.addWidget(simple_settings)

        themes = Themes()
        themes.theme_changed.connect(self.theme_changed.emit)
        v_lay.addWidget(themes)

        about_wid = AboutWin()
        v_lay.addWidget(about_wid)

        v_lay.addStretch()

        self.tabs_wid.addTab(v_wid, Lang.main)

    def second_tab(self):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        main_folder_wid = MainFolderWid()
        add_cmd = lambda main_folder: self.add_new_main_folder(main_folder)
        del_cmd = lambda main_folder: self.del_new_main_folder(main_folder)
        main_folder_wid.new_main_folder.connect(add_cmd)
        main_folder_wid.del_main_folder.connect(del_cmd)

        v_lay.addWidget(main_folder_wid)

        scan_wid = ScanTimeWid()
        scan_wid.new_scan_time.connect(lambda value: self.set_scan_time(value))
        v_lay.addWidget(scan_wid)

        # ДОПИЛИВАТЬ
        main_folder_tab = EditMainFoldersWid()
        cmd = lambda main_folder_copy: self.main_folder_changed_cmd(main_folder_copy)
        main_folder_tab.main_folder_changed.connect(cmd)
        v_lay.addWidget(main_folder_tab)

        v_lay.addStretch()
        self.tabs_wid.addTab(v_wid, Lang.collections)

    def btns_wid(self):
        btns_wid = QWidget()
        btns_layout = UHBoxLayout()
        btns_wid.setLayout(btns_layout)
        self.central_layout.addWidget(btns_wid)

        btns_layout.addStretch(1)

        self.ok_btn = QPushButton(text=Lang.ok)
        self.ok_btn.setFixedWidth(100)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_layout.addWidget(self.ok_btn)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        cancel_btn = QPushButton(text=Lang.cancel)
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.close)
        btns_layout.addWidget(cancel_btn)

        btns_layout.addStretch(1)

    def ok_cmd(self, *args):
        restart_app = False

        if self.new_main_folders:
            restart_app = True
            for i in self.new_main_folders:
                MainFolder.list_.append(i)

        if self.del_main_folders:
            restart_app = True
            for del_main_f in self.del_main_folders:
                for i in MainFolder.list_:
                    if del_main_f.name == i.name:
                        MainFolder.list_.remove(i)

        if self.changed_main_folders:
            for ch_main_folder in self.changed_main_folders:
                for main_folder in MainFolder.list_:
                    if ch_main_folder.name == main_folder.name:
                        ...

        if self.new_lang:
            restart_app = True
            JsonData.lang_ind = self.new_lang

        if self.scan_time:
            restart_app = True
            JsonData.scaner_minutes = self.scan_time

        if self.reset_data:
            shutil.rmtree(Static.APP_SUPPORT_DIR)
            QApplication.quit()
            MainUtils.start_new_app()
        elif restart_app:
            self.hide()
            MainFolder.write_json_data()
            JsonData.write_json_data()
            QApplication.quit()
            MainUtils.start_new_app()
        else:
            self.deleteLater()


    def new_row_list(self, wid: UTextEdit) -> list[str]:
        return[
            i
            for i in wid.toPlainText().split("\n")
            if i
        ]

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
