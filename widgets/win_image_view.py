import gc
import os
from typing import Literal

import sqlalchemy
from PyQt5.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (QColor, QContextMenuEvent, QKeyEvent, QMouseEvent,
                         QPainter, QPaintEvent, QPixmap, QPixmapCache,
                         QResizeEvent)
from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from base_widgets import LayoutHor, LayoutVer, SvgShadowed
from base_widgets.context import ContextCustom
from base_widgets.wins import WinChild
from cfg import Dynamic, Static
from database import THUMBS, Dbase
from main_folders import MainFolder
from utils.utils import Utils

from ._runnable import URunnable, UThreadPool
from .actions import (CopyName, CopyPath, FavActionDb, Reveal, Save,
                      WinInfoAction)
from .grid.cell_widgets import Thumbnail
from .win_info import WinInfo
from .win_smb import WinSmb

IMG_VIEW_STYLE = """
    background: black;
"""

ZOOM_STYLE = """
    background-color: rgba(128, 128, 128, 0.40);
    border-radius: 15px;
"""

NAVI_STYLE = """
    background-color: rgba(128, 128, 128, 0.40);
    border-radius: 27px;
"""

ZOOM_OUT = os.path.join(Static.images_dir, "zoom_out.svg")
ZOOM_IN = os.path.join(Static.images_dir, "zoom_in.svg")
ZOOM_FIT = os.path.join(Static.images_dir, "zoom_fit.svg")
CLOSE_ = os.path.join(Static.images_dir, "zoom_close.svg")
PREV_ = os.path.join(Static.images_dir, "prev.svg")
NEXT_ = os.path.join(Static.images_dir, "next.svg")

class ImageData:
    __slots__ = ["src", "pixmap"]
    def __init__(self, src: str, pixmap: QPixmap):
        self.src = src
        self.pixmap: QPixmap = pixmap


class WorkerSignals(QObject):
    finished_ = pyqtSignal(object)


class LoadThumb(URunnable):
    def __init__(self, short_src: str):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.short_src = short_src

    def task(self):
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(
            THUMBS.c.short_hash
            ).where(
                THUMBS.c.short_src == self.short_src
                )
        short_hash = conn.execute(q).scalar()
        conn.close()

        if short_hash:
            full_hash = Utils.get_full_hash(short_hash)
            small_img = Utils.read_image_hash(full_hash)
            small_img = Utils.desaturate_image(image=small_img, factor=0.2)
            pixmap = Utils.pixmap_from_array(small_img)
        else:
            pixmap = QPixmap(1, 1)
            pixmap.fill(QColor(128, 128, 128))

        image_data = ImageData(
            src=self.short_src,
            pixmap=pixmap
        )
        self.signals_.finished_.emit(image_data)


class LoadImage(URunnable):
    max_images_count = 50

    def __init__(self, full_src: str, cached_images: dict[str, QPixmap]):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.full_src = full_src
        self.cached_images = cached_images

    def task(self):

        if self.full_src not in self.cached_images:
        
            img = Utils.read_image(self.full_src)

            if img is not None:
                img = Utils.desaturate_image(image=img, factor=0.2)
                self.pixmap = Utils.pixmap_from_array(img)
                self.cached_images[self.full_src] = self.pixmap
            
            del img
            gc.collect()

        else:
            self.pixmap = self.cached_images.get(self.full_src)

        if not hasattr(self, "pixmap"):
            print("не могу загрузить крупное изображение")
            self.pixmap = QPixmap(0, 0)

        if len(self.cached_images) > self.max_images_count:
            self.cached_images.pop(next(iter(self.cached_images)))

        image_data = ImageData(
            src=self.full_src,
            pixmap=self.pixmap
        )

        try:
            self.signals_.finished_.emit(image_data)
        except RuntimeError:
            ...

        # === очищаем ссылки
        del self.pixmap
        self.signals_ = None
        gc.collect()
        QPixmapCache.clear()


class ImageWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_pixmap: QPixmap = None
        self.scale_factor: float = 1.0
        self.offset = QPoint(0, 0)
        self.w, self.h = 0, 0

    def set_image(self, pixmap: QPixmap):
        self.current_pixmap = pixmap
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.w, self.h = self.width(), self.height()

        self.current_pixmap.scaled(
            self.w, self.h, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
            )
        self.update()

    def zoom_in(self):
        self.scale_factor *= 1.1
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def zoom_out(self):
        self.scale_factor /= 1.1
        self.update()

    def zoom_reset(self):
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = ev.pos()
        return super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent | None) -> None:
        if ev.buttons() == Qt.MouseButton.LeftButton and self.scale_factor > 1.0:
            delta = ev.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = ev.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
        return super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if self.scale_factor > 1.0:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        return super().mouseReleaseEvent(ev)

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        if self.current_pixmap is not None:
            painter = QPainter(self)
            scaled_pixmap = self.current_pixmap.scaled(
                int(self.w * self.scale_factor),
                int(self.h * self.scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
                )

            offset = self.offset + QPoint(
                int((self.width() - scaled_pixmap.width()) / 2),
                int((self.height() - scaled_pixmap.height()) / 2)
                )
            painter.drawPixmap(offset, scaled_pixmap)
        return super().paintEvent(a0)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.w, self.h = self.width(), self.height()
        self.update()
        return super().resizeEvent(a0)
    

class ZoomBtns(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(ZOOM_STYLE)

        h_layout = LayoutHor()
        self.setLayout(h_layout)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.zoom_out = SvgShadowed(ZOOM_OUT, 45)
        h_layout.addWidget(self.zoom_out)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_in = SvgShadowed(ZOOM_IN, 45)
        h_layout.addWidget(self.zoom_in)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_fit = SvgShadowed(ZOOM_FIT, 45)
        h_layout.addWidget(self.zoom_fit)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_close = SvgShadowed(CLOSE_, 45)
        h_layout.addWidget(self.zoom_close)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.adjustSize()


class SwitchImageBtn(QFrame):
    def __init__(self, path: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setFixedSize(54, 54) # 27px border-radius, 27 * 2 for round shape
        self.setStyleSheet(NAVI_STYLE)

        v_layout = LayoutVer()
        self.setLayout(v_layout)

        btn = SvgShadowed(path, 50)
        v_layout.addWidget(btn)


class PrevImageBtn(SwitchImageBtn):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(PREV_, parent)


class NextImageBtn(SwitchImageBtn):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(NEXT_, parent)


class WinImageView(WinChild):
    task_count_limit = 10
    switch_image_sig = pyqtSignal(object)
    closed_ = pyqtSignal()

    def __init__(self, short_src: str, path_to_wid: dict[str, Thumbnail], is_selection: bool):
        super().__init__()

        self.cached_images: dict[str, QPixmap] = {}
        self.is_selection = is_selection
        self.path_to_wid = path_to_wid
        self.short_src_list = list(path_to_wid.keys())
        self.short_src = short_src
        self.wid = path_to_wid.get(self.short_src)
        self.task_count = 0

        self.setStyleSheet(IMG_VIEW_STYLE)
        self.setMinimumSize(QSize(500, 400))
        self.resize(Dynamic.imgview_g["aw"], Dynamic.imgview_g["ah"])
        self.installEventFilter(self)

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_all_buttons)

        self.image_label = ImageWidget()
        self.central_layout.addWidget(self.image_label)
        self.prev_image_btn = PrevImageBtn(self.centralWidget())
        self.prev_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("-")

        self.next_image_btn = NextImageBtn(self.centralWidget())
        self.next_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("+")

        self.zoom_btns = ZoomBtns(parent=self.centralWidget())
        self.zoom_btns.zoom_in.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_in()
        )
        self.zoom_btns.zoom_out.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_out()
        )
        self.zoom_btns.zoom_fit.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_reset()
        )
        self.zoom_btns.zoom_close.mouseReleaseEvent = lambda e: self.deleteLater()

        self.hide_all_buttons()
        QTimer.singleShot(100, self.first_load)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM


    def first_load(self):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        if not coll_folder:
            self.open_smb_win()

        self.load_thumb()

    def load_thumb(self):
        self.setFocus()
        self.img_viewer_title()
        task = LoadThumb(short_src=self.short_src)
        task.signals_.finished_.connect(self.load_thumb_fin)
        UThreadPool.start(task)

    def load_thumb_fin(self, data: ImageData):
        self.image_label.set_image(data.pixmap)
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()

        if coll_folder:
            self.full_src = Utils.get_full_src(coll_folder, self.short_src)
            self.load_image()

        else:
            print("img viewer > no smb")

    def load_image(self):
        self.task_count += 1
        cmd_ = lambda data: self.load_image_fin(data, self.full_src)

        img_thread = LoadImage(self.full_src, self.cached_images)
        img_thread.signals_.finished_.connect(cmd_)
        UThreadPool.start(img_thread)

    def load_image_fin(self, data: ImageData, full_src: str):
        self.task_count -= 1

        if data.pixmap.width() == 0 or data.src != full_src:
            return
        
        elif isinstance(data.pixmap, QPixmap):
            try:
                self.image_label.set_image(data.pixmap)
            except RuntimeError:
                ...

# GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI

    def hide_all_buttons(self):
        for i in (self.prev_image_btn, self.next_image_btn, self.zoom_btns):
            if i.underMouse():
                return
        self.zoom_btns.hide()
        self.prev_image_btn.hide()
        self.next_image_btn.hide()

    def switch_image(self, offset):
        if self.task_count == WinImageView.task_count_limit:
            return

        # мы формируем актуальный список src из актуальной сетки изображений
        self.short_src_list = list(self.path_to_wid.keys())

        if self.short_src in self.short_src_list:
            current_index = self.short_src_list.index(self.short_src)
            new_index = current_index + offset
        else:
            new_index = 0

        if new_index == len(self.short_src_list):
            new_index = 0

        elif new_index < 0:
            new_index = len(self.short_src_list) - 1

        # 
        # сетка = Thumbnail.path_to_wid = сетка thumbnails
        # 

        # ищем новый src после или до предыдущего
        # так как мы сохранили список src сетки, то новый src будет найден
        # но не факт, что он уже есть в сетке
        try:
            new_short_src = self.short_src_list[new_index]
        except IndexError as e:
            print(e)
            return

        # ищем виджет в актуальной сетке, которая могла обновиться в фоне
        new_wid = self.path_to_wid.get(new_short_src)

        # если виджет не найден в сетке
        # значит сетка обновилась в фоне с новыми виджетами
        # формируем заново список src соответсвуя новой сетке
        # берем первый src из этого списка
        # и первый виджет из сетки
        if not new_wid:
            self.short_src = self.short_src_list[0]
            self.wid = self.path_to_wid.get(self.short_src)

        # если виджет найден, тоне факт, что список src актуален
        # то есть сетка все равно могла быть перетасована
        # формируем заново список src соответсвуя новой сетке
        # так как мы ранее выяснили, что виджет есть в новой сетке
        # то есть и src в списке src
        # поэтому берем ранее найденный src и виджет
        else:
            self.short_src = new_short_src
            self.wid = new_wid

        self.load_thumb()

        # если был выделен один виджет для просмотра, значит мы просматриваем
        # все виджеты в сетке и, по мере пролистывания изображений,
        # выделяем просматриваемый виджет
        # но если было выбрано для просмотра х число виджетов, мы не 
        # снимаем с них выделение
        if not self.is_selection:
            self.switch_image_sig.emit(self.short_src)

    def img_viewer_title(self):
        self.setWindowTitle(f"{self.wid.collection}: {self.wid.name}")

    def button_switch_cmd(self, flag: Literal["+", "-"]) -> None:
        if flag == "+":
            self.switch_image(1)
        else:
            self.switch_image(-1)
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def change_fav(self, value: int):
        self.wid.change_fav(value)
        self.img_viewer_title()

    def open_info_win_delayed(self):
        self.info_win.adjustSize()
        self.info_win.center_relative_parent(self)
        self.info_win.show()

    def open_smb_win(self):
        self.smb_win = WinSmb()
        self.smb_win.adjustSize()
        self.smb_win.center_relative_parent(self)
        self.smb_win.show()

# EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS 

    def keyPressEvent(self, ev: QKeyEvent | None) -> None:
        if ev.key() == Qt.Key.Key_Left:
            self.switch_image(-1)

        elif ev.key() == Qt.Key.Key_Right:
            self.switch_image(1)

        elif ev.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.raise_()
            else:
                self.deleteLater()

        elif ev.key() == Qt.Key.Key_Equal:
            self.image_label.zoom_in()

        elif ev.key() == Qt.Key.Key_Minus:
            self.image_label.zoom_out()

        elif ev.key() == Qt.Key.Key_0:
            self.image_label.zoom_reset()

        elif ev.modifiers() & Qt.KeyboardModifier.ControlModifier and ev.key() == Qt.Key.Key_I:
            MainFolder.current.set_current_path()
            coll_folder = MainFolder.current.get_current_path()
            if coll_folder:
                full_src = Utils.get_full_src(coll_folder, self.short_src)
                urls = [full_src]
                self.info_win = WinInfo(urls)
                self.info_win.finished_.connect(self.open_info_win_delayed)
            else:
                self.open_smb_win()

        return super().keyPressEvent(ev)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        self.menu_ = ContextCustom(event=ev)
        urls = [self.short_src]

        info = WinInfoAction(
            parent=self.menu_,
            win=self,
            urls=urls
        )
        self.menu_.addAction(info)

        self.fav_action = FavActionDb(
            parent=self.menu_,
            short_src=self.short_src,
            fav_value=self.wid.fav_value
        )
        self.fav_action.finished_.connect(self.change_fav)
        self.menu_.addAction(self.fav_action)

        self.menu_.addSeparator()

        copy = CopyPath(
            parent=self.menu_,
            win=self,
            short_src=self.short_src
        )
        self.menu_.addAction(copy)

        copy_name = CopyName(
            parent=self.menu_,
            win=self,
            short_src=self.short_src
        )
        self.menu_.addAction(copy_name)

        reveal = Reveal(
            parent=self.menu_,
            win=self,
            short_src=self.short_src
        )
        self.menu_.addAction(reveal)

        save_as = Save(
            parent=self.menu_, 
            win=self,
            short_src=self.short_src,
            save_as=True
        )
        self.menu_.addAction(save_as)

        save = Save(
            parent=self.menu_,
            win=self,
            short_src=self.short_src,
            save_as=False
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

        Dynamic.imgview_g.update({"aw": a0.size().width(), "ah": a0.size().height()})

        return super().resizeEvent(a0)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == 129:
            self.mouse_move_timer.stop()
            self.prev_image_btn.show()
            self.next_image_btn.show()
            self.zoom_btns.show()
            self.mouse_move_timer.start(2000)
        return super().eventFilter(a0, a1)

    def leaveEvent(self, a0: QEvent | None) -> None:
        self.hide_all_buttons()
        return super().leaveEvent(a0)

    def closeEvent(self, a0):
        self.cached_images.clear()
        QPixmapCache.clear()
        gc.collect()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.cached_images.clear()
        QPixmapCache.clear()
        gc.collect()
        return super().deleteLater()