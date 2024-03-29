from PyQt5.QtCore import QMimeData, QObject, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QApplication, QLabel

from cfg import cnf
from signals import gui_signals_app
from utils import FindTiffLocal, PixmapThumb

from ..image_context import ImageContext
from ..win_image_view import WinImageView


class Thumbnail(QLabel, QObject):
    finish_find_tiff = pyqtSignal(str)

    def __init__(self, byte_array: bytearray, img_src: str):
        super().__init__()
        self.img_src = img_src
        self.tiff_src = None
        self.find_tiff_thread = None
        self.show_no_tiff = False
        cnf.images.append(img_src)

        self.setStyleSheet(
            f"""
            border: 2px solid transparent;
            """)

        byte_array = PixmapThumb(byte_array)
        if cnf.zoom:
            byte_array.resize_zoom()

        self.setPixmap(byte_array)
        self.image_context = None

    def mouseReleaseEvent(self, event):
        view_win = WinImageView(self.img_src)
        view_win.show()

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

        self.find_tiff()

    def find_tiff(self):
        self.find_tiff_local = FindTiffLocal(self.img_src)
        self.find_tiff_local.run_search()
        self.tiff_src = self.find_tiff_local.get_result()
        self.set_urls()
        self.finalize_move()

    def set_urls(self):
        self.urls = []

        if cnf.move_jpg:
            if self.img_src:
                self.urls.append(QUrl.fromLocalFile(self.img_src))

        if cnf.move_layers:
            if self.tiff_src:
                self.urls.append(QUrl.fromLocalFile(self.tiff_src))

            else:
                self.show_no_tiff = True

    def finalize_move(self):

        if len(self.urls) == 0:
            return

        self.mime_data.setUrls(self.urls)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.CopyAction)

        if self.show_no_tiff:
            self.show_no_tiff = False

            if cnf.scaner_running:
                t = f"{cnf.lng.no_tiff} {cnf.lng.wait_scan_finished}"
            else:
                t = cnf.lng.no_tiff

            gui_signals_app.noti_main.emit(t)


    def contextMenuEvent(self, event):
        self.image_context = ImageContext(parent=self, img_src=self.img_src, event=event)
