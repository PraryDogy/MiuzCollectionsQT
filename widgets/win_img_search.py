import os
from multiprocessing import shared_memory

import cv2
import numpy as np
import sqlalchemy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QVBoxLayout,
                             QWidget)
from sqlalchemy import func

from cfg import JsonData, Dynamic, Static
from system.database import Dbase, Thumbs
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker, ReadImg, ReadImgItem
from system.shared_utils import ImgUtils
from system.tasks import ImageSearcher, UThreadPool
from system.utils import Utils

from ._base_widgets import UMainWidget, UPushButton, USlider


class ProgressWin(UMainWidget):
    stop_img_search = pyqtSignal()
    ww = 200

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setFixedWidth(self.ww)
        self.setWindowTitle(Lng.progress[JsonData.lng_index])
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_layout.setSpacing(5)
        self.central_layout.setContentsMargins(0, 0, 0, 10)

        self.text_label = QLabel(Lng.preparing[JsonData.lng_index])
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setFixedSize(200, 30)
        self.central_layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cancel_btn = UPushButton(Lng.stop[JsonData.lng_index])
        self.cancel_btn.clicked.connect(self.stop_img_search.emit)
        self.central_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.set_text(0, 0)
        self.adjustSize()

    def set_text(self, current_count, total_count):
        if current_count > total_count:
            current_count = total_count
        if total_count == 0:
            text = Lng.preparing[JsonData.lng_index]
        else:
            text = (
                f"{Lng.search[JsonData.lng_index]} {current_count} " 
                f"{Lng.from_[JsonData.lng_index]} {total_count}"
            )
            self.text_label.setText(text)

    def closeEvent(self, a0):
        ...
        a0.ignore()


class SliderWidget(QWidget):

    def __init__(self):
        super().__init__()
        base_value = 50
        self.current_value = base_value

        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(10)

        self.accuracy_label = QLabel(Lng.accuracy[JsonData.lng_index] + ":")
        self.h_layout.addWidget(self.accuracy_label)

        self.slider = USlider()

        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setMinimum(30)
        self.slider.setMaximum(100)
        self.slider.setValue(base_value)

        self.h_layout.addWidget(self.slider)

        self.value_label = QLabel(f"{base_value}%")
        self.h_layout.addWidget(self.value_label)

        self.slider.clicked.connect(self.slider_clicked_cmd)

    def slider_clicked_cmd(self, value: int):
        self.value_label.setText(f"{value}%")
        self.current_value = value


class WinImgSearch(UMainWidget):
    found_image = pyqtSignal()
    reset_all_filters = pyqtSignal()
    closed = pyqtSignal()
    ww = 250
    hh = 200

    def __init__(self):
        super().__init__()

        self.img_array = None
        self.img_search_task = None
        self.read_img_task = None
        self.shm = None
        self.progress_win = None

        self.read_img_poll_ms = 300

        self.found_image_timer = QTimer(self)
        self.found_image_timer.setSingleShot(True)
        self.found_image_timer.timeout.connect(self.found_image.emit)

        self.poll_progress_win_timer = QTimer(self)
        self.poll_progress_win_timer.setSingleShot(True)
        self.poll_progress_win_timer.timeout.connect(self.poll_progress_win)

        self.read_img_timer = QTimer(self)
        self.read_img_timer.setSingleShot(True)
        self.read_img_timer.timeout.connect(self.poll_read_img)

        self.set_always_on_top()
        self.set_close_only()
        self.setAcceptDrops(True)
        self.setWindowTitle(Lng.image_search[JsonData.lng_index])
        self.central_layout.setContentsMargins(10, 10, 10, 5)
        self.central_layout.setSpacing(10)

        group = QGroupBox()
        self.central_layout.addWidget(group)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(5, 5, 5, 5)

        lines_base_text = (
            f"{Lng.search[JsonData.lng_index]} {Lng.in_[JsonData.lng_index]} "
            f"\"{Mf.current_mf.mf_alias}\".",
            f"{Lng.image_search_drop[JsonData.lng_index]}."
        )
        self.base_text = "\n".join(lines_base_text)

        self.img_label = QLabel(self.base_text)
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

        self.start_btn = UPushButton(Lng.start[JsonData.lng_index])
        self.start_btn.clicked.connect(self.start_img_search)
        btn_layout.addWidget(self.start_btn)

        cancel_btn = UPushButton(Lng.close[JsonData.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        self.adjustSize()

    def start_img_search(self):
        if self.img_array is None:
            return
        self.img_search_task = ImageSearcher(
            src_img=self.img_array,
            similarity_value=self.slider_widget.current_value
        )
        self.img_search_task.sigs.finished_.connect(
            self.img_search_finished
        )
        self.img_search_task.sigs.found_image.connect(
            self.found_image_cmd
        )
        UThreadPool.start(self.img_search_task)

        self.get_total_thumbnails_count()
        self.open_progress_win()
        self.poll_progress_win()
        self.reset_all_filters.emit()

    def stop_img_search(self):
        self.poll_progress_win_timer.stop()
        if self.img_search_task is not None:
            self.img_search_task.stop_task()
        if self.progress_win is not None:
            try:
                self.progress_win.deleteLater()
            except RuntimeError:
                pass
            self.progress_win = None

    def open_progress_win(self):
        self.progress_win = ProgressWin()
        self.progress_win.center_to_parent(self)
        self.progress_win.stop_img_search.connect(self.stop_img_search)
        self.progress_win.show()

    def img_search_finished(self):
        if not Dynamic.thumb_path_set:
            self.found_image_cmd("999999999999")
        
        # Безопасное удаление окна прогресса с проверкой на его существование
        self.poll_progress_win_timer.stop()
        if self.progress_win is not None:
            try:
                QTimer.singleShot(1000, self.progress_win.deleteLater)
            except RuntimeError:
                pass
            self.progress_win = None

    def poll_progress_win(self):
        self.poll_progress_win_timer.stop()
        if self.progress_win is None or self.img_search_task is None:
            return
            
        try:
            self.progress_win.set_text(
                self.img_search_task.current_count,
                self.total_count
            )
            self.poll_progress_win_timer.start(500)
        except RuntimeError:
            self.poll_progress_win_timer.stop()

    def poll_read_img(self):
        self.read_img_timer.stop()

        if self.read_img_task is None:
            return

        if not self.read_img_task.process_queue.empty():
            item: ReadImgItem = self.read_img_task.process_queue.get()

            try:
                self.shm = shared_memory.SharedMemory(name=item.shm_name)

                self.img_array = np.ndarray(
                    item.shape,
                    dtype=np.dtype(item.dtype),
                    buffer=self.shm.buf
                )

                if ImgUtils.is_grayscale(self.img_array):
                    self.cleanup_shm()

                    self.img_label.clear()
                    self.img_label.setText(Lng.only_color[JsonData.lng_index])

                    QTimer.singleShot(
                        1500,
                        lambda: self.img_label.setText(self.base_text)
                    )
                else:
                    qimage = Utils.qimage_from_array(self.img_array)

                    min_size = min(
                        self.img_label.width(),
                        self.img_label.height()
                    )

                    pixmap = QPixmap.fromImage(qimage)
                    resized_qpixmap = Utils.qiconed_resize(
                        pixmap,
                        min_size
                    )

                    self.img_label.setPixmap(resized_qpixmap)

            except Exception:
                self.cleanup_shm()

        if not self.read_img_task.is_alive():
            self.read_img_task.terminate_join()
            self.read_img_task = None
        else:
            self.read_img_timer.start(self.read_img_poll_ms)

    def get_total_thumbnails_count(self):
        with Dbase.main_engine.connect() as conn:
            stmt = sqlalchemy.select(func.count()).select_from(Thumbs.table)
            self.total_count = conn.execute(stmt).scalar()

    def found_image_cmd(self, rel_path: str):
        Dynamic.thumb_path_set.add(rel_path)
        self.found_image_timer.stop()
        self.found_image_timer.start(500)

    def start_read_img_task(self, url: str, ms=300):
        self.cleanup_shm()

        if self.read_img_timer.isActive():
            self.read_img_timer.stop()

        if self.read_img_task is not None:
            self.read_img_task.terminate_join()

        self.read_img_poll_ms = ms

        self.read_img_task = ProcessWorker(
            target=ReadImg.start,
            args=(url, Static.max_thumb_size * 2)
        )

        self.read_img_task.start()
        self.read_img_timer.start(ms)

    def cleanup_shm(self):
        """Безопасное освобождение ресурсов SharedMemory."""
        self.img_array = None
        if self.shm is not None:
            try:
                self.shm.close()
                self.shm.unlink()
            except Exception:
                pass
            self.shm = None

    def stop_all_tasks(self):
        self.poll_progress_win_timer.stop()
        if self.read_img_timer is not None:
            self.read_img_timer.stop()
        
        if self.img_search_task is not None:
            self.img_search_task.stop_task()
        if self.read_img_task is not None:
            self.read_img_task.terminate_join()
            
        self.cleanup_shm()

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            first_url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if first_url.endswith(ImgUtils.ext_all):
                self.img_label.clear()
                self.img_label.setText(Lng.loading[JsonData.lng_index])
                self.start_read_img_task(first_url)
        return super().dropEvent(a0)
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.close()  # Используем close() вместо деструктора напрямую
        return super().keyPressEvent(a0)
    
    def deleteLater(self):
        self.stop_all_tasks()
        # Вызываем закрытие родительского класса без дублирования сигналов
        self.closed.emit()
        return super().deleteLater()
    
    def closeEvent(self, a0):
        self.stop_all_tasks()
        self.closed.emit()
        return super().closeEvent(a0)