import os
from multiprocessing import shared_memory

import cv2
import numpy as np
import sqlalchemy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget)
from sqlalchemy import func

from cfg import Cfg, Dynamic, Static
from system.database import Dbase, Thumbs
from system.items import ReadImgItem
from system.lang import Lng
from system.multiprocess import ProcessWorker, ReadImg
from system.shared_utils import ImgUtils
from system.tasks import ImageSearcher, UThreadPool
from system.utils import Utils

from ._base_widgets import UMainWindow, USlider


class ProgressWin(UMainWindow):
    cancel_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedHeight(70)
        self.setWindowTitle(Lng.progress[Cfg.lng_index])
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_layout.setSpacing(5)
        self.central_layout.setContentsMargins(0, 0, 0, 0)

        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setFixedSize(200, 30)
        self.central_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cancel_btn = QPushButton(Lng.stop[Cfg.lng_index])
        self.cancel_btn.setFixedWidth(90)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self.central_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_text(0, 0)
        self.adjustSize()

    def set_text(self, current_count, total_count):
        if current_count > total_count:
            current_count = total_count
        if total_count == 0:
            text = Lng.preparing[Cfg.lng_index]
        else:
            text = f"{Lng.search[Cfg.lng_index]} {current_count} {Lng.from_[Cfg.lng_index]} {total_count}"
            self.text_label.setText(text)

    def closeEvent(self, a0):
        a0.ignore()


class SliderWidget(QWidget):
    # slider_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        base_value = 50
        self.current_value = base_value

        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(10)

        self.slider = USlider()

        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(base_value)
        self.slider.setFixedWidth(80)

        self.h_layout.addWidget(self.slider)

        self.value_label = QLabel(f"{base_value}%")
        self.h_layout.addWidget(self.value_label)

        self.slider.clicked.connect(self.slider_clicked_cmd)

    def slider_clicked_cmd(self, value: int):
        self.value_label.setText(f"{value}%")
        self.current_value = value


class WinImgSearch(UMainWindow):
    found_image = pyqtSignal()
    ww = 250
    hh = 200

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setAcceptDrops(True)
        self.setWindowTitle(Lng.image_search[Cfg.lng_index])
        self.central_layout.setContentsMargins(15, 10, 15, 5)
        self.central_layout.setSpacing(10)

        group = QGroupBox()
        self.central_layout.addWidget(group)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(5, 5, 5, 5)

        self.img_label = QLabel(Lng.image_search_drop[Cfg.lng_index])
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setFixedSize(self.ww, self.hh)
        self.img_label.setWordWrap(True)
        group_layout.addWidget(self.img_label)

        self.central_layout.addStretch()

        self.slider_widget = SliderWidget()
        self.central_layout.addWidget(self.slider_widget)

        btn_layout = QHBoxLayout()
        self.central_layout.addLayout(btn_layout)

        btn_layout.addStretch()

        self.start_btn = QPushButton(Lng.start[Cfg.lng_index])
        self.start_btn.clicked.connect(self.start_image_searcher)
        self.start_btn.setFixedWidth(90)
        btn_layout.addWidget(self.start_btn)

        cancel_btn = QPushButton(Lng.close[Cfg.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        self.adjustSize()

    def start_image_searcher(self):

        if not hasattr(self, "img_array") or self.img_array is None:
            return
        
        Dynamic.thumb_path_set.clear()

        self.image_searcher = ImageSearcher(self.img_array, self.slider_widget.current_value)
        self.image_searcher.sigs.finished_.connect(self.image_searcher_finished)
        self.image_searcher.sigs.found_image.connect(self.found_image_cmd)
        UThreadPool.start(self.image_searcher)

        self.get_total_count()
        self.open_progress_win()
        self.poll_progress_win()

    def open_progress_win(self):
        self.progress_win = ProgressWin()
        self.progress_win.center_to_parent(self)
        self.progress_win.cancel_clicked.connect(self.cancel_progress_win)
        self.progress_win.show()

    def cancel_progress_win(self):
        self.progress_timer.stop()
        self.image_searcher.stop_task()
        self.progress_win.deleteLater() 

    def image_searcher_finished(self):
        if not Dynamic.thumb_path_set:
            self.found_image_cmd("999999999999")
        self.progress_win.deleteLater()

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

    def found_image_cmd(self, rel_path: str):
        Dynamic.thumb_path_set.add(rel_path)
        if hasattr(self, "found_image_timer"):
            self.found_image_timer.stop()
        self.found_image_timer = QTimer(self)
        self.found_image_timer.setSingleShot(True)
        self.found_image_timer.timeout.connect(self.found_image.emit)
        self.found_image_timer.start(500)

    def read_img(self, url: str, ms=300):

        def poll():
            self.read_img_timer.stop()
            queue = self.read_img_task.process_queue
            if not queue.empty():
                item: ReadImgItem = queue.get()
                self.shm = shared_memory.SharedMemory(name=item.shm_name)
                self.img_array = np.ndarray(item.shape, dtype=np.dtype(item.dtype), buffer=self.shm.buf)

                if ImgUtils.is_grayscale(self.img_array):
                    del self.img_array
                    self.img_label.clear()
                    self.img_label.setText(Lng.only_color[Cfg.lng_index])
                    QTimer.singleShot(
                        1500,
                        lambda: self.img_label.setText(Lng.image_search_drop[Cfg.lng_index])
                    )
                else:
                    qimage = Utils.qimage_from_array(self.img_array)
                    qimage = qimage.scaled(
                        self.img_label.width(),
                        self.img_label.height(),
                        aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio
                    )
                    self.img_label.setPixmap(QPixmap.fromImage(qimage))

            if not self.read_img_task.is_alive():
                self.read_img_task.terminate_join()
                # self.shm.close()
                # self.shm.unlink()
            else:
                self.read_img_timer.start(ms)

        self.read_img_task = ProcessWorker(
            target=ReadImg.start,
            args=(url, Static.max_img_size * 2, )
        )
        self.read_img_timer = QTimer(self)
        self.read_img_timer.setSingleShot(True)
        self.read_img_timer.timeout.connect(poll)

        self.read_img_task.start()
        self.read_img_timer.start(ms)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            first_url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if first_url.endswith(ImgUtils.ext_all):
                self.img_label.clear()
                self.img_label.setText(Lng.loading[Cfg.lng_index])
                self.read_img(first_url)

        return super().dropEvent(a0)
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    
    def deleteLater(self):
        if hasattr(self, "image_searcher"):
            self.image_searcher.stop_task()
        return super().deleteLater()
    
    def closeEvent(self, a0):
        if hasattr(self, "image_searcher"):
            self.image_searcher.stop_task()
        return super().closeEvent(a0)
    
# чтение изображения в фоне
# решить где ресайз
# отправлять в таск только путь?
# как прервать задачу закрытием
# когда очищать список динамик
# при закрытии очищать и при отображении сетки очищать