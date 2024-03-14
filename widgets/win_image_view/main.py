import os

import sqlalchemy
from PyQt5.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import (QFocusEvent, QIcon, QImage, QMouseEvent, QPainter,
                         QPixmap)
from PyQt5.QtWidgets import QWidget

from base_widgets import WinImgViewBase
from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app
from utils import MainUtils, ReadDesatImage, get_image_size

from ..image_context import ImageContext


class Manager:
    images = {}


class ImageWinUtils:
    @staticmethod
    def close_same_win():

        widgets: list[WinImgViewBase] = MainUtils.get_app().topLevelWidgets()

        for widget in widgets:
            if isinstance(widget, WinImgViewBase):

                cnf.imgview_g.update(
                    {"aw": widget.width(), "ah": widget.height()}
                    )

                widget.delete_win.emit()
                widget.deleteLater()


class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(dict)

    def __init__(self, image_path: str, w, h):
        super().__init__()
        self.image_path = image_path
        self.width, self.height = w, h

    def run(self):
        try:
            if self.image_path not in Manager.images:
                img = ReadDesatImage(self.image_path)
                img = img.get_rgb_image()

                q_image = QImage(img.data, img.shape[1], img.shape[0],
                                img.shape[1] * 3, QImage.Format_RGB888)
                Manager.images[self.image_path] = q_image
            else:
                q_image = Manager.images[self.image_path]

            pixmap = QPixmap.fromImage(q_image)

            if len(Manager.images) > 50:
                Manager.images.pop(next(iter(Manager.images)))

        except Exception as e:
            print("image viewer cant open image, open with pixmap")
            print(e)
            pixmap = QPixmap(self.image_path)
        
        self.image_loaded.emit({"image": pixmap, "src": self.image_path})


class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_pixmap: QPixmap = None
        self.scale_factor: float = 1.0
        self.offset = QPoint(0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        px = self.current_pixmap

        try:
            if px.width() < self.width() and px.height() < self.height():
                px = px.scaled(4000, 4000, aspectRatioMode=Qt.KeepAspectRatio)
        except AttributeError:
            pass

        icon = QIcon(px)

        ww = int(self.width() * self.scale_factor)
        hh = int(self.height() * self.scale_factor)

        x = int((self.width() - ww) / 2) + self.offset.x()
        y = int((self.height() - hh) / 2) + self.offset.y()

        icon.paint(painter, x, y, ww, hh, Qt.AlignmentFlag.AlignCenter)

    def set_image(self, pixmap):
        self.current_pixmap = pixmap
        self.offset = QPoint(0, 0)
        self.scale_factor = 1.0
        self.update()

    def zoom_in(self):
        self.scale_factor *= 1.1
        self.update()
        self.setCursor(Qt.OpenHandCursor) 

    def zoom_out(self):
        self.scale_factor /= 1.1
        self.update()
        self.setCursor(Qt.OpenHandCursor)

    def zoom_reset(self):
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)  # Сброс смещения
        self.update()
        self.setCursor(Qt.ArrowCursor) 

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.scale_factor > 1.0:
            delta = event.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.pos()
            self.update()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if self.scale_factor > 1.0:
            self.setCursor(Qt.OpenHandCursor)
        return super().mouseReleaseEvent(a0)


class ImageViewerBase(WinImgViewBase):
    def __init__(self):
        ImageWinUtils.close_same_win()
        super().__init__(close_func=self.my_close)
        self.disable_min_max()
        self.setMinimumSize(QSize(500, 400))

    def update_geometry(self):
        cnf.imgview_g.update({"aw": self.width(), "ah": self.height()})

    def my_close(self, event):
        # if event.spontaneous():
        # Manager.images.clear()
        self.update_geometry()
        self.delete_win.emit()
        self.deleteLater()
        event.ignore()


class WinImageView(ImageViewerBase):
    def __init__(self, image_path):
        super().__init__()

        self.image_path = image_path
        self.fullsize_thread = None

        self.thread_timer = QTimer(self)
        self.thread_timer.setSingleShot(True)
        self.thread_timer.setInterval(10)
        self.thread_timer.timeout.connect(self.run_thread)

        self.my_set_title()
        self.resize(cnf.imgview_g["aw"], cnf.imgview_g["ah"])
        self.bind_content_wid(self.mouse_click)
        gui_signals_app.set_focus_viewer.connect(self.setFocus)

        self.image_label = ImageWidget()
        self.content_layout.addWidget(self.image_label)
        self.bind_zoom(
            zoom_fit=lambda e: self.image_label.zoom_reset(),
            zoom_out=lambda e: self.image_label.zoom_out(),
            zoom_in=lambda e: self.image_label.zoom_in()
            )

        self.setFocus()
        self.center_win()
        self.load_image()


    def load_image(self):
        ww, hh = self.width(), self.height()

        if self.image_path not in Manager.images:
            self.my_set_title(loading=True)

            q = (sqlalchemy.select(ThumbsMd.img150)
                .filter(ThumbsMd.src == self.image_path))
            session = Dbase.get_session()

            try:
                res = session.execute(q).first()[0]

            except Exception as e:
                print(e)
                self.update_geometry()
                self.delete_win.emit()
                self.deleteLater()
                return

            finally:
                session.close()    

            pixmap = QPixmap()
            pixmap.loadFromData(res)

            pixmap = pixmap.scaled(ww, hh, Qt.KeepAspectRatio)
            self.image_label.set_image(pixmap)

        self.thread_timer.start()

    def run_thread(self):
        self.fullsize_thread = ImageLoaderThread(self.image_path, self.width(), self.height())
        self.fullsize_thread.image_loaded.connect(self.set_fullsize_image)
        self.fullsize_thread.start()

    def set_fullsize_image(self, data: dict):
        if data["image"].size().width() == 0 or data["src"] != self.image_path:
            return
        
        self.image_label.set_image(data["image"])
        self.my_set_title()

    def switch_image(self, offset):
        try:
            current_index = cnf.images.index(self.image_path)
        except ValueError:
            current_index = 0

        total_images = len(cnf.images)
        new_index = (current_index + offset) % total_images
        self.image_path = cnf.images[new_index]
        self.my_set_title()
        self.load_image()

    def my_set_title(self, loading=False):
        if loading:
            self.set_title(cnf.lng.loading)
            return

        try:
            w, h = get_image_size(self.image_path)
        except Exception:
            w, h = "?", "?"
        coll = MainUtils.get_coll_name(self.image_path)
        name = os.path.basename(self.image_path)

        self.set_title(f"{w}x{h} {coll[:50]} - {name[:50]}")

    def mouse_click(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.LeftButton and self.image_label.scale_factor == 1.0:
            move_left = event.x() < self.width() / 2
            offset = -1 if move_left else 1
            self.switch_image(offset)
            self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.switch_image(-1)

        elif event.key() == Qt.Key_Right:
            self.switch_image(1)

        elif event.key() == Qt.Key_Escape:
            self.my_close(event)

        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Equal:
            self.image_label.zoom_in()

        elif event.modifiers() & Qt.ControlModifier and  event.key() == Qt.Key_Minus:
            self.image_label.zoom_out()

        elif event.modifiers() & Qt.ControlModifier and  event.key() == Qt.Key_0:
            self.image_label.zoom_reset()

        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        ImageContext(parent=self, img_src=self.image_path, event=event)

    def focusInEvent(self, a0: QFocusEvent | None) -> None:
        self.setFocus()
        return super().focusInEvent(a0)
