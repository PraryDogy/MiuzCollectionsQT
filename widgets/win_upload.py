import os
import sys

from PyQt6.QtCore import QDir, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QFrame,
                             QGroupBox, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMainWindow, QPushButton,
                             QSpacerItem, QSplitter, QTreeView, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import RowArrowWidget, SmallBtn, UHBoxLayout, UMainWindow


class UploadWin(UMainWindow):
    ok_clicked = pyqtSignal(str)

    def __init__(self, mf: Mf, current_dir: str, dropped_files: list[str]):
        super().__init__()
        self.setWindowTitle("Подтверждение выгрузки")
        self.resize(700, 500)

        # Приводим все пути к абсолютному виду
        self.root_dir = mf.mf_current_path
        self.dest = os.path.join(
            mf.mf_current_path,
            current_dir.strip(os.sep)
        ).rstrip(os.sep)
        self.target_files = dropped_files

        # Главный сплиттер (Разделяет дерево и правое превью)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(15)
        self.central_layout.addWidget(splitter)

        # === ЛЕВАЯ ПАНЕЛЬ: Куда загружаем ===
        self.tree_view = QTreeView()
        self.tree_view.header().hide()  # Скрываем имя колонки
        
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)

        
        # Модель инициализируем от корня ограничителя, чтобы она читала только его
        self.file_model.setRootPath(self.root_dir)
        self.tree_view.setModel(self.file_model)
        
        # Скрываем лишние колонки
        for i in range(1, 4):
            self.tree_view.setColumnHidden(i, True)
            
        # ОГРАНИЧЕНИЕ: Пользователь заперт внутри root_dir (например, Downloads)
        root_index = self.file_model.index(self.root_dir)
        self.tree_view.setRootIndex(root_index)
        
        # ПОШАГОВОЕ РАСКРЫТИЕ: Подключаемся к загрузке директорий
        self.file_model.directoryLoaded.connect(self._expand_to_target)
        
        # Подключаем клики для ручного выбора подпапок пользователем
        self.tree_view.clicked.connect(self.on_folder_selected)
        
        splitter.addWidget(self.tree_view)

        # === ПРАВАЯ ПАНЕЛЬ: Что загружаем ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        group_one = QGroupBox()
        group_one_layout = QVBoxLayout(group_one)
        group_one_layout.setContentsMargins(2, 5, 2, 0)
        group_one_layout.setSpacing(0)
        right_layout.addWidget(group_one)

        group_one_layout.addWidget(QLabel("Список выгружаемых файлов"))

        group_one_layout.addSpacerItem(QSpacerItem(0, 10))

        self.list_widget = QListWidget()
        total_size = 0
        
        for file_path in self.target_files:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setIcon(QIcon("./images/img.svg"))
            item.setToolTip(file_path)
            self.list_widget.addItem(item)
            
            # Считаем размер файлов относительно папки назначения
            full_path = file_path if os.path.isabs(file_path) else os.path.join(self.dest, file_path)
            if os.path.exists(full_path):
                total_size += os.path.getsize(full_path)

        group_one_layout.addWidget(self.list_widget)
        
        total_files = RowArrowWidget(f"Всего файлов: {len(self.target_files)} шт.")
        total_files.hide_arrow()
        group_one_layout.addWidget(total_files)

        size_mb = total_size / (1024 * 1024)
        total_size = RowArrowWidget(f"Общий размер: {size_mb:.2f} MB")
        total_size.hide_arrow()
        group_one_layout.addWidget(total_size)

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

        self.btn_ok = SmallBtn(Lng.ok[Cfg.lng_index])
        self.btn_ok.clicked.connect(self.ok_clicked_cmd)
        self.btn_ok.setFixedWidth(90)
        btn_layout.addWidget(self.btn_ok)

        self.btn_cancel = SmallBtn(Lng.cancel[Cfg.lng_index])
        self.btn_cancel.clicked.connect(self.deleteLater)
        self.btn_cancel.setFixedWidth(90)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

    def _expand_to_target(self):

        def cmd():
            idx = self.file_model.index(self.dest)
            self.tree_view.expand(idx)
            self.tree_view.setCurrentIndex(idx)
            self.tree_view.scrollTo(idx, QTreeView.ScrollHint.PositionAtCenter)  

        QTimer.singleShot(100, cmd)

    def update_target_dir_label(self):
        folder_name = os.path.basename(self.dest) 
        self.lbl_target_dir.text_widget.setText(f"Целевая папка: {folder_name}")

    def ok_clicked_cmd(self):
        self.ok_clicked.emit(self.dest)

    def on_folder_selected(self, index):
        if self.file_model.isDir(index):
            self.dest = self.file_model.filePath(index)
            self.update_target_dir_label()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.ok_clicked_cmd()
        return super().keyPressEvent(a0)

