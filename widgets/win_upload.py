import os

from PyQt6.QtCore import QDir, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QIcon
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QSpacerItem, QSplitter,
                             QTreeView, QVBoxLayout, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import SharedUtils

from ._base_widgets import RowArrowWidget, SmallBtn, UMainWindow


class UploadWin(UMainWindow):
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

        self.tree_view = QTreeView()
        self.tree_view.header().hide()
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        self.file_model.setRootPath(self.root_dir)
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(self.root_dir))
        self.file_model.directoryLoaded.connect(self._expand_to_target)
        self.tree_view.clicked.connect(self.on_folder_selected)
        for i in range(1, 4):
            self.tree_view.setColumnHidden(i, True)

        splitter.addWidget(self.tree_view)

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
        total_size = 0
        for file_path in self.files_to_copy:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setIcon(QIcon(self.img_icon_path))
            item.setToolTip(file_path)
            self.list_widget.addItem(item)
            total_size += os.path.getsize(file_path)    

        group_one_layout.addWidget(self.list_widget)
        
        total_files = RowArrowWidget(
            f"{Lng.total_files[Cfg.lng_index]}: {len(self.files_to_copy)}"
        )
        total_files.hide_arrow()
        group_one_layout.addWidget(total_files)

        size_mb = SharedUtils.get_f_size(total_size)
        total_size = RowArrowWidget(f"{Lng.file_size[Cfg.lng_index]}: {size_mb}")
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
        self.lbl_target_dir.text_widget.setText(
            f"{Lng.dest_folder[Cfg.lng_index]}: {folder_name}"
        )

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

