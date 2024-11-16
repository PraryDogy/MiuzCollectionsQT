import os

import sqlalchemy
from PyQt5.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (QColor, QContextMenuEvent, QKeyEvent, QMouseEvent,
                         QPainter, QPaintEvent, QPixmap, QResizeEvent)
from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from base_widgets import LayoutHor, LayoutVer, SvgShadowed
from base_widgets.context import ContextCustom
from base_widgets.wins import WinChild
from cfg import PIXMAP_SIZE, PSD_TIFF, Dynamic, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp
from styles import Names, Themes
from utils.utils import URunnable, UThreadPool, Utils

from .actions import CopyPath, OpenInfo, Reveal, Save
from .win_info import WinInfo
from .win_smb import WinSmb


class ImageData:
    __slots__ = ["src", "width", "pixmap"]
    def __init__(self, src: str, width: int, pixmap: QPixmap):
        self.src = src
        self.width = width
        self.pixmap = pixmap


class WorkerSignals(QObject):
    finished_ = pyqtSignal(object)


class LoadThumb(URunnable):
    def __init__(self, src: str):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.src = src

    def run(self):
        small_src = self.src.replace(JsonData.coll_folder, "")

        conn = Dbase.engine.connect()
        q = (sqlalchemy.select(THUMBS.c.hash_path).where(THUMBS.c.src == small_src))
        res = conn.execute(q).scalar()
        conn.close()

        if res:
            small_img = Utils.read_image_hash(res)
            pixmap = Utils.pixmap_from_array(small_img)
        else:
            pixmap = QPixmap(1, 1)
            pixmap.fill(QColor(128, 128, 128))


class LoadImage(URunnable):
    images: dict[str, QPixmap] = {}

    def __init__(self, src: str):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.src = src

    @URunnable.set_running_state
    def run(self):

        if self.src not in LoadImage.images:
            img = Utils.read_image(self.src)

            if not self.src.endswith(PSD_TIFF):
                img = Utils.array_color(img, "BGR")

            pixmap = Utils.pixmap_from_array(img)
            LoadImage.images[self.src] = pixmap

        else:
            pixmap = LoadImage.images.get(self.src)

        if pixmap is None:
            print("не могу загрузить крупное изображение")
            pixmap = QPixmap(1, 1)
            pixmap.fill(QColor(128, 128, 128))

        if len(LoadImage.images) > 50:
            LoadImage.images.pop(next(iter(LoadImage.images)))

        image_data = ImageData(self.src, pixmap.width(), pixmap)
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

        self.setObjectName(Names.navi_zoom)
        self.setStyleSheet(Themes.current)

        h_layout = LayoutHor()
        self.setLayout(h_layout)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.zoom_out = SvgShadowed(os.path.join("images", "zoom_out.svg"), 45)
        h_layout.addWidget(self.zoom_out)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_in = SvgShadowed(os.path.join("images", "zoom_in.svg"), 45)
        h_layout.addWidget(self.zoom_in)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_fit = SvgShadowed(os.path.join("images", "zoom_fit.svg"), 45)
        h_layout.addWidget(self.zoom_fit)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_close = SvgShadowed(os.path.join("images", "zoom_close.svg"), 45)
        h_layout.addWidget(self.zoom_close)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.adjustSize()


class SwitchImageBtn(QFrame):
    def __init__(self, icon_name: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName(Names.navi_switch)
        self.setStyleSheet(Themes.current)
        self.setFixedSize(54, 54) # 27px border-radius, 27 * 2 for round shape

        v_layout = LayoutVer()
        self.setLayout(v_layout)

        btn = SvgShadowed(os.path.join("images", icon_name), 50)
        v_layout.addWidget(btn)


class PrevImageBtn(SwitchImageBtn):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("prev.svg", parent)


class NextImageBtn(SwitchImageBtn):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("next.svg", parent)


class WinImageView(WinChild):
    def __init__(self, src: str, path_to_wid: dict[str, QWidget]):

        try:
            Dynamic.image_viewer.close()
        except (AttributeError, RuntimeError) as e:
            pass

        super().__init__()

        self.close_btn_cmd(self.close_)
        self.min_btn_disable()
        self.setMinimumSize(QSize(500, 400))
        self.resize(JsonData.imgview_g["aw"], JsonData.imgview_g["ah"])
        self.installEventFilter(self)

        self.content_lay_v.setContentsMargins(10, 0, 10, 0)
        self.content_wid.setObjectName("img_view_bg")
        self.content_wid.setStyleSheet(Themes.current)

        self.src = src
        self.all_images = list(path_to_wid.keys())

        self.collection = None
        Dynamic.image_viewer = self

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
        self.zoom_btns.zoom_in.mouseReleaseEvent = lambda e: self.image_label.zoom_in()
        self.zoom_btns.zoom_out.mouseReleaseEvent = lambda e: self.image_label.zoom_out()
        self.zoom_btns.zoom_fit.mouseReleaseEvent = lambda e: self.image_label.zoom_reset()
        self.zoom_btns.zoom_close.mouseReleaseEvent = self.close_

        self.hide_all_buttons()
        self.setFocus()
        self.load_thumbnail()

        QTimer.singleShot(300, self.smb_check)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM

    def smb_check(self):
        if not Utils.smb_check():
            self.win_smb = WinSmb()
            self.win_smb.center_relative_parent(self)
            self.win_smb.show()

    def load_thumbnail(self):

        if self.src not in LoadImage.images:
            self.set_titlebar_title(Dynamic.lng.loading)

            # преобразуем полный путь в относительный для работы в ДБ
            small_src = self.src.replace(JsonData.coll_folder, "")

            conn = Dbase.engine.connect()
            q = (sqlalchemy.select(THUMBS.c.hash_path).where(THUMBS.c.src == small_src))
            res = conn.execute(q).scalar()
            conn.close()

            if res:
                small_img = Utils.read_image_hash(res)
                pixmap = Utils.pixmap_from_array(small_img)
            else:
                pixmap = QPixmap(1, 1)
                pixmap.fill(QColor(128, 128, 128))

            self.image_label.set_image(pixmap)

        if Utils.smb_check():
            self.load_image_thread()
        else:
            print("img viewer > no smb", self.src)

    def load_image_thread(self):
        img_thread = LoadImage(self.src)
        img_thread.signals_.finished_.connect(self.load_image_finished)
        UThreadPool.pool.start(img_thread)

    def load_image_finished(self, data: ImageData):
        if data.width == 0 or data.src != self.src:
            print("img viewer load finished, but this image don't need, it's OK")
        
        elif isinstance(data.pixmap, QPixmap):
            self.image_label.set_image(data.pixmap)
            self.set_image_title()

    def close_(self, *args):
        LoadImage.images.clear()
        Dynamic.image_viewer = None
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
        try:
            current_index = self.all_images.index(self.src)
        except Exception as e:
            current_index = 0

        total_images = len(self.all_images)
        new_index = (current_index + offset) % total_images
        self.src = self.all_images[new_index]
        SignalsApp.all_.thumbnail_select.emit(self.src)
        self.load_thumbnail()

    def cut_text(self, text: str) -> str:
        limit = 40
        if len(text) > limit:
            return text[:limit] + "..."
        return text

    def set_image_title(self):
        self.collection = Utils.get_coll_name(self.src)
        cut_coll = self.cut_text(Utils.get_coll_name(self.src))
        name = self.cut_text(os.path.basename(self.src))

        self.set_titlebar_title(f"{cut_coll} - {name}")

    def button_switch_cmd(self, flag: str) -> None:
        if flag == "+":
            self.switch_image(1)
        else:
            self.switch_image(-1)
        self.setFocus()
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

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
            if Utils.smb_check():
                self.win_info = WinInfo(src=self.src)
                self.win_info.center_relative_parent(self)
                self.win_info.show()
            else:
                self.win_smb = WinSmb()
                self.win_smb.center_relative_parent(self)
                self.win_smb.show()

        return super().keyPressEvent(ev)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.menu_ = ContextCustom(event=ev)

            info = OpenInfo(parent=self, src=self.src)
            self.menu_.addAction(info)

            self.menu_.addSeparator()

            copy = CopyPath(parent=self, src=self.src)
            self.menu_.addAction(copy)

            reveal = Reveal(parent=self, src=self.src)
            self.menu_.addAction(reveal)

            save_as = Save(parent=self, src=self.src, save_as=True)
            self.menu_.addAction(save_as)

            save = Save(parent=self, src=self.src, save_as=False)
            self.menu_.addAction(save)

            self.menu_.show_menu()

            return super().contextMenuEvent(ev)

        except Exception as e:
            Utils.print_err(error=e)

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
