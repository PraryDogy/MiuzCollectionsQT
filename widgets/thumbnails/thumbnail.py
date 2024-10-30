import os

from PyQt5.QtCore import QMimeData, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QDrag, QMouseEvent
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QSpacerItem

from base_widgets import LayoutV
from cfg import cnf
from styles import Names, Themes
from utils import MainUtils, PixmapFromBytes

from ..image_context import ImageContext


class NameLabel(QLabel):
    def __init__(self, parent, filename: str, coll: str):
        super().__init__(parent)

        self.filename = filename
        self.coll = coll
        max_row = 27

        coll = f"{cnf.lng.collection}: {coll}"
        name, ext = os.path.splitext(filename)
        name = f"{cnf.lng.file_name}: {name}"
        ext = f"{cnf.lng.type}: {ext.replace('.', '')}"

        if len(coll) > max_row:
            cut_coll = coll[:max_row]
            cut_coll = cut_coll[:-6]
            coll = cut_coll + "..." + coll[-3:]

        if len(name) >= max_row:
            cut_name = name[:max_row]
            cut_name = cut_name[:-6]
            name = cut_name + "..." + name[-3:]

        self.setText(f"{coll}\n{name}\n{ext}")


class BaseThumb(QFrame):
    select = pyqtSignal(str)
    open_in_view = pyqtSignal(str)

    def __init__(self, byte_array: bytearray, src: str, coll: str, images_date: str):
        super().__init__()

        self.row, self.col = 0, 0
        self.src = src
        self.coll = coll
        self.images_date = images_date
        self.img_name = os.path.basename(src)

        self.v_layout = LayoutV()
        self.v_layout.setContentsMargins(0, 2, 0, 0)
        self.setLayout(self.v_layout)

        cnf.images[src] = {
            "widget": self,
            "collection": coll,
            "filename": self.img_name
            }

        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        self.v_layout.addSpacerItem(QSpacerItem(0, 7))

        self.img_label = QLabel()
        byte_array = PixmapFromBytes(byte_array)
        self.img_label.setPixmap(byte_array)
        self.v_layout.addWidget(self.img_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setToolTip(
            f"{cnf.lng.collection}: {self.coll}\n"
            f"{cnf.lng.file_name}: {self.img_name}\n"
            f"{self.images_date}"
            )  

        self.setFixedWidth(cnf.THUMBSIZE + cnf.THUMBPAD)
        self.setMaximumHeight(cnf.THUMBSIZE + 75)

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        self.select.emit(self.src)
        self.open_in_view.emit(self.src)
        return super().mouseDoubleClickEvent(a0)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        self.select.emit(self.src)

        # return super().mouseReleaseEvent(ev)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = a0.pos()
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.RightButton:
            return

        distance = (a0.pos() - self.drag_start_position).manhattanLength()

        if distance < QApplication.startDragDistance():
            return

        self.select.emit(self.src)
        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        self.drag.setPixmap(self.img_label.pixmap())
        
        url = [QUrl.fromLocalFile(self.src)]
        self.mime_data.setUrls(url)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        return super().mouseMoveEvent(a0)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.image_context = ImageContext(img_src=self.src, event=ev, parent=self)
            self.image_context.add_preview_item()
            if cnf.curr_coll == cnf.ALL_COLLS:
                self.image_context.add_show_coll_item(collection=self.coll)

            self.select.emit(self.src)
            self.image_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)


class Thumbnail(BaseThumb):
    select = pyqtSignal(str)
    open_in_view = pyqtSignal(str)

    def __init__(self, byte_array: bytearray, src: str, coll: str, images_date: str):
        super().__init__(byte_array, src, coll, images_date)
   
        self.title = NameLabel(parent=self, filename=self.img_name, coll=coll)
        self.title.setContentsMargins(8, 5, 8, 7)

        self.title.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.addWidget(self.title)
    
    def selected_style(self):
        try:
            for i in (self, self.title):
                i.setObjectName(Names.thumbnail_selected)
                i.setStyleSheet(Themes.current)
        except RuntimeError:
            ...

    def regular_style(self):
        try:
            for i in (self, self.title):
                i.setObjectName(Names.thumbnail_normal)
                i.setStyleSheet(Themes.current)
        except RuntimeError:
            ...


class SmallThumbnail(BaseThumb):
    select = pyqtSignal(str)
    open_in_view = pyqtSignal(str)

    def __init__(self, byte_array: bytearray, src: str, coll: str, images_date: str):
        super().__init__(byte_array, src, coll, images_date)
        self.setContentsMargins(0, 0, 0, 8)
        self.v_layout.setContentsMargins(0, 0, 0, 0)

    def selected_style(self):
        try:
            self.setObjectName(Names.thumbnail_selected)
            self.setStyleSheet(Themes.current)
        except RuntimeError:
            ...

    def regular_style(self):
        try:
            self.setObjectName(Names.thumbnail_normal)
            self.setStyleSheet(Themes.current)
        except RuntimeError:
            ...