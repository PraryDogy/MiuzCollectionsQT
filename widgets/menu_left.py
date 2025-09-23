import os
import re
import subprocess

from PyQt5.QtCore import (QDir, QModelIndex, QSize, QSortFilterProxyModel, Qt,
                          QTimer, pyqtSignal)
from PyQt5.QtWidgets import (QAction, QFileSystemModel, QHeaderView,
                             QStyledItemDelegate, QTabWidget, QTreeView)

from cfg import Cfg, Dynamic, Static
from system.lang import Lng
from system.main_folder import Mf
from system.utils import Utils

from ._base_widgets import SettingsItem, UListWidgetItem, UMenu, VListWidget


class CustomSortProxy(QSortFilterProxyModel):
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        left_name = self.normalize_name(left.data())
        right_name = self.normalize_name(right.data())
        return left_name < right_name

    def normalize_name(self, name: str) -> str:
        # убираем ведущие цифры и пробелы
        return re.sub(r"^[\d\s]+", "", name).lower()


class RowHeightDelegate(QStyledItemDelegate):
    def __init__(self, height: int = 28, parent=None):
        super().__init__(parent)
        self._height = height

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width(), self._height)
    

class TreeWid(QTreeView):
    reload_thumbnails = pyqtSignal(str)
    reveal = pyqtSignal(str)
    restart_scaner = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.last_selection: QModelIndex = None

        self.model_ = QFileSystemModel()
        self.model_.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)

        # proxy для сортировки (наш кастомный)
        self.proxy = CustomSortProxy()
        self.proxy.setSourceModel(self.model_)

        self.setModel(self.proxy)
        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        # показывать только первую колонку
        for col in range(1, self.model_.columnCount()):
            self.setColumnHidden(col, True)

        # отключить горизонтальный скролл
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self.setItemDelegate(RowHeightDelegate(parent=self))

        self.clicked.connect(self.on_item_click)

    def init_ui(self, root_dir: str):
        self.model_.setRootPath(root_dir)
        self.setRootIndex(self.proxy.mapFromSource(self.model_.index(root_dir)))

    def on_item_click(self, index: QModelIndex):
        if self.last_selection != index:
            self.last_selection = index
            self.reload_thumbnails.emit(self.get_path(index))

    def get_path(self, index: QModelIndex):
        source_index = self.proxy.mapToSource(index)
        return self.model_.filePath(source_index)

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        menu = UMenu(event)

        # Открыть
        view_action = QAction(Lng.open[Cfg.lng], menu)
        view_action.triggered.connect(
            lambda: self.on_item_click(index)
        )
        menu.addAction(view_action)

        # Перезапустить сканер
        restart_action = QAction(Lng.scan_folder[Cfg.lng], menu)
        restart_action.triggered.connect(
            lambda: self.restart_scaner.emit()
        )
        menu.addAction(restart_action)

        menu.addSeparator()

        # Показать в проводнике / Finder
        reveal_action = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
        reveal_action.triggered.connect(
            lambda: self.reveal.emit(self.get_path(index))
        )
        menu.addAction(reveal_action)

        menu.show_umenu()

        super().contextMenuEvent(event)


class MainFolerListItem(UListWidgetItem):
    def __init__(self, parent, height = 28, text = None):
        super().__init__(parent, height, text)
        self.mf: Mf = None
    

class MfList(VListWidget):
    open_mf = pyqtSignal(Mf)
    no_connection = pyqtSignal(Mf)
    setup_mf = pyqtSignal(Mf)
    setup_new_folder = pyqtSignal()
    update_grid = pyqtSignal()
    restart_scaner = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

        for i in Mf.list_:
            if i.curr_path:
                true_name = os.path.basename(i.curr_path)
            else:
                true_name = os.path.basename(i.paths[0])
            text = f"{true_name} ({i.name})"
            item = MainFolerListItem(parent=self, text=text)
            item.mf = i
            item.setToolTip(i.name)
            self.addItem(item)

        self._last_mf = Mf.list_[0]
        self.setCurrentRow(0)

    @staticmethod
    def with_conn(fn):
        def wrapper(self: "MfList", item: MainFolerListItem):
            mf = item.mf
            path = mf.get_curr_path()
            if path:
                return fn(self, item, path, mf)
            else:
                self.no_connection.emit(mf)
        return wrapper

    @with_conn
    def view_cmd(self, item, path, mf):
        self.open_mf.emit(mf)

    @with_conn
    def update_grid_cmd(self, item, path, mf):
        self.update_grid.emit()

    @with_conn
    def reveal_cmd(self, item, path, mf):
        subprocess.Popen(["open", path])

    def mouseReleaseEvent(self, e):
        item: MainFolerListItem = self.itemAt(e.pos())
        if not item:
            return

        if e.button() == Qt.MouseButton.LeftButton:
            self.view_cmd(item)
            self._last_mf = item.mf

        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        item = self.itemAt(a0.pos())
        if item:
            open = QAction(Lng.open[Cfg.lng], menu)
            open.triggered.connect(lambda: self.view_cmd(item))
            menu.addAction(open)
            update_grid = QAction(Lng.update_grid[Cfg.lng], menu)
            update_grid.triggered.connect(lambda: self.update_grid_cmd(item))
            menu.addAction(update_grid)
            restart_scaner = QAction(Lng.scan_folder[Cfg.lng], menu)
            restart_scaner.triggered.connect(self.restart_scaner.emit)
            menu.addAction(restart_scaner)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(lambda: self.reveal_cmd(item))
            menu.addAction(reveal)
            menu.addSeparator()
            setup = QAction(Lng.setup[Cfg.lng], menu)
            setup.triggered.connect(lambda: self.setup_mf.emit(item.mf))
            menu.addAction(setup)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng], menu)
            new_folder.triggered.connect(self.setup_new_folder.emit)
            menu.addAction(new_folder)
        menu.show_umenu()


class MenuLeft(QTabWidget):
    reload_thumbnails = pyqtSignal(str)
    reveal = pyqtSignal(str)
    restart_scaner = pyqtSignal()


    no_connection = pyqtSignal(Mf)
    edit_mf = pyqtSignal(SettingsItem)
    setup_new_mf = pyqtSignal(SettingsItem)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def mf_clicked(self, mf: Mf):
        Mf.current = mf
        mf_path = Mf.current.get_curr_path()
        if mf_path:
            Dynamic.current_dir = mf_path
            Dynamic.thumbnails_count = 0
            self.reload_thumbnails_cmd(mf_path)
            self.tree_wid.init_ui(mf_path)
        else:
            self.no_connection.emit()
        
    def init_ui(self):
        
        def edit_mf(mf: Mf):
            item = SettingsItem()
            item.action_type = item.type_edit_folder
            item.content = mf
            self.edit_mf.emit(item)
            
        def setup_new_folder():
            item = SettingsItem()
            item.action_type = item.type_new_folder
            item.content = ""
            self.setup_new_mf.emit(item) 
        
        self.clear()

        mfs = MfList(self)
        mfs.open_mf.connect(self.mf_clicked)
        mfs.no_connection.connect(self.no_connection.emit)
        mfs.setup_mf.connect(edit_mf)
        mfs.setup_new_folder.connect(setup_new_folder)
        mfs.restart_scaner.connect(self.restart_scaner.emit)
        self.addTab(mfs, Lng.folders[Cfg.lng])

        self.tree_wid = TreeWid()
        self.tree_wid.reload_thumbnails.connect(
            lambda abs_path: self.reload_thumbnails.emit(abs_path)
        )
        self.tree_wid.restart_scaner.connect(
            lambda: self.restart_scaner.emit()
        )
        self.tree_wid.reveal.connect(
            lambda abs_path: self.reveal.emit(abs_path)
        )
        self.tree_wid.restart_scaner.connect(
            lambda: self.restart_scaner.emit()
        )
        self.addTab(self.tree_wid, Lng.images[Cfg.lng])
        
        mf_path = Mf.current.get_curr_path()
        if mf_path:
            self.tree_wid.init_ui(mf_path)
            self.setCurrentIndex(1)
            # без таймера не срабатывает
            QTimer.singleShot(0, lambda: self.reload_thumbnails.emit(mf_path))
            
    def dragEnterEvent(self, a0):
        a0.accept()
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if os.path.isdir(url):
                item = SettingsItem()
                item.action_type = item.type_new_folder
                item.content = url
                self.edit_mf.emit(item)                