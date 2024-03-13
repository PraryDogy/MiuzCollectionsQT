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
from utils import MainUtils, ReadDesatImage

from ..image_context import ImageContext


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


IMAGES = {}


class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(dict)

    def __init__(self, image_path: str, w, h):
        super().__init__()
        self.image_path = image_path
        self.width, self.height = w, h

    def run(self):
        try:
            if self.image_path not in IMAGES:
                img = ReadDesatImage(self.image_path)
                img = img.get_rgb_image()

                q_image = QImage(img.data, img.shape[1], img.shape[0],
                                img.shape[1] * 3, QImage.Format_RGB888)
                IMAGES[self.image_path] = q_image
            else:
                q_image = IMAGES[self.image_path]

            pixmap = QPixmap.fromImage(q_image)

            if len(IMAGES) > 50:
                IMAGES.pop(next(iter(IMAGES)))

        except Exception as e:
            print("image viewer cant open image with PIL")
            print(e)
            pixmap = QPixmap(self.image_path)
        
        self.image_loaded.emit({"image": pixmap, "src": self.image_path})


class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_pixmap = None
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        icon = QIcon(self.current_pixmap)

        ww = int(self.width() * self.scale_factor)
        hh = int(self.height() * self.scale_factor)
        x = int((self.width() - ww) / 2) + self.offset.x()  # Учтено смещение
        y = int((self.height() - hh) / 2) + self.offset.y()  # Учтено смещение

        icon.paint(painter, x, y, ww, hh, Qt.AlignmentFlag.AlignCenter)

    def set_image(self, pixmap):
        self.current_pixmap = pixmap
        self.offset = QPoint(0, 0)  # Сброс смещения
        self.update()
        self.scale_factor = 1.0

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
        if event.spontaneous():
            self.update_geometry()
            self.delete_win.emit()
            self.deleteLater()
            event.ignore()


class WinImageView(ImageViewerBase):
    def __init__(self, image_path):
        super().__init__()

        self.image_path = image_path
        self.fullsize_thread = None

        self.my_set_title()
        self.resize(cnf.imgview_g["aw"], cnf.imgview_g["ah"])
        self.bind_content_wid(self.mouse_click)
        gui_signals_app.set_focus_viewer.connect(self.setFocus)

        self.image_label = ImageWidget()
        self.content_layout.addWidget(self.image_label)

        self.fullimg_timer = QTimer(self)
        self.fullimg_timer.setInterval(50)
        self.fullimg_timer.setSingleShot(True)
        self.fullimg_timer.timeout.connect(self.load_fullsize_image)

        self.setFocus()
        self.center_win()
        self.load_image()

    def load_image(self):
        self.my_set_title(loading=True)
        self.fullimg_timer.stop()

        if self.image_path not in IMAGES:

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

            ww, hh = self.width(), self.height()
            pixmap = pixmap.scaled(ww, hh, Qt.KeepAspectRatio)
            self.image_label.set_image(pixmap)

        self.fullimg_timer.start()

    def load_fullsize_image(self):
        ww, hh = self.width(), self.height()
        self.fullsize_thread = ImageLoaderThread(self.image_path, ww, hh)
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

        coll = MainUtils.get_coll_name(self.image_path)
        name = os.path.basename(self.image_path)

        self.set_title(f"{coll[:50]} - {name[:50]}")

    def mouse_click(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.LeftButton and self.image_label.scale_factor == 1.0:
            move_left = event.x() < self.width() / 2
            offset = -1 if move_left else 1
            self.switch_image(offset)
            self.my_set_title()
            self.load_image()
            self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.switch_image(-1)

        elif event.key() == Qt.Key_Right:
            self.switch_image(1)

        elif event.key() == Qt.Key_Escape:
            self.update_geometry()
            self.delete_win.emit()
            self.deleteLater()

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
