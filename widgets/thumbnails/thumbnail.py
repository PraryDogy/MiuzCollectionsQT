import os

from PyQt5.QtCore import QEvent, QMimeData, Qt, QUrl
from PyQt5.QtGui import QContextMenuEvent, QDrag
from PyQt5.QtWidgets import QAction, QApplication, QFrame, QLabel, QSpacerItem

from base_widgets import ContextMenuBase, LayoutV
from cfg import cnf
from styles import Names, Themes
from utils import MainUtils, PixmapThumb

from ..image_context import ImageContext
from ..win_image_view import WinImageView


class Manager:
    win_image_view = None
    co = None


class SelectableLabel(QLabel):
    def __init__(self, parent, text: str):
        super().__init__(parent)

        self.setText(text)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = ContextMenuBase(ev)

        copy_text = QAction(parent=context_menu, text=cnf.lng.copy)
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=cnf.lng.copy_all)
        select_all.triggered.connect(lambda: MainUtils.copy_text(self.text().replace("\n", "")))
        context_menu.addAction(select_all)

        context_menu.show_menu()

    def copy_text_md(self):
        MainUtils.copy_text(self.selectedText().replace("\n", ""))


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

        cnf.images.append(img_src)

        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        self.v_layout.addSpacerItem(QSpacerItem(0, 7))

        self.img_label = QLabel()
        byte_array = PixmapThumb(byte_array)
        self.img_label.setPixmap(byte_array)
        self.v_layout.addWidget(self.img_label, alignment=Qt.AlignmentFlag.AlignCenter)

        max_chars = 30
        name = '\n'.join(
                [self.img_name[i:i + max_chars]
                 for i in range(0, len(self.img_name), max_chars)]
                 )
        self.title = SelectableLabel(parent=self, text=name)
        self.title.setContentsMargins(8, 2, 8, 7)

        self.title.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.addWidget(self.title)

        self.setFixedWidth(cnf.THUMBSIZE + cnf.THUMBPAD)
        self.setMaximumHeight(cnf.THUMBSIZE + 50)
        

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
        self.drag.setPixmap(self.img_label.pixmap())
        
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
