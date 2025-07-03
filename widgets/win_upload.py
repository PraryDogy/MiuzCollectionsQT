
import os

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QLabel, QListWidget, QWidget

from cfg import Dynamic, Static
from system.lang import Lang
from system.main_folder import MainFolder

from ._base_widgets import UHBoxLayout, UListWidgetItem, WinSystem
from .menu_left import CollectionBtn, MenuLeft


class WinUpload(WinSystem):
    h_ = 30
    finished_ = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lang.title_downloads)
        self.resize(Static.MENU_LEFT_WIDTH, Dynamic.root_g.get("ah"))
        self.current_submenu: QListWidget = None
        self.coll_path: str = None

        self.h_wid = QWidget()
        self.central_layout.addWidget(self.h_wid)

        self.h_lay = UHBoxLayout()
        self.h_lay.setSpacing(10)
        self.h_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.h_wid.setLayout(self.h_lay)

        self.menu_left = MenuLeft()
        self.menu_left.tabBarClicked.disconnect()
        self.menu_left.tabBarClicked.connect(self.tab_bar_cmd)
        self.h_lay.addWidget(self.menu_left)
        self.check_coll_btns()

    def check_coll_btns(self):
        any_tab = self.menu_left.menu_tabs_list[0]
        if len(any_tab.coll_btns) == 0:
            QTimer.singleShot(300, self.check_coll_btns)
        else:
            self.setup_coll_btns()

    def setup_coll_btns(self):
        for menu in self.menu_left.menu_tabs_list:

            disabled_btns = menu.coll_btns[:3]
            coll_btns = menu.coll_btns[3:]
            
            for i in disabled_btns:
                i.setDisabled(True)

            for i in coll_btns:
                i.pressed_.disconnect()
                i.main_folder_index = menu.main_folder_index
                cmd_ = lambda coll_btn=i: self.coll_btn_cmd(coll_btn=coll_btn)
                i.pressed_.connect(cmd_)

    def coll_btn_cmd(self, coll_btn: CollectionBtn):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            self.coll_path = os.path.join(main_folder_path, coll_btn.coll_name)
            # поправка на корневой каталог
            # может получиться путь/к/коллекциям/коллекциям
            if coll_btn.coll_name == os.path.basename(main_folder_path):
                self.coll_path = main_folder_path
            subfolders: list[os.DirEntry] = [
                i
                for i in os.scandir(self.coll_path)
                if i.is_dir()
            ]
            self.create_submenu(subfolders=subfolders)

    def del_submenu(self):
        if self.current_submenu is not None:
            self.current_submenu.deleteLater()
            self.current_submenu = None

    def tab_bar_cmd(self, index: int):
        self.del_submenu()
        self.menu_left.setCurrentIndex(index)
        QTimer.singleShot(100, lambda: self.resize(Static.MENU_LEFT_WIDTH, self.height()))

    def create_submenu(self, subfolders: list[os.DirEntry]):
        
        self.resize(Static.MENU_LEFT_WIDTH * 2, self.height())

        self.del_submenu()
        self.current_submenu = QListWidget()
        self.current_submenu.horizontalScrollBar().setDisabled(True)
        self.current_submenu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.h_lay.addWidget(self.current_submenu)

        self.current_submenu.setFixedHeight(self.current_submenu.height() - 10)
        self.current_submenu.move(self.current_submenu.x(), self.current_submenu.y() + 5)

        wid = QLabel(os.path.basename(self.coll_path))
        wid.setStyleSheet("padding-left: 5px;")
        cmd_ = lambda e, : self.list_widget_item_cmd(entry=self.coll_path)
        wid.mouseReleaseEvent = cmd_
        list_item = UListWidgetItem(self.current_submenu)
        self.current_submenu.addItem(list_item)
        self.current_submenu.setItemWidget(list_item, wid)

        for entry_ in subfolders:

            wid = QLabel(entry_.name)
            wid.setStyleSheet("padding-left: 5px;")
            wid.mouseReleaseEvent = lambda e, entry=entry_: self.list_widget_item_cmd(entry=entry)
            list_item = UListWidgetItem(self.current_submenu)
            self.current_submenu.addItem(list_item)
            self.current_submenu.setItemWidget(list_item, wid)

    def list_widget_item_cmd(self, entry: os.DirEntry | str):
        if isinstance(entry, str):
            dest = entry
        else:
            dest = entry.path

        self.finished_.emit(dest)
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)