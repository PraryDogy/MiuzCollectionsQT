from PyQt5.QtCore import QEvent, QMimeData, QObject, Qt, QUrl
from PyQt5.QtGui import QContextMenuEvent, QDrag
from PyQt5.QtWidgets import QApplication, QLabel

from cfg import cnf
from styles import Names, Themes
from utils import PixmapThumb

from ..image_context import ImageContext
from ..win_image_view import WinImageView
import os

class Manager:
    win_image_view = None
    co = None


class Thumbnail(QLabel, QObject):
    def __init__(self, byte_array: bytearray, img_src: str, coll: str, images_date: str):
        super().__init__()

        self.img_src = img_src
        self.coll = coll
        self.images_date = images_date
        self.img_name = os.path.basename(img_src)

        cnf.images.append(img_src)

        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        byte_array = PixmapThumb(byte_array)

        self.setPixmap(byte_array)
        self.image_context = None

    def mouseReleaseEvent(self, event):
        Manager.win_image_view = WinImageView(parent=self, img_src=self.img_src)
        Manager.win_image_view.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton:
            return

        distance = (event.pos() - self.drag_start_position).manhattanLength()

        if distance < QApplication.startDragDistance():
            return

        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        self.drag.setPixmap(self.pixmap())
        
        url = [QUrl.fromLocalFile(self.img_src)]
        self.mime_data.setUrls(url)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.CopyAction)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.image_context = ImageContext(img_src=self.img_src, event=ev, parent=self)
            self.image_context.closed.connect(self.closed_context)
            self.image_context.add_preview_item()
            self.setObjectName(Names.thumbnail_selected)
            self.setStyleSheet(Themes.current)
            self.image_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            print(e)

    def closed_context(self):
        try:
            self.setObjectName(Names.thumbnail_normal)
            self.setStyleSheet(Themes.current)
        except Exception as e:
            print(e)

    def enterEvent(self, a0: QEvent | None) -> None:
        self.setToolTip(
            f"{self.images_date}\n"
            f"{cnf.lng.collection}: {self.coll}"
            f"\n{cnf.lng.file_name}: {self.img_name}"
            )
        return super().enterEvent(a0)
    
    def leaveEvent(self, a0: QEvent | None) -> None:
        self.setToolTip("")
        return super().leaveEvent(a0)
