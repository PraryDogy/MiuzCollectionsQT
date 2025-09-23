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
    tree_click = pyqtSignal(str)
    reveal = pyqtSignal(str)
    restart_scaner = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.last_selection: QModelIndex = None

    def init_ui(self, root_dir: str):

        if not root_dir:
            self.setModel(None)
            return

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

        self.model_.setRootPath(root_dir)
        self.setRootIndex(
            self.proxy.mapFromSource(self.model_.index(root_dir))
        )

    def on_item_click(self, index: QModelIndex):
        if self.last_selection != index:
            self.last_selection = index
            self.tree_click.emit(self.get_path(index))

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


class MfListItem(UListWidgetItem):
    def __init__(self, parent, height = 28, text = None):
        super().__init__(parent, height, text)
        self.mf: Mf = None
    

class MfList(VListWidget):
    mf_view = pyqtSignal(Mf)
    mf_reveal = pyqtSignal(Mf)
    mf_edit = pyqtSignal(Mf)
    mf_new = pyqtSignal()
    restart_scaner = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

    def init_ui(self):
        for i in Mf.list_:
            if i.curr_path:
                true_name = os.path.basename(i.curr_path)
            else:
                true_name = os.path.basename(i.paths[0])
            text = f"{true_name} ({i.name})"
            item = MfListItem(parent=self, text=text)
            item.mf = i
            item.setToolTip(i.name)
            self.addItem(item)

        self._last_mf = Mf.list_[0]
        self.setCurrentRow(0)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(VListWidget.DragDropMode.InternalMove)

    def mouseReleaseEvent(self, e):
        item: MfListItem = self.itemAt(e.pos())
        if not item:
            return

        if e.button() == Qt.MouseButton.LeftButton:
            self.mf_view.emit(item.mf)
            self._last_mf = item.mf

        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        item: MfListItem = self.itemAt(a0.pos())
        if item:

            view_action = QAction(Lng.open[Cfg.lng], menu)
            view_action.triggered.connect(
                lambda: self.mf_view.emit(item.mf)
            )
            menu.addAction(view_action)
            restart_scaner = QAction(Lng.scan_folder[Cfg.lng], menu)
            restart_scaner.triggered.connect(
                lambda: self.restart_scaner.emit()
            )
            menu.addAction(restart_scaner)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(
                lambda: self.mf_reveal.emit(item.mf)
            )
            menu.addAction(reveal)
            menu.addSeparator()
            setup = QAction(Lng.setup[Cfg.lng], menu)
            setup.triggered.connect(
                lambda: self.mf_edit.emit(item.mf)
            )
            menu.addAction(setup)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng], menu)
            new_folder.triggered.connect(
                lambda: self.mf_new.emit()
            )
            menu.addAction(new_folder)
        menu.show_umenu()

    def dropEvent(self, event):
        super().dropEvent(event)  # перемещаем элемент визуально

        # обновляем порядок в Mf.list_ согласно виджету
        new_order = []
        for i in range(self.count()):
            item: MfListItem = self.item(i)
            new_order.append(item.mf)
        Mf.list_ = new_order


class MenuLeft(QTabWidget):
    left_menu_click = pyqtSignal(str)
    path_reveal = pyqtSignal(str)
    restart_scaner = pyqtSignal()
    mf_edit = pyqtSignal(SettingsItem)
    mf_new = pyqtSignal(SettingsItem)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        def mf_view(mf: Mf):
            Mf.current = mf
            self.left_menu_click.emit(mf.curr_path)
            self.tree_wid.init_ui(mf.curr_path)

        def mf_reveal(mf: Mf):
            # такой костыль, потому что в MainWin функция reveal_in_Finder
            # подразумевает reveal только для текущей Mf
            # поэтому мы временно делаем желаемую Mf текущей,
            # а потом возвращаем назад
            old_mf = Mf.current
            Mf.current = mf
            self.path_reveal.emit(mf.curr_path)
            Mf.current = old_mf
  
        def mf_edit(mf: Mf):
            item = SettingsItem()
            item.action_type = item.type_edit_folder
            item.content = mf
            self.mf_edit.emit(item)
            
        def mf_new():
            item = SettingsItem()
            item.action_type = item.type_new_folder
            item.content = str()
            self.mf_new.emit(item) 
        
        self.clear()

        self.mf_list = MfList(self)
        self.mf_list.init_ui()
        self.mf_list.mf_view.connect(
            lambda mf: mf_view(mf)
        )
        self.mf_list.mf_reveal.connect(
            lambda mf: mf_reveal(mf)
        )
        self.mf_list.restart_scaner.connect(
            lambda: self.restart_scaner.emit()
        )
        self.mf_list.mf_edit.connect(
            lambda mf: mf_edit(mf)
        )
        self.mf_list.mf_new.connect(
            lambda: mf_new()
        )

        self.addTab(self.mf_list, Lng.folders[Cfg.lng])

        self.tree_wid = TreeWid()
        self.tree_wid.tree_click.connect(
            lambda abs_path: self.left_menu_click.emit(abs_path)
        )
        self.tree_wid.restart_scaner.connect(
            lambda: self.restart_scaner.emit()
        )
        self.tree_wid.reveal.connect(
            lambda abs_path: self.path_reveal.emit(abs_path)
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
            QTimer.singleShot(0, lambda: self.left_menu_click.emit(mf_path))
            
    def dragEnterEvent(self, a0):
        a0.accept()
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if os.path.isdir(url):
                item = SettingsItem()
                item.action_type = item.type_new_folder
                item.content = url
                self.mf_edit.emit(item)                