import os

from PyQt5.QtCore import QMimeData, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QContextMenuEvent, QDrag, QMouseEvent, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QLabel

from base_widgets import LayoutV
from cfg import (PIXMAP_SIZE, TEXT_LENGTH, THUMB_MARGIN, THUMB_W, Dynamic,
                 JsonData)
from signals import SignalsApp
from styles import Names, Themes
from utils.main_utils import ImageUtils, MainUtils

from ..context_img import ContextImg


class NameLabel(QLabel):
    def __init__(self, parent, name: str, coll: str):
        super().__init__(parent)
        self.name = name
        self.coll = coll

    def set_text(self):
        max_row = TEXT_LENGTH[JsonData.curr_size_ind]

        if len(self.name) >= max_row:
            name = f"{self.name[:max_row - 10]}...{self.name[-7:]}"
        else:
            name = self.name

        if len(self.coll) > max_row:
            cut_coll = self.coll[:max_row]
            cut_coll = cut_coll[:-6]
            coll = cut_coll + "..." + self.coll[-3:]
        else:
            coll = self.coll

        self.setText(f"{coll}\n{name}")


class Thumbnail(QFrame):
    select = pyqtSignal(str)

    def __init__(self, img: bytes, src: str, coll: str):
        super().__init__()
        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        self.img = ImageUtils.pixmap_from_bytes(img)

        if not isinstance(self.img, QPixmap):
            self.img = QPixmap(PIXMAP_SIZE, PIXMAP_SIZE)
            self.img.fill(QColor(128, 128, 128))

        self.src = src
        self.coll = coll
        self.name = os.path.basename(src)

        self.setToolTip(
            f"{Dynamic.lng.collection}: {self.coll}\n"
            f"{Dynamic.lng.file_name}: {self.name}"
            )  
        
        self.row, self.col = 0, 0

        self.spacing = 5
        self.v_layout = LayoutV()
        self.v_layout.setSpacing(self.spacing)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.v_layout)

        self.img_label = QLabel()
        fl = Qt.AlignmentFlag.AlignCenter
        self.v_layout.addWidget(self.img_label, alignment=fl)

        self.name_label = NameLabel(parent=self, name=self.name, coll=coll)
        fl = Qt.AlignmentFlag.AlignCenter
        self.name_label.setAlignment(fl)
        self.v_layout.addWidget(self.name_label, alignment=fl)

        self.setup()

    def setup(self):
        name_label_h = 32
        thumb_h = PIXMAP_SIZE[JsonData.curr_size_ind] + name_label_h + THUMB_MARGIN + self.spacing
        thumb_w = THUMB_W[JsonData.curr_size_ind] + THUMB_MARGIN

        self.img_label.setFixedHeight(PIXMAP_SIZE[JsonData.curr_size_ind])
        self.name_label.setFixedHeight(name_label_h)

        self.setFixedSize(thumb_w, thumb_h)

        pixmap = ImageUtils.pixmap_scale(self.img, PIXMAP_SIZE[JsonData.curr_size_ind])
        self.img_label.setPixmap(pixmap)

        self.name_label.set_text()


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

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        self.select.emit(self.src)
        SignalsApp.all.win_img_view_open_in.emit(self)
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
            self.image_context = ContextImg(src=self.src, event=ev, parent=self)
            self.image_context.add_preview_item()

            self.select.emit(self.src)
            self.image_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
