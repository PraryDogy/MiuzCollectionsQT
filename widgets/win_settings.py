import os
import subprocess

from PyQt5.QtCore import QModelIndex, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QSpacerItem, QSpinBox, QTabWidget, QWidget)

from base_widgets import ContextCustom, CustomTextEdit, LayoutHor, LayoutVer
from base_widgets.input import ULineEdit
from base_widgets.wins import WinSystem
from cfg import JsonData, Static
from lang import Lang
from main_folder import MainFolder
from paletes import ThemeChanger
from utils.main import MainUtils

NEED_REBOOT = "___need_reboot___"
LIST_ITEM_H = 25
REMOVE_MAIN_FOLDER_NAME = "REMOVE_MAIN_FOLDER_NAME"
ADD_NEW_MAIN_FOLDER = "ADD_NEW_MAIN_FOLDER"
ICON_SVG = os.path.join(Static.images_dir, "icon.svg")

class RebootableSettings(QGroupBox):
    apply = pyqtSignal()

    def __init__(self):
        super().__init__()

        v_lay = LayoutVer()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        first_row_lay = LayoutHor()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.lang_btn = QPushButton(text=Lang._lang_name)
        self.lang_btn.setFixedWidth(115)
        self.lang_btn.clicked.connect(self.lang_btn_cmd)
        first_row_lay.addWidget(self.lang_btn)

        self.lang_label = QLabel(Lang.lang_label)
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        sec_row_lay = LayoutHor()
        sec_row_lay.setSpacing(15)
        sec_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sec_row_wid.setLayout(sec_row_lay)

        self.reset_btn = QPushButton(Lang.reset)
        self.reset_btn.setFixedWidth(115)
        self.reset_btn.clicked.connect(self.reset_btn_cmd)
        sec_row_lay.addWidget(self.reset_btn)

        descr = QLabel(text=Lang.restore_db_descr)
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def cmd_(self, wid: QWidget):
        self.apply.emit()
        setattr(wid, NEED_REBOOT, True)

    def reset_btn_cmd(self, *args):
        self.lang_btn.setDisabled(True)
        self.cmd_(wid=self.reset_btn)

    def lang_btn_cmd(self, *args):
        # костыль но что ж поделать
        if self.lang_btn.text() == "Русский":
            self.lang_btn.setText("English")
        else:
            self.lang_btn.setText("Русский")

        self.reset_btn.setDisabled(True)
        self.cmd_(wid=self.lang_btn)


class SimpleSettings(QGroupBox):
    def __init__(self):
        super().__init__()

        v_lay = LayoutVer()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        v_lay.addWidget(first_row_wid)
        first_row_lay = LayoutHor()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        sec_row_wid = QWidget()
        v_lay.addWidget(sec_row_wid)
        sec_row_lay = LayoutHor()
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


class AddItemWindow(WinSystem):
    clicked_ = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 80)
        self.setWindowTitle(Lang.paste_text)
        self.central_layout.setSpacing(10)

        self.text_edit = ULineEdit()
        self.text_edit.setPlaceholderText(Lang.paste_text)
        self.central_layout.addWidget(self.text_edit)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = LayoutHor()
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
            self.clicked_.emit(text)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd()
        return super().keyPressEvent(a0)


class BaseListWidget(QListWidget):
    changed = pyqtSignal()

    def __init__(self, main_folder: MainFolder, items: list[str]):
        super().__init__()
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.contextMenuEvent = self.list_item_context

        if not main_folder or not items:
            return

        self.main_folder_instance = main_folder

        for i in items:
            item_ = QListWidgetItem(i)
            item_.setSizeHint(QSize(self.width(), LIST_ITEM_H))
            item_.item_name = i
            self.addItem(item_)

    def list_item_context(self, ev):
        menu = ContextCustom(event=ev)

        add_item = QAction(parent=menu, text=Lang.add_)
        add_item.triggered.connect(self.add_item_cmd)
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
        self.takeItem(row)
        self.changed.emit()

    def get_items(self):
        return [
            self.item(i).text()
            for i in range(self.count())
        ]

    def add_item_cmd(self):
        win = AddItemWindow()
        win.clicked_.connect(self.add_item_fin)
        win.center_relative_parent(parent=self.window())
        win.show()

    def add_item_fin(self, text: str):
        item_ = QListWidgetItem(text)
        item_.setSizeHint(QSize(self.width(), LIST_ITEM_H))
        item_.item_name = text
        self.addItem(item_)
        self.changed.emit()


class StopList(BaseListWidget):
    def __init__(self, main_folder, items):
        super().__init__(main_folder, items)
        self.main_folder_instance = main_folder


class MainFoldersPaths(BaseListWidget):
    def __init__(self, main_folder, items):
        super().__init__(main_folder, items)
        self.main_folder_instance = main_folder


class TabsWidget(QTabWidget):
    need_lock_widgets = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stop_colls_wid: dict[int, CustomTextEdit] = {}
        self.coll_folders_wid: dict[int, CustomTextEdit] = {}

        for main_folder in MainFolder.list_:
            wid = self.tab_ui(main_folder=main_folder)
            self.addTab(wid, main_folder.name)

        current_index = MainFolder.list_.index(MainFolder.current)
        self.setCurrentIndex(current_index)

    def tab_ui(self, main_folder: MainFolder):
        wid = QWidget()
        v_lay = LayoutVer()
        v_lay.setSpacing(10)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        wid.setLayout(v_lay)

        h_wid_one = QWidget()
        v_lay.addWidget(h_wid_one)
        h_lay_one = LayoutHor()
        h_lay_one.setSpacing(15)
        h_wid_one.setLayout(h_lay_one)

        add_btn_one = QPushButton(Lang.add_)
        add_btn_one.setFixedWidth(115)
        h_lay_one.addWidget(add_btn_one)

        stop_colls_lbl = QLabel(Lang.sett_stopcolls)
        h_lay_one.addWidget(stop_colls_lbl)

        stop_colls_list = StopList(main_folder, main_folder.stop_list)
        stop_colls_list.changed.connect(self.list_changed)
        add_btn_one.clicked.connect(stop_colls_list.add_item_cmd)
        v_lay.addWidget(stop_colls_list)

        h_wid_two = QWidget()
        v_lay.addWidget(h_wid_two)
        h_lay_two = LayoutHor()
        h_lay_two.setSpacing(15)
        h_wid_two.setLayout(h_lay_two)

        add_btn_two = QPushButton(Lang.add_)
        add_btn_two.setFixedWidth(115)
        h_lay_two.addWidget(add_btn_two)

        coll_folders_label = QLabel(Lang.where_to_look_coll_folder)
        h_lay_two.addWidget(coll_folders_label)

        coll_folders_list = MainFoldersPaths(main_folder, main_folder.paths)
        coll_folders_list.changed.connect(self.list_changed)
        add_btn_two.clicked.connect(coll_folders_list.add_item_cmd)
        v_lay.addWidget(coll_folders_list)

        return wid
    
    def list_changed(self):
        # сигнал нужен, чтобы остальные виджеты окна настроек были заблокированы
        self.need_lock_widgets.emit()

        # аттрибут нужен, чтобы при нажатии на "ок" в главном окне настроек
        # произошла перезагрузка приложения
        setattr(self, NEED_REBOOT, True)


class AddMainFolderWin(WinSystem):
    ok_pressed = pyqtSignal(object)

    def __init__(self):
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
        h_lay_one = LayoutHor()
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
        h_lay_two = LayoutHor()
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

        h_lay = LayoutHor()
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

            self.ok_pressed.emit(new_main_folder)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd()
        return super().keyPressEvent(a0)
    

class RemoveWin(WinSystem):
    ok_pressed = pyqtSignal(str)

    def __init__(self):
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
        h_lay = LayoutHor()
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
                    self.ok_pressed.emit(text)
                    self.deleteLater()
                    break

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd()
        return super().keyPressEvent(a0)


class MainFolderWid(QGroupBox):
    need_lock_widgets = pyqtSignal()

    def __init__(self):
        super().__init__()

        v_lay = LayoutVer()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        first_row = QWidget()
        v_lay.addWidget(first_row)

        h_lay = LayoutHor()
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

        second_lay = LayoutHor()
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

        # аттрибут нужен, чтобы при нажатии на "ок" в главном окне настроек
        # произошла перезагрузка приложения
        self.win.ok_pressed.connect(lambda obj: setattr(self, NEED_REBOOT, True))
        self.win.ok_pressed.connect(lambda obj: setattr(self, ADD_NEW_MAIN_FOLDER, obj))
        # сигнал нужен, чтобы при нажатии на "ок" в окне AddMainFolderWin
        # остальные виджеты окна настроек были заблокированы
        self.win.ok_pressed.connect(self.need_lock_widgets.emit)
        self.win.center_relative_parent(parent=self.window())
        self.win.show()

    def remove_btn_cmd(self, *args):
        self.win = RemoveWin()

        # аттрибут нужен, чтобы при нажатии на "ок" в главном окне настроек
        # произошла перезагрузка приложения
        self.win.ok_pressed.connect(lambda text: setattr(self, NEED_REBOOT, True))
        self.win.ok_pressed.connect(lambda text: setattr(self, REMOVE_MAIN_FOLDER_NAME, text))

        # сигнал нужен, чтобы при нажатии на "ок" в окне AddMainFolderWin
        # остальные виджеты окна настроек были заблокированы
        self.win.ok_pressed.connect(self.need_lock_widgets.emit)
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
        context_menu = ContextCustom(ev)

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
        h_lay = LayoutHor()
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
        v_lay = LayoutVer()
        self.setLayout(v_lay)

        self.svg_container = QFrame()
        self.svg_container.setObjectName("svg_container")
        self.svg_container.setStyleSheet(self.regular_style())
        v_lay.addWidget(self.svg_container)

        svg_lay = LayoutVer()
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
        h_lay = LayoutHor()
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

        ThemeChanger.start()
        self.theme_changed.emit()

    def set_selected(self, selected_frame: SvgFrame):
        for f in self.frames:
            f.selected(f is selected_frame)


class ScanTime(QGroupBox):
    def __init__(self):
        super().__init__()

        layout = LayoutHor(self)
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
        JsonData.scaner_minutes = value


class WinSettings(WinSystem):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lang.settings)

        self.init_ui()
        self.first_tab()
        self.second_tab()
        self.btns_wid()
        self.setFixedWidth(420)

        self.scaner_minutes = JsonData.scaner_minutes

    def init_ui(self):
        self.tabs_wid = QTabWidget()
        self.tabs_wid.tabBarClicked.connect(lambda: self.setFocus())
        self.central_layout.addWidget(self.tabs_wid)
        self.central_layout.setContentsMargins(5, 10, 5, 5)
        self.central_layout.setSpacing(10)

    def first_tab(self):
        v_wid = QWidget()
        v_lay = LayoutVer()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        rebootable_settings = RebootableSettings()
        rebootable_settings.apply.connect(self.lock_widgets)
        v_lay.addWidget(rebootable_settings)

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
        v_lay = LayoutVer()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        add_main_folder = MainFolderWid()
        add_main_folder.need_lock_widgets.connect(self.lock_widgets)
        v_lay.addWidget(add_main_folder)

        scan_wid = ScanTime()
        v_lay.addWidget(scan_wid)

        main_folder_tab = TabsWidget()
        main_folder_tab.need_lock_widgets.connect(self.lock_widgets)
        v_lay.addWidget(main_folder_tab)

        v_lay.addStretch()
        self.tabs_wid.addTab(v_wid, Lang.collections)

    def btns_wid(self):
        btns_wid = QWidget()
        btns_layout = LayoutHor()
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

    def lock_widgets(self, *args):
        self.ok_btn.setText(Lang.apply)

    def ok_cmd(self, *args):
        rebootable = self.findChild(RebootableSettings)
        main_folder_tab = self.findChild(TabsWidget)
        main_folder_wid = self.findChild(MainFolderWid)

        if self.scaner_minutes != JsonData.scaner_minutes:
            JsonData.write_json_data()

        if hasattr(rebootable.reset_btn, NEED_REBOOT):
            JsonData.write_json_data()
            QApplication.quit()
            MainUtils.rm_rf(folder_path=Static.APP_SUPPORT_DIR)
            MainUtils.start_new_app()

        elif hasattr(rebootable.lang_btn, NEED_REBOOT):
            JsonData.lang_ind += 1
            Lang.init()
            JsonData.write_json_data()
            QApplication.quit()
            MainUtils.start_new_app()

        elif hasattr(main_folder_wid, NEED_REBOOT):

            if hasattr(main_folder_wid, REMOVE_MAIN_FOLDER_NAME):
                for i in MainFolder.list_:
                    if i.name == getattr(main_folder_wid, REMOVE_MAIN_FOLDER_NAME):
                        MainFolder.list_.remove(i)

            elif hasattr(main_folder_wid, ADD_NEW_MAIN_FOLDER):
                MainFolder.list_.append(getattr(main_folder_wid, ADD_NEW_MAIN_FOLDER))

            JsonData.write_json_data()
            QApplication.quit()
            MainUtils.start_new_app()

        elif hasattr(main_folder_tab, NEED_REBOOT):
            for i in self.findChildren(MainFoldersPaths):
                i.main_folder_instance.paths = i.get_items()

            for i in self.findChildren(StopList):
                i.main_folder_instance.stop_list = i.get_items()

            JsonData.write_json_data()
            QApplication.quit()
            MainUtils.start_new_app()

        self.deleteLater()

    def new_row_list(self, wid: CustomTextEdit) -> list[str]:
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
