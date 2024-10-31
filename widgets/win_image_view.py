import os

import sqlalchemy
from PyQt5.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (QContextMenuEvent, QKeyEvent, QMouseEvent, QPainter,
                         QPaintEvent, QPixmap, QResizeEvent)
from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from base_widgets import LayoutH, LayoutV, SvgShadowed, WinImgViewBase
from cfg import cnf
from database import Dbase, ThumbsMd
from signals import signals_app, signals_app
from styles import Names, Themes
from utils import ImageUtils, MainUtils, MyThread, get_image_size

from .context_img import ContextImg
from .wid_notification import Notification
from .win_smb import WinSmb


class Shared:
    loaded_images: dict[str, QPixmap] = {}


class ImageData:
    __slots__ = ["src", "width", "pixmap"]
    def __init__(self, src: str, width: int, pixmap: QPixmap):
        self.src = src
        self.width = width
        self.pixmap = pixmap


class LoadImageThread(MyThread):
    finished = pyqtSignal(object)

    def __init__(self, img_src: str):
        super().__init__(parent=None)
        self.img_src = img_src

    def run(self):
        try:
            if not os.path.exists(self.img_src):
                print("image viewer thread no connection")
                return

            if self.img_src not in Shared.loaded_images:

                img = ImageUtils.read_image(self.img_src)
                img = ImageUtils.array_bgr_to_rgb(img)
                pixmap = ImageUtils.pixmap_from_array(img)
                Shared.loaded_images[self.img_src] = pixmap

            else:
                pixmap = Shared.loaded_images.get(self.img_src)

        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            pixmap = None

        if len(Shared.loaded_images) > 50:
            Shared.loaded_images.pop(next(iter(Shared.loaded_images)))

        self.finished.emit(ImageData(self.img_src, pixmap.width(), pixmap))
        self.remove_threads()


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

        h_layout = LayoutH()
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

        v_layout = LayoutV()
        self.setLayout(v_layout)

        btn = SvgShadowed(os.path.join("images", icon_name), 50)
        v_layout.addWidget(btn)


class PrevImageBtn(SwitchImageBtn):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("prev.svg", parent)


class NextImageBtn(SwitchImageBtn):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("next.svg", parent)


class WinImageView(WinImgViewBase):
    def __init__(self, parent: QWidget, img_src: str):

        try:
            cnf.image_viewer.close()
        except (AttributeError, RuntimeError) as e:
            pass

        super().__init__(close_func=self.my_close)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(QSize(500, 400))
        self.resize(cnf.imgview_g["aw"], cnf.imgview_g["ah"])
        self.installEventFilter(self)

        self.img_src = img_src
        self.collection = None
        cnf.image_viewer = self

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_all_buttons)

        self.image_label = ImageWidget()
        self.content_layout.addWidget(self.image_label)

        self.notification = Notification(self.content_wid)
        self.notification.move(10, 2) # 10 left side, 10 right side, 2 top side
        signals_app.noti_img_view.connect(self.notification.show_notify)

        self.prev_image_btn = PrevImageBtn(self.content_wid)
        self.prev_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("-")

        self.next_image_btn = NextImageBtn(self.content_wid)
        self.next_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("+")

        self.zoom_btns = ZoomBtns(parent=self.content_wid)
        self.zoom_btns.zoom_in.mouseReleaseEvent = lambda e: self.image_label.zoom_in()
        self.zoom_btns.zoom_out.mouseReleaseEvent = lambda e: self.image_label.zoom_out()
        self.zoom_btns.zoom_fit.mouseReleaseEvent = lambda e: self.image_label.zoom_reset()
        self.zoom_btns.zoom_close.mouseReleaseEvent = self.my_close

        self.hide_all_buttons()
        self.setFocus()
        self.center_win(parent=parent)
        self.load_thumbnail()

        QTimer.singleShot(300, self.smb_check_first)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM

    def smb_check_first(self):
        if not MainUtils.smb_check():
            signals_app.migrate_finished.connect(self.finalize_smb)
            self.win_smb = WinSmb(parent=self)
            self.win_smb.show()

    def finalize_smb(self):
        name = os.path.basename(self.img_src)
        for k, v in cnf.images.items():
            if name == v["filename"] and self.collection == v["collection"]:
                self.img_src = k
                self.load_image_thread()
                return
                
    def load_thumbnail(self):
        if self.img_src not in Shared.loaded_images:
            self.set_title(cnf.lng.loading)

            q = (sqlalchemy.select(ThumbsMd.img150)
                .filter(ThumbsMd.src == self.img_src))
            conn = Dbase.engine.connect()

            try:
                thumbnail = conn.execute(q).first()[0]
                conn.close()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)
                return

            pixmap = QPixmap()
            pixmap.loadFromData(thumbnail)
            self.image_label.set_image(pixmap)

        self.load_image_thread()

    def load_image_thread(self):
        img_thread = LoadImageThread(self.img_src)
        img_thread.finished.connect(self.load_image_finished)
        img_thread.start()

    def load_image_finished(self, data: ImageData):
        if data.width == 0 or data.src != self.img_src:
            return
        
        if isinstance(data.pixmap, QPixmap):
            self.image_label.set_image(data.pixmap)
            self.set_image_title()

    def my_close(self, event):
        Shared.loaded_images.clear()
        cnf.image_viewer = None
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
            keys = list(cnf.images.keys())
            current_index = keys.index(self.img_src)
        except Exception as e:
            keys = list(cnf.images.keys())
            current_index = 0

        total_images = len(cnf.images)
        new_index = (current_index + offset) % total_images
        self.img_src = keys[new_index]
        signals_app.select_new_wid.emit(self.img_src)
        self.load_thumbnail()

    def cut_text(self, text: str) -> str:
        limit = 40
        if len(text) > limit:
            return text[:limit] + "..."
        return text

    def set_image_title(self):
        try:
            w, h = get_image_size(self.img_src)
        except Exception:
            w, h = "?", "?"
        self.collection = MainUtils.get_coll_name(self.img_src)
        cut_coll = self.cut_text(MainUtils.get_coll_name(self.img_src))
        name = self.cut_text(os.path.basename(self.img_src))

        self.set_title(f"{w}x{h} - {cut_coll} - {name}")

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
            self.my_close(ev)

        elif ev.key() == Qt.Key.Key_Equal:
            self.image_label.zoom_in()

        elif ev.key() == Qt.Key.Key_Minus:
            self.image_label.zoom_out()

        elif ev.key() == Qt.Key.Key_0:
            self.image_label.zoom_reset()

        return super().keyPressEvent(ev)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        self.image_context = ContextImg(parent=self, img_src=self.img_src, event=event)
        self.image_context.show_menu()
        return super().contextMenuEvent(event)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        vertical_center = a0.size().height() // 2 - self.next_image_btn.height() // 2
        right_window_side = a0.size().width() - self.next_image_btn.width()
        self.prev_image_btn.move(10, vertical_center)
        self.next_image_btn.move(right_window_side - 10, vertical_center)

        horizontal_center = a0.size().width() // 2 - self.zoom_btns.width() // 2
        bottom_window_side = a0.size().height() - self.zoom_btns.height()
        self.zoom_btns.move(horizontal_center, bottom_window_side - 50)

        self.notification.resize(a0.size().width() - 20, 30)

        cnf.imgview_g.update({"aw": a0.size().width(), "ah": a0.size().height()})

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
