import os
from multiprocessing import shared_memory

import cv2
import numpy as np
import sqlalchemy
from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCursor
from PyQt6.QtSvgWidgets import QSvgWidget  # Не забудьте импортировать
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QStackedWidget,
                             QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker, ReadImg, ReadImgItem
from system.shared_utils import ImgUtils
from system.tasks import ImagePreviewTask, ImageSearcher, UThreadPool
from system.utils import Utils

from ._base_widgets import (ActiveButton, GrayTextLabel, RowArrowWidget,
                            TitleTextLabel, TransparentFrame, TransparentLabel,
                            TransparentWidget, UGroupBox, UMainWidget,
                            UPushButton, USep, USlider)



class ProgressWin(UMainWidget):
    stop_img_search = pyqtSignal()
    base_image_svg_path = Static.COMMON_ICONS / "base_image.svg"
    stop_svg_path = Static.COMMON_ICONS / "stop.svg"
    base_image_size = (28, 28)

    def __init__(self):
        super().__init__()

        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.progress[JsonData.lng_index])

        self.stop_icon = QIcon(str(self.stop_svg_path))

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 10)

        self.text_container = TransparentWidget()
        self.central_layout.addWidget(self.text_container)

        self.text_layout = QHBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(5, 0, 5, 0)
        self.text_layout.setSpacing(10)

        self.svg_icon = QSvgWidget() 
        self.svg_icon.load(str(self.base_image_svg_path))
        self.svg_icon.setFixedSize(*self.base_image_size)
        self.text_layout.addWidget(self.svg_icon)

        self.text_label = TransparentLabel("")
        self.text_layout.addWidget(self.text_label)

        self.cancel_btn = UPushButton(Lng.stop[JsonData.lng_index])
        self.cancel_btn.setIcon(self.stop_icon)
        self.cancel_btn.clicked.connect(self.stop_img_search.emit)
        self.central_layout.addWidget(self.cancel_btn)

        max_ = 99999
        self.set_text(max_, max_)
        self.text_label.adjustSize()
        self.text_label.setFixedWidth(self.text_label.width())

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        # self.text_label.setText(Lng.please_wait[JsonData.lng_index])

    def set_text(self, current_count, total_count):
        if current_count > total_count:
            current_count = total_count

        if total_count == 0:
            text = Lng.please_wait[JsonData.lng_index]
        else:
            text = (
                f"{Lng.indexing[JsonData.lng_index]} "
                f"{current_count} "
                f"{Lng.from_[JsonData.lng_index]} "
                f"{total_count}"
            )

        self.text_label.setText(text)

    def set_text(self, current_count, total_count):
        if current_count > total_count:
            current_count = total_count

        if total_count == 0:
            text = Lng.please_wait[JsonData.lng_index]
        else:
            text = (
                f"{Lng.indexing[JsonData.lng_index]} "
                f"{current_count} "
                f"{Lng.from_[JsonData.lng_index]} "
                f"{total_count}"
            )

        self.text_label.setText(text)

    def closeEvent(self, a0):
        a0.ignore()


class SliderWidget(TransparentWidget):

    def __init__(self):
        super().__init__()

        base_value = 50
        self.current_value = base_value

        self.h_layout = QHBoxLayout(self)
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(10)

        self.slider = USlider()
        self.slider.setOrientation(
            Qt.Orientation.Horizontal
        )
        self.slider.setMinimum(30)
        self.slider.setMaximum(100)
        self.slider.setValue(base_value)

        self.h_layout.addWidget(self.slider)

        self.value_label = TransparentLabel(
            f"{base_value}%"
        )
        self.h_layout.addWidget(self.value_label)

        self.slider.clicked.connect(
            self.slider_clicked_cmd
        )

    def slider_clicked_cmd(self, value: int):
        self.value_label.setText(f"{value}%")
        self.current_value = value


DROP_WIDGET_SIZE = (350, 300)


class WinImgSearchDropWidget(TransparentFrame):
    svg_path = Static.COMMON_ICONS / "base_image.svg"
    svg_size = (50, 50)
    image_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(*DROP_WIDGET_SIZE)
        self.setAcceptDrops(True)

        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(10)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(str(self.svg_path))
        self.svg_widget.setFixedSize(*self.svg_size)

        self.v_layout.addWidget(
            self.svg_widget,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        self.title_label = TitleTextLabel(Lng.image_search[JsonData.lng_index])

        self.v_layout.addWidget(
            self.title_label,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        self.descr_label = GrayTextLabel("")
        self.descr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(
            self.descr_label,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        lines_base_text = (
            f"{Lng.search[JsonData.lng_index]} "
            f"{Lng.in_[JsonData.lng_index]} "
            f"\"{Mf.current_mf.mf_alias}\"",

            f"{Lng.image_search_drop[JsonData.lng_index]}.",
        )
        self.base_text = "\n".join(lines_base_text)
        self.descr_label.setText(self.base_text)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)

    def dropEvent(self, a0):
        if not a0.mimeData().hasUrls():
            return
        path = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
        if not path.endswith(ImgUtils.ext_all):
            return
        self.image_dropped.emit(path)
        a0.acceptProposedAction()


class WinImgSearchPreviewWidget(TransparentFrame):
    pixmap_finished = pyqtSignal()
    cancel_clicked = pyqtSignal()
    cancel_svg_path = Static.COMMON_ICONS / "cancel.svg"
    cancel_icon_size = (20, 20)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(*DROP_WIDGET_SIZE)

        self.pixmap = QPixmap()
        self.image_label = QLabel(Lng.loading[JsonData.lng_index])
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.image_label)

        self.create_cancel_button()

        self.cancel_timer = QTimer(self)
        self.cancel_timer.setSingleShot(True)
        self.cancel_timer.timeout.connect(self.hide_cancel_icon)

    def clear_image_cmd(self, e):
        self.cancel_clicked.emit()

    def set_pixmap(self, img_array: np.ndarray):

        def finished(qimage: QImage):
            self.pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(self.pixmap)
            self.pixmap_finished.emit()

        self.qimage_task = ImagePreviewTask(
            img_array=img_array,
            size=DROP_WIDGET_SIZE,
            radius=10.0
        )
        self.qimage_task.sigs.finished_.connect(finished)
        UThreadPool.start(self.qimage_task)

    def clear(self):
        self.pixmap = QPixmap()
        self.image_label.clear()

    def create_cancel_button(self):
        self.cancel_icon = QSvgWidget(self)
        self.cancel_icon.load(str(self.cancel_svg_path))
        self.cancel_icon.setFixedSize(*self.cancel_icon_size)
        self.cancel_icon.mouseReleaseEvent = self.clear_image_cmd
        self.cancel_icon.setCursor(Qt.CursorShape.PointingHandCursor)

        x, y = self.width() - self.cancel_icon.width() - 10, 10
        self.cancel_icon.move(x, y)
        self.cancel_icon.hide()

    def hide_cancel_icon(self):
        pos = self.mapFromGlobal(QCursor.pos())

        if not self.rect().contains(pos):
            self.cancel_icon.hide()
        else:
            self.cancel_timer.start(2000)

    def enterEvent(self, event):
        self.cancel_icon.show()
        return super().enterEvent(event)

    def leaveEvent(self, a0):
        self.cancel_icon.hide()
        return super().leaveEvent(a0)

    def showEvent(self, event):
        super().showEvent(event)

        self.cancel_icon.show()
        self.cancel_timer.start(2000)


class ControlsWidget(UGroupBox):
    reset_svg = Static.COMMON_ICONS / "reset.svg"
    reset_btn_clicked = pyqtSignal()
    slider_moved = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.reset_icon = QIcon(str(self.reset_svg))

        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(5, 5, 5, 15)
        self.v_layout.setSpacing(0)

        title = TitleTextLabel(Lng.accuracy[JsonData.lng_index])
        self.v_layout.addWidget(title)

        self.slider_widget = SliderWidget()
        self.v_layout.addWidget(self.slider_widget)

        descr = GrayTextLabel(Lng.image_search_descr[JsonData.lng_index])
        self.v_layout.addWidget(descr)


class WinImgSearch(UMainWidget):
    reload_thumbnails = pyqtSignal()
    closed = pyqtSignal()
    magnifier_svg_path = Static.COMMON_ICONS / "magnifier.svg"

    def __init__(self):
        super().__init__()

        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.image_search[JsonData.lng_index])
        self.img_array = None
        self.img_search_task = None
        self.read_img_task = None
        self.shm = None
        self.progress_win = None
        self.read_img_poll_ms = 300

        self.magnifier_icon = QIcon(str(self.magnifier_svg_path))

        self.found_image_timer = QTimer(self)
        self.found_image_timer.setSingleShot(True)
        self.found_image_timer.timeout.connect(self.reload_thumbnails.emit)
        self.poll_progress_win_timer = QTimer(self)
        self.poll_progress_win_timer.setSingleShot(True)
        self.poll_progress_win_timer.timeout.connect(self.poll_progress_win)
        self.read_img_timer = QTimer(self)
        self.read_img_timer.setSingleShot(True)
        self.read_img_timer.timeout.connect(self.poll_read_img)

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)

        self.image_stack = QStackedWidget()
        self.drop_widget = WinImgSearchDropWidget()
        self.preview_widget = WinImgSearchPreviewWidget()
        self.preview_widget.cancel_clicked.connect(self.reset_img_search)
        self.image_stack.addWidget(self.drop_widget)
        self.image_stack.addWidget(self.preview_widget)
        self.image_stack.setCurrentIndex(0)
        self.central_layout.addWidget(
            self.image_stack,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        self.drop_widget.image_dropped.connect(self.image_dropped)

        self.controls_widget = ControlsWidget()
        self.central_layout.addWidget(self.controls_widget)

        btn_layout = QHBoxLayout()
        self.central_layout.addLayout(btn_layout)
        btn_layout.addStretch()
        self.start_btn = ActiveButton(Lng.find_matches[JsonData.lng_index])
        self.start_btn.setIcon(self.magnifier_icon)
        self.start_btn.clicked.connect(self.start_img_search)
        btn_layout.addWidget(self.start_btn)
        cancel_btn = UPushButton(Lng.close[JsonData.lng_index])
        cancel_btn.clicked.connect(self.hide_window)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

        # QTimer.singleShot(500, self.open_progress_win)

    def image_dropped(self, path: str):
        self.start_read_img_task(path)

    def reset_img_search(self):
        self.stop_timers_and_tasks()
        self.cleanup_shm()
        self.img_array = None
        self.preview_widget.clear()
        self.image_stack.setCurrentIndex(0)
        if Dynamic.img_search_thumb_paths:
            Dynamic.img_search_thumb_paths.clear()
        self.reload_thumbnails.emit()

    def start_img_search(self):
        if self.img_array is None:
            return
        if self.img_search_task is not None:
            self.img_search_task.stop_task()
            self.img_search_task = None
        self.img_search_task = ImageSearcher(
            src_img=self.img_array,
            similarity_value=self.controls_widget.slider_widget.current_value,
            mf=Mf.current_mf,
        )
        self.img_search_task.sigs.finished_.connect(self.img_search_finished)
        self.img_search_task.sigs.found_image.connect(self.found_image_cmd)
        Dynamic.img_search_thumb_paths.clear()
        UThreadPool.start(self.img_search_task)
        self.open_progress_win()
        self.poll_progress_win()

    def stop_img_search(self):
        self.poll_progress_win_timer.stop()
        if self.img_search_task is not None:
            self.img_search_task.stop_task()
            self.img_search_task = None
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
        if not Dynamic.img_search_thumb_paths:
            self.found_image_cmd("999999999999")
        self.poll_progress_win_timer.stop()
        if self.progress_win is not None:
            try:
                QTimer.singleShot(1000, self.progress_win.deleteLater,)
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
                self.img_search_task.total_count,
            )
            self.poll_progress_win_timer.start(500)
        except RuntimeError:
            self.poll_progress_win_timer.stop()

    def poll_read_img(self):
        self.read_img_timer.stop()
        if self.read_img_task is None:
            return
        if not self.read_img_task.process_queue.empty():
            item: ReadImgItem = (self.read_img_task.process_queue.get())
            try:
                self.shm = shared_memory.SharedMemory(name=item.shm_name)
                self.img_array = np.ndarray(
                    item.shape,
                    dtype=np.dtype(item.dtype),
                    buffer=self.shm.buf,
                )
                self.image_stack.setCurrentIndex(1)
                self.preview_widget.set_pixmap(self.img_array)

                if ImgUtils.is_grayscale(self.img_array):
                    self.cleanup_shm()
                    self.img_array = None
                    QTimer.singleShot(1500, self.reset_img_search,)
                if not self.read_img_task.is_alive():
                    self.read_img_task.terminate_join()
                    self.read_img_task = None
            except Exception:
                self.cleanup_shm()
                self.img_array = None
                if self.read_img_task is not None:
                    try:
                        self.read_img_task.terminate_join()
                    except Exception:
                        pass
                    self.read_img_task = None
        else:
            self.read_img_timer.start(self.read_img_poll_ms)

    def start_read_img_task(self, url: str, ms=300):
        self.cleanup_shm()
        if self.read_img_timer.isActive():
            self.read_img_timer.stop()
        if self.read_img_task is not None:
            try:
                self.read_img_task.terminate_join()
            except Exception:
                pass
            self.read_img_task = None
        self.img_array = None
        self.read_img_poll_ms = ms
        self.read_img_task = ProcessWorker(
            target=ReadImg.start,
            args=(url, 0),
        )
        self.read_img_task.start()
        self.read_img_timer.start(ms)

    def found_image_cmd(self, rel_path: str):
        Dynamic.img_search_thumb_paths.add(rel_path)
        self.found_image_timer.stop()
        self.found_image_timer.start(500)

    def cleanup_shm(self):
        if self.shm is not None:
            try:
                self.shm.close()
                self.shm.unlink()
            except Exception:
                pass
            self.shm = None

    def stop_timers_and_tasks(self):
        if self.poll_progress_win_timer is not None:
            self.poll_progress_win_timer.stop()
        if self.read_img_timer is not None:
            self.read_img_timer.stop()
        if self.img_search_task is not None:
            try:
                self.img_search_task.stop_task()
            except Exception:
                pass
            self.img_search_task = None
        if self.read_img_task is not None:
            try:
                self.read_img_task.terminate_join()
            except Exception:
                pass
            self.read_img_task = None

    def hide_window(self):
        self.stop_timers_and_tasks()
        if self.progress_win is not None:
            try:
                self.progress_win.deleteLater()
            except RuntimeError:
                pass
            self.progress_win = None
        self.closed.emit()
        self.hide()

    def custom_close(self):
        self.stop_timers_and_tasks()
        self.cleanup_shm()
        self.img_array = None
        self.closed.emit()
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_window()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide_window()