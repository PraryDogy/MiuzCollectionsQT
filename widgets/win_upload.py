import os
import re

from PyQt6.QtCore import QDir, Qt, QTimer, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QListWidget,
                             QListWidgetItem, QSplitter, QTreeView,
                             QVBoxLayout, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import ImgUtils, SharedUtils

from ._base_widgets import RowArrowWidget, UMainWidget, UPushButton


class LetterFirstProxyModel(QSortFilterProxyModel):
    """Кастомный прокси для сортировки папок строго по первой букве."""
    def lessThan(self, left, right):
        left_name = self.sourceModel().data(left)
        right_name = self.sourceModel().data(right)
        
        if not isinstance(left_name, str): left_name = ""
        if not isinstance(right_name, str): right_name = ""
        
        # Регулярное выражение удаляет любые символы в начале, кроме букв (включая кириллицу)
        left_clean = re.sub(r"^[^a-zA-Zа-яА-ЯёЁ]+", "", left_name).lower()
        right_clean = re.sub(r"^[^a-zA-Zа-яА-ЯёЁ]+", "", right_name).lower()
        
        if not left_clean: left_clean = left_name.lower()
        if not right_clean: right_clean = right_name.lower()
        
        return left_clean < right_clean


class UploadWin(UMainWidget):
    ok_clicked = pyqtSignal(str)
    img_icon_path = os.path.join(Static.internal_images, "img.svg")

    def __init__(self, mf: Mf, current_dir: str, files_to_copy: list[str]):
        super().__init__()
        self.setWindowTitle(Lng.upload_in[Cfg.lng_index])
        self.resize(700, 500)
        # self.setAcceptDrops(True)

        self.root_dir = mf.mf_current_path
        self.dest = os.path.join(
            mf.mf_current_path,
            current_dir.strip(os.sep)
        ).rstrip(os.sep)
        self.files_to_copy = files_to_copy

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(15)
        self.central_layout.addWidget(splitter)

        # Инициализируем стандартную файловую модель папок
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        self.file_model.setRootPath(self.root_dir)

        # Используем наш кастомный прокси-класс вместо стандартного
        self.proxy_model = LetterFirstProxyModel()
        self.proxy_model.setSourceModel(self.file_model)

        left_wid = QGroupBox()
        splitter.addWidget(left_wid)
        left_layout = QVBoxLayout(left_wid)
        left_layout.setContentsMargins(1, 10, 1, 1)
        left_layout.setSpacing(0)

        self.tree_view = QTreeView()
        self.tree_view.setIndentation(10)
        self.tree_view.header().hide()
        
        # Устанавливаем прокси-модель в дерево и активируем сортировку
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setSortingEnabled(True)
        self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)
        
        # Задаем корень отображения на уровень выше
        parent_dir_src_idx = self.file_model.index(os.path.dirname(self.root_dir))
        parent_dir_proxy_idx = self.proxy_model.mapFromSource(parent_dir_src_idx)
        self.tree_view.setRootIndex(parent_dir_proxy_idx)
        
        # Подключаем скрытие соседей и автораскрытие целевой папки
        self.file_model.directoryLoaded.connect(self._hide_neighbor_folders)
        self.file_model.directoryLoaded.connect(self._expand_to_target)
        self.tree_view.clicked.connect(self.on_folder_selected)
        
        for i in range(1, 4):
            self.tree_view.setColumnHidden(i, True)

        left_layout.addWidget(self.tree_view)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        group_one = QGroupBox()
        group_one_layout = QVBoxLayout(group_one)
        group_one_layout.setContentsMargins(5, 0, 5, 0)
        group_one_layout.setSpacing(0)
        right_layout.addWidget(group_one)

        title = RowArrowWidget(Lng.upload_list[Cfg.lng_index])
        title.hide_arrow()
        title.hide_sep()
        group_one_layout.addWidget(title)

        self.list_widget = QListWidget()
        group_one_layout.addWidget(self.list_widget)
        
        self.total_files_widget = RowArrowWidget("")
        self.total_files_widget.hide_arrow()
        group_one_layout.addWidget(self.total_files_widget)

        self.total_size_widget = RowArrowWidget("")
        self.total_size_widget.hide_arrow()
        group_one_layout.addWidget(self.total_size_widget)

        self.lbl_target_dir = RowArrowWidget("")
        self.lbl_target_dir.hide_arrow()
        self.lbl_target_dir.hide_sep()
        self.update_target_dir_label()
        group_one_layout.addWidget(self.lbl_target_dir)
        
        splitter.addWidget(right_widget)

        # Левое дерево строго 210 пикселей при старте
        splitter.setSizes([210, self.width() - 210])

        right_layout.addStretch()

        btn_layout = QHBoxLayout()
        right_layout.addLayout(btn_layout)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        btn_layout.addStretch()

        self.btn_ok = UPushButton(Lng.ok[Cfg.lng_index])
        self.btn_ok.clicked.connect(self.ok_clicked_cmd)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = UPushButton(Lng.cancel[Cfg.lng_index])
        self.btn_cancel.clicked.connect(self.deleteLater)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.init_list()

    def init_list(self):
        total_size = 0
        self.list_widget.clear()

        for file_path in self.files_to_copy:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setIcon(QIcon(self.img_icon_path))
            item.setToolTip(file_path)
            self.list_widget.addItem(item)
            total_size += os.path.getsize(file_path)    

        txt = f"{Lng.total_files[Cfg.lng_index]}: {len(self.files_to_copy)}"
        self.total_files_widget.text_widget.setText(txt)

        size_mb = SharedUtils.get_f_size(total_size)
        text = f"{Lng.file_size[Cfg.lng_index]}: {size_mb}"
        self.total_size_widget.text_widget.setText(text)

    def _hide_neighbor_folders(self, loaded_path):
        """Скрывает все папки на верхнем уровне интерфейса, кроме self.root_dir."""
        if os.path.normpath(loaded_path) == os.path.normpath(os.path.dirname(self.root_dir)):
            parent_src_idx = self.file_model.index(loaded_path)
            parent_proxy_idx = self.proxy_model.mapFromSource(parent_src_idx)
            
            for row in range(self.proxy_model.rowCount(parent_proxy_idx)):
                child_proxy_idx = self.proxy_model.index(row, 0, parent_proxy_idx)
                child_src_idx = self.proxy_model.mapToSource(child_proxy_idx)
                child_path = self.file_model.filePath(child_src_idx)
                
                if os.path.normpath(child_path) != os.path.normpath(self.root_dir):
                    self.tree_view.setRowHidden(row, parent_proxy_idx, True)

    def _expand_to_target(self):
        def cmd():
            root_src_idx = self.file_model.index(self.root_dir)
            dest_src_idx = self.file_model.index(self.dest)
            
            root_proxy_idx = self.proxy_model.mapFromSource(root_src_idx)
            dest_proxy_idx = self.proxy_model.mapFromSource(dest_src_idx)
            
            self.tree_view.expand(root_proxy_idx)
            self.tree_view.expand(dest_proxy_idx)
            self.tree_view.setCurrentIndex(dest_proxy_idx)
            self.tree_view.scrollTo(dest_proxy_idx, QTreeView.ScrollHint.PositionAtCenter)  

        QTimer.singleShot(100, cmd)

    def update_target_dir_label(self):
        folder_name = os.path.basename(self.dest) 
        self.lbl_target_dir.text_widget.setText(
            f"{Lng.dest_folder[Cfg.lng_index]}: {folder_name}"
        )

    def ok_clicked_cmd(self):
        if self.files_to_copy:
            self.ok_clicked.emit(self.dest)
        else:
            self.deleteLater()

    def on_folder_selected(self, proxy_index):
        src_index = self.proxy_model.mapToSource(proxy_index)
        if self.file_model.isDir(src_index):
            self.dest = self.file_model.filePath(src_index)
            self.update_target_dir_label()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.ok_clicked_cmd()
        return super().keyPressEvent(a0)

    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            urls = [
                i
                for i in a0.mimeData().urls()
                if i.toLocalFile().endswith(ImgUtils.ext_all)
                and
                os.path.isfile(i.toLocalFile())
            ]
        return super().dropEvent(a0)
