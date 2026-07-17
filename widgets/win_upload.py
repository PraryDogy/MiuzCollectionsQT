import os
import re

from PyQt6.QtCore import QDir, Qt, QTimer, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QFileSystemModel, QIcon, QAction
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QListWidget,
                             QListWidgetItem, QSplitter, QTreeView,
                             QVBoxLayout, QWidget, QMenu)

from cfg import Cfg, Static
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import ImgUtils, SharedUtils

from ._base_widgets import RowArrowWidget, UMainWidget, UPushButton


class LetterFirstProxyModel(QSortFilterProxyModel):
    """Кастомный прокси для гибкой сортировки папок."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Флаг режима сортировки: True — по первой букве, False — стандартная
        self.letter_only_mode = True

    def lessThan(self, left, right):
        left_name = self.sourceModel().data(left)
        right_name = self.sourceModel().data(right)
        
        if not isinstance(left_name, str): left_name = ""
        if not isinstance(right_name, str): right_name = ""
        
        if self.letter_only_mode:
            # Сортировка А-Я: удаляем любые символы в начале, кроме букв
            left_clean = re.sub(r"^[^a-zA-Zа-яА-ЯёЁ]+", "", left_name).lower()
            right_clean = re.sub(r"^[^a-zA-Zа-яА-ЯёЁ]+", "", right_name).lower()
            
            if not left_clean: left_clean = left_name.lower()
            if not right_clean: right_clean = right_name.lower()
            
            return left_clean < right_clean
        else:
            # Стандартная сортировка ОС (регистронезависимая)
            return left_name.lower() < right_name.lower()


class CustomTreeView(QTreeView):
    """Кастомное дерево с контекстным меню для переключения режимов сортировки."""
    def __init__(self, proxy_model: LetterFirstProxyModel, parent=None):
        super().__init__(parent)
        self.proxy_model = proxy_model
        
        self.setIndentation(10)
        self.header().hide()
        self.setModel(self.proxy_model)
        self.setSortingEnabled(True)
        
        # Задаем контекстное меню по умолчанию через событие
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # Создаем действия (Actions)
        standard_sort_action = QAction(Lng.sort_standart[Cfg.lng_index], self)
        letter_sort_action = QAction(Lng.sort_alphabet[Cfg.lng_index], self)
        
        # Добавляем галочки для наглядности текущего режима
        standard_sort_action.setCheckable(True)
        letter_sort_action.setCheckable(True)
        
        if self.proxy_model.letter_only_mode:
            letter_sort_action.setChecked(True)
        else:
            standard_sort_action.setChecked(True)
            
        # Подключаем слоты
        standard_sort_action.triggered.connect(lambda: self.set_sorting_mode(False))
        letter_sort_action.triggered.connect(lambda: self.set_sorting_mode(True))
        
        menu.addAction(standard_sort_action)
        menu.addAction(letter_sort_action)
        
        menu.exec(event.globalPos())

    def set_sorting_mode(self, letter_only: bool):
        if self.proxy_model.letter_only_mode != letter_only:
            self.proxy_model.letter_only_mode = letter_only
            # Принудительно заставляем модель инвалидировать кэш и пересортировать дерево
            self.proxy_model.invalidate()
            self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)


class UploadWin(UMainWidget):
    ok_clicked = pyqtSignal(str)
    img_icon_path = os.path.join(Static.internal_images, "img.svg")

    def __init__(self, mf: Mf, current_dir: str, files_to_copy: list[str]):
        super().__init__()
        self.setWindowTitle(Lng.upload_in[Cfg.lng_index])
        self.resize(700, 500)

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

        # Инициализируем прокси-модель
        self.proxy_model = LetterFirstProxyModel()
        self.proxy_model.setSourceModel(self.file_model)

        left_wid = QGroupBox()
        splitter.addWidget(left_wid)
        left_layout = QVBoxLayout(left_wid)
        left_layout.setContentsMargins(1, 10, 1, 1)
        left_layout.setSpacing(0)

        # Используем наш кастомный TreeView вместо стандартного
        self.tree_view = CustomTreeView(self.proxy_model)
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
