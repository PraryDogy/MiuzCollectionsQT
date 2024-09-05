import os

from PyQt5.QtCore import QEvent, QMimeData, Qt, QUrl
from PyQt5.QtGui import QContextMenuEvent, QDrag, QMouseEvent
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QSpacerItem

from base_widgets import LayoutV
from cfg import cnf
from styles import Names, Themes
from utils import MainUtils, PixmapFromBytes

from ..image_context import ImageContext
from ..win_image_view import WinImageView


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


class Thumbnail(QFrame):
    def __init__(self, byte_array: bytearray, img_src: str, coll: str, images_date: str):
        super().__init__()

        self.v_layout = LayoutV()
        self.v_layout.setContentsMargins(0, 2, 0, 0)
        self.setLayout(self.v_layout)

        self.img_src = img_src
        self.coll = coll
        self.images_date = images_date
        self.img_name = os.path.basename(img_src)

        cnf.images[img_src] = {
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

        self.title = NameLabel(parent=self, filename=self.img_name, coll=coll)
        self.title.setContentsMargins(8, 5, 8, 7)

        self.title.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.addWidget(self.title)

        self.setFixedWidth(cnf.THUMBSIZE + cnf.THUMBPAD)
        self.setMaximumHeight(cnf.THUMBSIZE + 75)

        self.setToolTip(
            f"{cnf.lng.collection}: {self.coll}\n"
            f"{cnf.lng.file_name}: {self.img_name}\n"
            f"{self.images_date}"
            )
        
    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        self.win_image_view = WinImageView(parent=self, img_src=self.img_src)
        self.win_image_view.show()
        return super().mouseReleaseEvent(a0)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:

            try:
                cnf.selected_thumbnail.regular_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            try:
                cnf.selected_thumbnail = self
                self.selected_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            self.drag_start_position = a0.pos()
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.RightButton:
            return

        distance = (a0.pos() - self.drag_start_position).manhattanLength()

        if distance < QApplication.startDragDistance():
            return

        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        self.drag.setPixmap(self.img_label.pixmap())
        
        url = [QUrl.fromLocalFile(self.img_src)]
        self.mime_data.setUrls(url)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        self.regular_style()

        return super().mouseMoveEvent(a0)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.image_context = ImageContext(img_src=self.img_src, event=ev, parent=self)
            self.image_context.closed.connect(self.closed_context)
            self.image_context.add_preview_item()
            if cnf.curr_coll == cnf.ALL_COLLS:
                self.image_context.add_show_coll_item(collection=self.coll)

            try:
                cnf.selected_thumbnail.regular_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            try:
                cnf.selected_thumbnail = self
                self.selected_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            self.image_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def closed_context(self):
        try:
            self.regular_style()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def selected_style(self):
        for i in (self, self.title):
            i.setObjectName(Names.thumbnail_selected)
            i.setStyleSheet(Themes.current)

    def regular_style(self):
        for i in (self, self.title):
            i.setObjectName(Names.thumbnail_normal)
            i.setStyleSheet(Themes.current)


class SmallThumbnail(QLabel):
    def __init__(self, byte_array: bytearray, img_src: str, coll: str, images_date: str):
        super().__init__()
        # 0 2 0 0
        self.setContentsMargins(8, 9, 8, 8)

        self.img_src = img_src
        self.coll = coll
        self.images_date = images_date
        self.img_name = os.path.basename(img_src)

        cnf.images[img_src] = {
            "widget": self,
            "collection": coll,
            "filename": self.img_name
            }

        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        byte_array = PixmapFromBytes(byte_array)
        self.setPixmap(byte_array)

        self.setFixedWidth(cnf.THUMBSIZE + cnf.THUMBPAD)
        self.setMaximumHeight(cnf.THUMBSIZE + 75)

        self.setToolTip(
            f"{cnf.lng.collection}: {self.coll}\n"
            f"{cnf.lng.file_name}: {self.img_name}\n"
            f"{self.images_date}"
            )
        
    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        self.win_image_view = WinImageView(parent=self, img_src=self.img_src)
        self.win_image_view.show()
        return super().mouseReleaseEvent(a0)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:

            try:
                cnf.selected_thumbnail.regular_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            try:
                cnf.selected_thumbnail = self
                self.selected_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            self.drag_start_position = a0.pos()
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.RightButton:
            return

        distance = (a0.pos() - self.drag_start_position).manhattanLength()

        if distance < QApplication.startDragDistance():
            return

        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        self.drag.setPixmap(self.pixmap())
        
        url = [QUrl.fromLocalFile(self.img_src)]
        self.mime_data.setUrls(url)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        self.regular_style()

        return super().mouseMoveEvent(a0)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.image_context = ImageContext(img_src=self.img_src, event=ev, parent=self)
            self.image_context.closed.connect(self.closed_context)
            self.image_context.add_preview_item()
            if cnf.curr_coll == cnf.ALL_COLLS:
                self.image_context.add_show_coll_item(collection=self.coll)

            try:
                cnf.selected_thumbnail.regular_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            try:
                cnf.selected_thumbnail = self
                self.selected_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            self.image_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def closed_context(self):
        try:
            self.regular_style()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def selected_style(self):
        self.setObjectName(Names.thumbnail_selected)
        self.setStyleSheet(Themes.current)

    def regular_style(self):
        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)