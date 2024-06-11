from PyQt5.QtCore import QMimeData, QObject, Qt, QUrl
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QApplication, QLabel

from cfg import cnf
from styles import Names, Themes
from utils import PixmapThumb

from ..image_context import ImageContext
from ..win_image_view import WinImageView


class Manager:
    win_image_view = None


class Thumbnail(QLabel, QObject):
    def __init__(self, byte_array: bytearray, img_src: str):
        super().__init__()
        self.img_src = img_src
        cnf.images.append(img_src)

        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        byte_array = PixmapThumb(byte_array)

        self.setPixmap(byte_array)
        self.image_context = None

    def mouseReleaseEvent(self, event):
        Manager.win_image_view = WinImageView(self.img_src)
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

    def contextMenuEvent(self, event):
        try:
            self.image_context = ImageContext(parent=self, img_src=self.img_src, event=event)
            self.image_context.closed.connect(self.closed_context)
            self.setObjectName(Names.thumbnail_selected)
            self.setStyleSheet(Themes.current)
            self.image_context.show_menu()
        except Exception as e:
            print(e)

    def closed_context(self):
        try:
            self.setObjectName(Names.thumbnail_normal)
            self.setStyleSheet(Themes.current)
        except Exception as e:
            print(e)
