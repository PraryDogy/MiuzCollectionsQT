import os
import sys

from PyQt6.QtCore import QDir, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QFrame,
                             QGroupBox, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QMainWindow, QPushButton,
                             QSplitter, QTreeView, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import SmallBtn, UHBoxLayout, UMainWindow


class UploadWin(UMainWindow):
    ok_clicked = pyqtSignal()

    def __init__(self, mf: Mf, current_dir: str, dropped_files: list[str]):
        super().__init__()
        self.setWindowTitle("Подтверждение выгрузки")
        self.resize(900, 500)

        # Приводим все пути к абсолютному виду
        self.root_dir = mf.mf_current_path
        self.target_dir = os.path.join(
            mf.mf_current_path,
            current_dir.strip(os.sep)
        ).rstrip(os.sep)

        self.target_files = dropped_files

        # Главный сплиттер (Разделяет дерево и правое превью)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(splitter)

        # === ЛЕВАЯ ПАНЕЛЬ: Куда загружаем ===
        self.tree_view = QTreeView()
        self.tree_view.header().hide()  # Скрываем имя колонки
        
        self.file_model = QFileSystemModel()
        
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
        right_layout.setContentsMargins(10, 0, 10, 0)

        right_layout.addWidget(QLabel("Список выгружаемых файлов"))

        self.list_widget = QListWidget()
        total_size = 0
        
        for file_path in self.target_files:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setToolTip(file_path)
            self.list_widget.addItem(item)
            
            # Считаем размер файлов относительно папки назначения
            full_path = file_path if os.path.isabs(file_path) else os.path.join(self.target_dir, file_path)
            if os.path.exists(full_path):
                total_size += os.path.getsize(full_path)

        right_layout.addWidget(self.list_widget)

        # === Карточка со сводной информацией ===
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        
        size_mb = total_size / (1024 * 1024)
        info_layout.addWidget(QLabel(f"<b>Всего файлов:</b> {len(self.target_files)} шт."))
        info_layout.addWidget(QLabel(f"<b>Общий размер:</b> {size_mb:.2f} MB"))
        
        self.lbl_target_dir = QLabel()
        self.update_target_dir_label(self.target_dir)
        info_layout.addWidget(self.lbl_target_dir)
        
        right_layout.addWidget(info_frame)
        splitter.addWidget(right_widget)

        # Левое дерево строго 210 пикселей при старте
        splitter.setSizes([210, self.width() - 210])

        # === НИЖНЯЯ ПАНЕЛЬ: Кнопки управления окном ===
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Отмена")
        self.btn_ok = QPushButton("Загрузить")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        self.central_layout.addLayout(btn_layout)

        # Логика кнопок
        self.btn_cancel.clicked.connect(self.deleteLater)
        self.btn_ok.clicked.connect(self.ok_clicked.emit)
        self.btn_ok.clicked.connect(self.deleteLater)

    def _expand_to_target(self):

        def cmd():
            idx = self.file_model.index(self.target_dir)
            self.tree_view.expand(idx)
            self.tree_view.setCurrentIndex(idx)
            self.tree_view.scrollTo(idx, QTreeView.ScrollHint.PositionAtCenter)  

        QTimer.singleShot(100, cmd)

    def update_target_dir_label(self, path: str):
        folder_name = os.path.basename(path) or path
        self.lbl_target_dir.setText(f"<b>Целевая папка:</b> {folder_name}")
        self.lbl_target_dir.setToolTip(path)

    def on_folder_selected(self, index):
        if self.file_model.isDir(index):
            selected_path = self.file_model.filePath(index)
            self.target_dir = selected_path
            self.update_target_dir_label(selected_path)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.ok_clicked.emit()
            self.deleteLater()
        return super().keyPressEvent(a0)

