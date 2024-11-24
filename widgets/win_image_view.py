import os

import sqlalchemy
from PyQt5.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (QColor, QContextMenuEvent, QKeyEvent, QMouseEvent,
                         QPainter, QPaintEvent, QPixmap, QResizeEvent)
from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from base_widgets import LayoutHor, LayoutVer, SvgShadowed
from base_widgets.context import ContextCustom
from base_widgets.wins import WinChild
from cfg import PSD_TIFF, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp
from utils.utils import URunnable, UThreadPool, Utils

from .actions import CopyPath, FavActionDb, OpenInfoDb, OpenWins, Reveal, Save
from .grid.thumbnail import Thumbnail

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

IMAGES = "images"
ZOOM_OUT = os.path.join(IMAGES, "zoom_out.svg")
ZOOM_IN = os.path.join(IMAGES, "zoom_in.svg")
ZOOM_FIT = os.path.join(IMAGES, "zoom_fit.svg")
CLOSE_ = os.path.join(IMAGES, "zoom_close.svg")
PREV_ = os.path.join(IMAGES, "prev.svg")
NEXT_ = os.path.join(IMAGES, "next.svg")

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

    @URunnable.set_running_state
    def run(self):
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(
            THUMBS.c.hash_path
            ).where(
                THUMBS.c.src == self.short_src
                )
        res = conn.execute(q).scalar()
        conn.close()

        if res:
            small_img = Utils.read_image_hash(res)
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
    images: dict[str, QPixmap] = {}

    def __init__(self, full_src: str):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.full_src = full_src

    @URunnable.set_running_state
    def run(self):

        if self.full_src not in LoadImage.images:
        
            img = Utils.read_image(full_src=self.full_src)

            if not self.full_src.endswith(PSD_TIFF):
                img = Utils.array_color(img, "BGR")

            if img is not None:
                self.pixmap = Utils.pixmap_from_array(img)
                LoadImage.images[self.full_src] = self.pixmap

        else:
            self.pixmap = LoadImage.images.get(self.full_src)

        if not hasattr(self, "pixmap"):
            print("не могу загрузить крупное изображение")
            self.pixmap = QPixmap(0, 0)

        if len(LoadImage.images) > 50:
            LoadImage.images.pop(next(iter(LoadImage.images)))

        image_data = ImageData(
            src=self.full_src,
            pixmap=self.pixmap
        )
        self.signals_.finished_.emit(image_data)


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
    def __init__(self, short_src: str):
        super().__init__()
        self.enable_min()

        self.short_src_list = list(Thumbnail.path_to_wid.keys())
        self.short_src = short_src
        self.wid = Thumbnail.path_to_wid.get(self.short_src)

        self.setStyleSheet(IMG_VIEW_STYLE)
        self.setMinimumSize(QSize(500, 400))
        self.resize(JsonData.imgview_g["aw"], JsonData.imgview_g["ah"])
        self.installEventFilter(self)

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_all_buttons)

        self.image_label = ImageWidget()
        self.content_lay_v.addWidget(self.image_label)

        self.prev_image_btn = PrevImageBtn(self.content_wid)
        self.prev_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("-")

        self.next_image_btn = NextImageBtn(self.content_wid)
        self.next_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("+")

        self.zoom_btns = ZoomBtns(parent=self.content_wid)
        self.zoom_btns.zoom_in.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_in()
        )
        self.zoom_btns.zoom_out.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_out()
        )
        self.zoom_btns.zoom_fit.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_reset()
        )
        self.zoom_btns.zoom_close.mouseReleaseEvent = self.close_

        self.hide_all_buttons()
        QTimer.singleShot(100, self.first_load)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM


    def first_load(self):
        coll_folder = Utils.get_coll_folder(brand_ind=JsonData.brand_ind)
        if not coll_folder:
            OpenWins.smb(self)

        self.load_thumb()

    def load_thumb(self):
        self.setFocus()
        self.img_viewer_title()
        task = LoadThumb(short_src=self.short_src)
        task.signals_.finished_.connect(self.load_thumb_fin)
        UThreadPool.pool.start(task)

    def load_thumb_fin(self, data: ImageData):
        self.image_label.set_image(data.pixmap)

        coll_folder = Utils.get_coll_folder(brand_ind=JsonData.brand_ind)

        if coll_folder:
            self.full_src = Utils.get_full_src(coll_folder, self.short_src)
            self.load_image()

        else:
            print("img viewer > no smb")

    def load_image(self):
        cmd_ = lambda data: self.load_image_fin(data=data, full_src=self.full_src)

        img_thread = LoadImage(full_src=self.full_src)
        img_thread.signals_.finished_.connect(cmd_)
        UThreadPool.pool.start(img_thread)

    def load_image_fin(self, data: ImageData, full_src: str):
        if data.pixmap.width() == 0 or data.src != full_src:
            return
        
        elif isinstance(data.pixmap, QPixmap):
            self.image_label.set_image(data.pixmap)

    def close_(self, *args):
        LoadImage.images.clear()
        self.close()


# GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI

    def hide_all_buttons(self):
        for i in (self.prev_image_btn, self.next_image_btn, self.zoom_btns):
            if i.underMouse():
                return
        self.zoom_btns.hide()
        self.prev_image_btn.hide()
        self.next_image_btn.hide()

    def switch_image(self, offset):
        current_index = self.short_src_list.index(self.short_src)
        new_index = current_index + offset
        total_ = len(self.short_src_list)

        if new_index > total_:
            new_index = 0

        elif new_index < 0:
            new_index = total_

        # 
        # сетка = Thumbnail.path_to_wid = сетка thumbnails
        # 

        # ищем новый src после или до предыдущего
        # так как мы сохранили список src сетки, то новый src будет найден
        # но не факт, что он уже есть в сетке
        new_short_src = self.short_src_list[new_index]

        # ищем виджет в актуальной сетке, которая могла обновиться в фоне
        new_wid = Thumbnail.path_to_wid.get(new_short_src)

        # если виджет не найден в сетке
        # значит сетка обновилась в фоне с новыми виджетами
        # формируем заново список src соответсвуя новой сетке
        # берем первый src из этого списка
        # и первый виджет из сетки
        if not new_wid:
            self.short_src_list = list(Thumbnail.path_to_wid.keys())
            self.short_src = self.short_src_list[0]
            self.wid = Thumbnail.path_to_wid.get(self.short_src)

        # если виджет найден, тоне факт, что список src актуален
        # то есть сетка все равно могла быть перетасована
        # формируем заново список src соответсвуя новой сетке
        # так как мы ранее выяснили, что виджет есть в новой сетке
        # то есть и src в списке src
        # поэтому берем ранее найденный src и виджет
        else:
            self.short_src_list = list(Thumbnail.path_to_wid.keys())
            self.short_src = new_short_src
            self.wid = new_wid

        self.load_thumb()
        # SignalsApp.all_.thumbnail_select.emit(self.short_src)
        self.wid.select.emit(self.short_src)

    def img_viewer_title(self):
        self.setWindowTitle(f"{self.wid.collection}: {self.wid.name}")

    def button_switch_cmd(self, flag: str) -> None:
        if flag == "+":
            self.switch_image(1)
        else:
            self.switch_image(-1)
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def change_fav(self, value: int):
        self.wid.change_fav(value)
        self.img_viewer_title()

# EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS 

    def keyPressEvent(self, ev: QKeyEvent | None) -> None:
        if ev.key() == Qt.Key.Key_Left:
            self.switch_image(-1)

        elif ev.key() == Qt.Key.Key_Right:
            self.switch_image(1)

        elif ev.key() == Qt.Key.Key_Escape:
            self.close_(ev)

        elif ev.key() == Qt.Key.Key_Equal:
            self.image_label.zoom_in()

        elif ev.key() == Qt.Key.Key_Minus:
            self.image_label.zoom_out()

        elif ev.key() == Qt.Key.Key_0:
            self.image_label.zoom_reset()

        elif ev.modifiers() & Qt.KeyboardModifier.ControlModifier and ev.key() == Qt.Key.Key_I:

            coll_folder = Utils.get_coll_folder(brand_ind=JsonData.brand_ind)

            if coll_folder:

                OpenWins.info_db(
                    parent_=self,
                    short_src=self.short_src,
                    coll_folder=coll_folder
                )

            else:
                OpenWins.smb(parent_=self)

        return super().keyPressEvent(ev)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        self.menu_ = ContextCustom(event=ev)

        info = OpenInfoDb(
            parent=self.menu_,
            win=self,
            short_src=self.short_src
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

        JsonData.imgview_g.update({"aw": a0.size().width(), "ah": a0.size().height()})

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
