import os

import sqlalchemy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QPushButton
from sqlalchemy import func

from cfg import Dynamic
from system.database import Dbase, Thumbs
from system.shared_utils import ImgUtils
from system.tasks import ImageSearcher, UThreadPool
from system.utils import Utils

from ._base_widgets import UMainWindow


class ProgressWin(UMainWindow):
    cancel_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()

        self.text_label = QLabel()
        self.central_layout.addWidget(self.text_label)

        self.cancel_btn = QPushButton("cancel")
        self.cancel_btn.clicked.connect(self.cancel_cmd)
        self.central_layout.addWidget(self.cancel_btn)

        self.adjustSize()
        self.set_text(0, 0)

    def cancel_cmd(self):
        self.cancel_clicked.emit()
        self.deleteLater()

    def set_text(self, current_count, total_count):
        if total_count == 0:
            total_count = "..."
        text = f"Поиск {current_count} из {total_count}"
        self.text_label.setText(text)

    def closeEvent(self, a0):
        self.cancel_clicked.emit()
        return super().closeEvent(a0)


class WinImgSearch(UMainWindow):
    finished_ = pyqtSignal(set)
    img_size = 450

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setAcceptDrops(True)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(5)

        self.img_label = QLabel("Перетяните сюда изображение")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setFixedSize(self.img_size, self.img_size)
        self.central_layout.addWidget(self.img_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_layout.addStretch()

        self.start_btn = QPushButton("start")
        self.start_btn.clicked.connect(self.start_image_searcher)
        self.start_btn.setFixedWidth(90)
        self.central_layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()

    def start_image_searcher(self):

        if not hasattr(self, "img_array") or self.img_array is None:
            return

        self.image_searcher = ImageSearcher(self.img_array, max_side=450)
        self.image_searcher.sigs.finished_.connect(self.finished)
        UThreadPool.start(self.image_searcher)

        self.get_total_count()
        self.open_progress_win()
        self.poll_progress_win()

    def open_progress_win(self):
        self.progress_win = ProgressWin()
        self.progress_win.center_to_parent(self)
        self.progress_win.cancel_clicked.connect(self.image_searcher.stop_task)
        self.progress_win.show()

    def poll_progress_win(self):

        def timeout():
            try:
                self.progress_win.set_text(
                    self.image_searcher.current_count,
                    self.total_count
                )
            except RuntimeError:
                ...

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(timeout)
        self.progress_timer.start(500)

    def get_total_count(self):
        with Dbase.main_engine.connect() as conn:
            stmt = sqlalchemy.select(func.count()).select_from(Thumbs.table)
            self.total_count = conn.execute(stmt).scalar()

    def finished(self, thumb_names_list: set[str]):

        # if not thumb_names_list:
            # return

        Dynamic.thumb_path_set = thumb_names_list
        self.finished_.emit(thumb_names_list)
        self.progress_timer.stop()
        self.progress_win.deleteLater()

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            first_url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if first_url.endswith(ImgUtils.ext_all):
                import cv2
                self.img_array = ImgUtils.read_img(first_url)
                # self.img_array = ImgUtils.resize(self.img_array, 450)
                qimage = Utils.qimage_from_array(self.img_array)
                qimage = qimage.scaled(self.img_size, self.img_size, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
                self.img_label.setPixmap(QPixmap.fromImage(qimage))

                self.img_array = cv2.cvtColor(self.img_array, cv2.COLOR_RGB2BGR)

        return super().dropEvent(a0)
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.image_searcher.stop_task()
            self.deleteLater()
        return super().keyPressEvent(a0)
    
# чтение изображения в фоне
# решить где ресайз
# отправлять в таск только путь?
# как прервать задачу закрытием
# когда очищать список динамик
# при закрытии очищать и при отображении сетки очищать