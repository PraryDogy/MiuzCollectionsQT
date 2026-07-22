import os
from dataclasses import dataclass
from multiprocessing import shared_memory

import numpy as np
from PyQt6.QtCore import (QEvent, QObject, QPoint, QPointF, QSize, Qt, QTimer,
                          pyqtSignal)
from PyQt6.QtGui import (QAction, QContextMenuEvent, QCursor, QIcon, QImage,
                         QKeyEvent, QMouseEvent, QPainter, QPixmap,
                         QResizeEvent, QTransform)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QGraphicsOpacityEffect,
                             QGraphicsPixmapItem, QGraphicsScene,
                             QGraphicsView)
from typing_extensions import Literal

from cfg import Cfg, Static
from system.items import DataItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker, ReadImg, ReadImgItem
from system.shared_utils import SharedUtils
from system.tasks import ImgArrayQImage, UThreadPool
from system.utils import Utils

from ._base_widgets import UMainWidget, UMenu, USubMenu
from .actions import CopyPath, RevealInFinder, Save, SetFav, WinInfoAction


@dataclass(slots=True)
class ImgViewItem:
    start_data_item: DataItem
    data_items: list[DataItem]
    is_selection: bool


class ImgWid(QGraphicsView):
    mouse_moved = pyqtSignal()

    def __init__(self, pixmap: QPixmap = None):
        super().__init__()

        self.setMouseTracking(True)
        self.setStyleSheet("background: black")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene_ = QGraphicsScene()
        self.setScene(self.scene_)

        self.pixmap_item: QGraphicsPixmapItem = None
        self._last_mouse_pos: QPointF = None
        self.is_zoomed = False

        if pixmap:
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene_.addItem(self.pixmap_item)
            self.resetTransform()
            self.horizontalScrollBar().setValue(0)
            self.verticalScrollBar().setValue(0)

    def zoom_in(self):
        self.scale(1.1, 1.1)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.is_zoomed = True

    def zoom_out(self):
        self.scale(0.9, 0.9)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.is_zoomed = True

    def zoom_fit(self):
        if self.pixmap_item:
            self.resetTransform()
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.is_zoomed = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_transparent(self, value: float):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(value)
        self.pixmap_item.setGraphicsEffect(effect)

    # ---------------------- Drag через мышь ----------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._last_mouse_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_moved.emit()
        if self._last_mouse_pos and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_zoomed:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self._last_mouse_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # Если это стрелки, не обрабатываем их здесь
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            event.ignore()  # передаём событие родителю
            return
        # для остальных клавиш можно оставить стандартную обработку
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)


class CustomSvg(QSvgWidget):
    clicked = pyqtSignal()
    svg_size = 50

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
                background: transparent;
            """
        )

    def load(self, file_path: str):
        super().load(file_path)
        renderer = self.renderer()
        if renderer and renderer.isValid():
            orig_size = renderer.defaultSize()
            aspect_ratio = orig_size.width() / orig_size.height()
            calculated_width = int(self.svg_size * aspect_ratio)
            self.setFixedSize(calculated_width, self.svg_size)

    def mouseReleaseEvent(self, a0: QMouseEvent):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mouseReleaseEvent(a0)


class ZoomWidget(CustomSvg):
    zoom_close = pyqtSignal()
    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()
    zoom_fit = pyqtSignal()
    svg_path = os.path.join(Static.internal_images, "zoom.svg")

    def __init__(self):
        super().__init__()
        self.load(self.svg_path)
        self.zone_width = self.width() / 4
        self.start_pos = None
        self.is_move = False

    def mousePressEvent(self, e: QMouseEvent):
        self.start_pos = e.pos()
        self.is_move = False
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent):
        if not self.start_pos:
            return
        dx = e.pos().x() - self.start_pos.x()
        if abs(dx) > 30:  # горизонтальное движение
            self.is_move = True
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            if dx > 0:
                self.zoom_in.emit()
            else:
                self.zoom_out.emit()
            self.start_pos = e.pos()
        super().mouseMoveEvent(e)


    def mouseReleaseEvent(self, a0: QMouseEvent):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self.is_move:
            self.is_move = False
            return  # не считаем клик, если двигали мышь

        zone_index = int(a0.pos().x() // self.zone_width)
        if zone_index == 0:
            self.zoom_out.emit()
        elif zone_index == 1:
            self.zoom_in.emit()
        elif zone_index == 2:
            self.zoom_fit.emit()
        else:
            self.zoom_close.emit()
        return super().mouseReleaseEvent(a0)


class PrevButton(CustomSvg):
    svg_path = os.path.join(Static.internal_images, "prev.svg")

    def __init__(self) -> None:
        super().__init__()
        self.load(self.svg_path)


class NextButton(CustomSvg):
    svg_path = os.path.join(Static.internal_images, "next.svg")

    def __init__(self) -> None:
        super().__init__()
        self.load(self.svg_path)


class WinImageView(UMainWidget):
    select_thumb = pyqtSignal(str)
    open_win_info = pyqtSignal(list)
    copy_path = pyqtSignal(list)
    reveal_in_finder = pyqtSignal(list)
    set_fav = pyqtSignal(tuple)
    save_files = pyqtSignal(list)
    open_in_app = pyqtSignal(tuple)
    image_not_exists = pyqtSignal()
    
    min_w, min_h = 500, 400
    ww, hh = 0, 0
    xx, yy = 0, 0

    def __init__(self, img_view_item: ImgViewItem):
        super().__init__()

        self.image_apps = {i: os.path.basename(i) for i in SharedUtils.get_apps(Static.apps)}
        self.url_to_pixmap: dict[str, QPixmap] = {}
        self.img_view_item = img_view_item
        self.current_data_item = img_view_item.start_data_item

        self.setStyleSheet("background: black;")
        self.setMinimumSize(QSize(self.min_w, self.min_h))
        self.installEventFilter(self)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_all_buttons)

        pixmap = QPixmap(10, 10)
        pixmap.fill(Qt.GlobalColor.black)
        self.img_wid = ImgWid(pixmap)
        self.central_layout.addWidget(self.img_wid)

        self.prev_image_btn = PrevButton()
        self.prev_image_btn.setParent(self)
        self.prev_image_btn.clicked.connect(lambda: self.switch_image(1))

        self.next_image_btn = NextButton()
        self.next_image_btn.setParent(self)
        self.next_image_btn.clicked.connect(lambda: self.switch_image(-1))

        self.zoom_btns = ZoomWidget()
        self.zoom_btns.setParent(self)
        self.zoom_btns.zoom_in.connect(lambda: self.zoom_cmd("in"))
        self.zoom_btns.zoom_out.connect(lambda: self.zoom_cmd("out"))
        self.zoom_btns.zoom_fit.connect(lambda: self.zoom_cmd("fit"))
        self.zoom_btns.zoom_close.connect(self.deleteLater)

        # self.hide_all_buttons()
        QTimer.singleShot(100, self.load_thumb)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM
    
    def zoom_cmd(self, flag: Literal["in", "out", "fit"]):
        actions = {
            "in": self.img_wid.zoom_in,
            "out": self.img_wid.zoom_out,
            "fit": self.img_wid.zoom_fit,
        }
        actions[flag]()

    def restart_img_wid(self, pixmap: QPixmap):
        self.img_wid.hide()  # скрываем старый
        new_wid = ImgWid(pixmap)
        new_wid.mouse_moved.connect(self.show_all_buttons)
        self.central_layout.addWidget(new_wid)

        self.img_wid.deleteLater()
        self.img_wid = new_wid
        self.img_wid.show()

        btns = (self.zoom_btns, self.prev_image_btn, self.next_image_btn)
        for i in btns:
            i.raise_()

    def load_thumb(self):
        self.restart_img_wid(self.current_data_item.pixmap)

        avaiable_mf_path = Mf.current_mf.get_avaiable_mf_path()
        if avaiable_mf_path:
            Mf.current_mf.set_mf_current_path(avaiable_mf_path)
            abs_path = Utils.get_abs_any_path(
                avaiable_mf_path,
                self.current_data_item.rel_path
            )
            
            if not os.path.exists(abs_path):
                self.image_not_exists.emit()
            else:
                self.set_title()
                self.load_image()
        else:
            self.image_not_exists.emit()
            print("img viewer > no smb")

    def load_image(self, ms = 300):

        def fin(qimage: QImage, shm: shared_memory.SharedMemory):
            qpixmap = QPixmap.fromImage(qimage)
            self.url_to_pixmap[self.current_data_item.rel_path] = qpixmap
            self.restart_img_wid(qpixmap)
            shm.close()
            shm.unlink()

        def poll():
            self.read_img_timer.stop()
            queue = self.read_img_task.process_queue
            if not queue.empty():
                item: ReadImgItem = queue.get()
                shm = shared_memory.SharedMemory(name=item.shm_name)
                img_array = np.ndarray(item.shape, dtype=np.dtype(item.dtype), buffer=shm.buf)

                if item.src == abs_path:
                    qimage_task = ImgArrayQImage(img_array)
                    qimage_task.sigs.finished_.connect(
                        lambda qimage: fin(qimage, shm)
                    )
                    UThreadPool.start(qimage_task)
            
            if not self.read_img_task.is_alive():
                self.read_img_task.terminate_join()
            else:
                self.read_img_timer.start(ms)

        if hasattr(self, "read_img_task"):
            self.read_img_task.terminate_join()
            self.read_img_timer.stop()

        if self.current_data_item.rel_path in self.url_to_pixmap:
            self.restart_img_wid(self.url_to_pixmap[self.current_data_item.rel_path])
        else:

            abs_path = Utils.get_abs_any_path(
                mf_path=Mf.current_mf.mf_current_path,
                rel_path=self.current_data_item.rel_path
            )

            self.read_img_task = ProcessWorker(
                target=ReadImg.start,
                args=(abs_path, 0, )
            )
            self.read_img_timer = QTimer(self)
            self.read_img_timer.setSingleShot(True)
            self.read_img_timer.timeout.connect(poll)

            self.read_img_task.start()
            self.read_img_timer.start(ms)

    def rotate(self, value: int):
        pixmap = self.img_wid.pixmap()
        transform = QTransform().rotate(value)
        pixmap = pixmap.transformed(transform)
        self.restart_img_wid(pixmap)

# GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI

    def hide_all_buttons(self):
        btns = (self.prev_image_btn, self.next_image_btn, self.zoom_btns)
        widget_under_cursor = QApplication.widgetAt(QCursor.pos())
        if isinstance(widget_under_cursor, QSvgWidget):
            return
        for i in btns:
            i.hide()

    def show_all_buttons(self):
        btns = (self.prev_image_btn, self.next_image_btn, self.zoom_btns)
        for i in btns:
            i.show()

    def switch_image(self, offset):
        current_index = self.img_view_item.data_items.index(self.current_data_item)
        next_index = current_index + offset
        if next_index < 0:
            next_index = len(self.img_view_item.data_items) - 1
        elif next_index >= len(self.img_view_item.data_items):
            next_index = 0
        self.current_data_item = self.img_view_item.data_items[next_index]
        self.load_thumb()
        if not self.img_view_item.is_selection:
            self.select_thumb.emit(self.current_data_item.rel_path)

    def set_title(self):
        self.setWindowTitle(
            self.current_data_item.filename
        )


# EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS 

    def keyPressEvent(self, ev: QKeyEvent | None) -> None:

        if ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if ev.key() == Qt.Key.Key_I:
                self.open_win_info.emit([self.current_data_item.rel_path, ])
            
            elif ev.key() == Qt.Key.Key_Left:
                self.rotate(-90)

            elif ev.key() == Qt.Key.Key_Right:
                self.rotate(90)

            elif ev.key() == Qt.Key.Key_Equal:
                self.img_wid.zoom_in()

            elif ev.key() == Qt.Key.Key_Minus:
                self.img_wid.zoom_out()

            elif ev.key() == Qt.Key.Key_0:
                self.img_wid.zoom_fit()

        else:
            if ev.key() == Qt.Key.Key_Left:
                self.switch_image(-1)

            elif ev.key() == Qt.Key.Key_Right:
                self.switch_image(1)

            elif ev.key() == Qt.Key.Key_Space:
                self.deleteLater()

            elif ev.key() == Qt.Key.Key_Escape:
                if self.isFullScreen():
                    self.showNormal()
                    self.raise_()
                else:
                    self.deleteLater()

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        self.menu_ = UMenu(event=ev)
        rel_paths = [self.current_data_item.rel_path, ]
        # открыть в приложении
        open_menu = USubMenu(
            f"{Lng.open_in[Cfg.lng_index]}",
            self.menu_
        )

        act = QAction(Lng.open_default[Cfg.lng_index], open_menu)
        act.triggered.connect(
            lambda: self.open_in_app.emit((rel_paths, None))
        )
        open_menu.addAction(act)
        open_menu.addSeparator()

        for app_path, basename in self.image_apps.items():
            act = QAction(basename, open_menu)
            act.triggered.connect(
                lambda _, x=app_path: self.open_in_app.emit((rel_paths, x))
            )
            open_menu.addAction(act)

        self.menu_.addMenu(open_menu)

        self.fav_action = SetFav(self.menu_, self.current_data_item.fav)
        self.fav_action.triggered.connect(
            lambda: self.set_fav.emit(
                (self.current_data_item.rel_path, not self.current_data_item.fav)
            )
        )
        self.menu_.addAction(self.fav_action)

        self.menu_.addSeparator()

        info = WinInfoAction(self.menu_)
        info.triggered.connect(
            lambda: self.open_win_info.emit(rel_paths)
        )
        self.menu_.addAction(info)

        self.menu_.addSeparator()

        reveal = RevealInFinder(self.menu_, 1)
        reveal.triggered.connect(
            lambda: self.reveal_in_finder.emit(rel_paths)
        )
        self.menu_.addAction(reveal)

        copy_path = CopyPath(self.menu_, 1)
        copy_path.triggered.connect(
            lambda: self.copy_path.emit(rel_paths)
        )
        self.menu_.addAction(copy_path)

        self.menu_.addSeparator()

        rotate_cw = QAction(Lng.clockwise[Cfg.lng_index], self.menu_)
        rotate_cw.triggered.connect(lambda: self.rotate(90))
        self.menu_.addAction(rotate_cw)

        rotate_ccw = QAction(Lng.counter_clockwise[Cfg.lng_index], self.menu_)
        rotate_ccw.triggered.connect(lambda: self.rotate(-90))
        self.menu_.addAction(rotate_ccw)

        self.menu_.addSeparator()

        save = Save(self.menu_, 1)
        save.triggered.connect(
            lambda: self.save_files.emit(rel_paths)
        )
        self.menu_.addAction(save)

        self.menu_.show_menu()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        vertical_center = a0.size().height() // 2 - self.next_image_btn.height() // 2
        right_window_side = a0.size().width() - self.next_image_btn.width()
        self.prev_image_btn.move(10, vertical_center)
        self.next_image_btn.move(right_window_side - 10, vertical_center)

        horizontal_center = a0.size().width() // 2 - self.zoom_btns.width() // 2
        bottom_window_side = a0.size().height() - self.zoom_btns.height()
        self.zoom_btns.move(horizontal_center, bottom_window_side - 50)

        self.setFocus()

        return super().resizeEvent(a0)
    
    def enterEvent(self, event):
        self.show_all_buttons()
        self.mouse_move_timer.start(2000)
        return super().enterEvent(event)

    def leaveEvent(self, a0: QEvent | None) -> None:
        self.hide_all_buttons()
        return super().leaveEvent(a0)

    def closeEvent(self, a0):
        try:
            self.read_img_task.terminate_join()
            self.read_img_timer.stop()
        except AttributeError as e:
            print("close img view error", e)
        WinImageView.ww = self.size().width()
        WinImageView.hh = self.size().height()
        WinImageView.xx = self.x()
        WinImageView.yy = self.y()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        try:
            self.read_img_task.terminate_join()
            self.read_img_timer.stop()
        except AttributeError as e:
            print("close img view error", e)
        WinImageView.ww = self.size().width()
        WinImageView.hh = self.size().height()
        WinImageView.xx = self.x()
        WinImageView.yy = self.y()
        return super().deleteLater()