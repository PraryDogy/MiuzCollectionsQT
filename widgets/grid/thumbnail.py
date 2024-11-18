import os

from PyQt5.QtCore import QMimeData, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QDrag, QMouseEvent, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QLabel

from base_widgets import LayoutVer
from base_widgets.context import ContextCustom
from cfg import (PIXMAP_SIZE, STAR_SYM, TEXT_LENGTH, THUMB_MARGIN, THUMB_W,
                 NAME_FAVS, JsonData)
from signals import SignalsApp
from styles import Names, Themes
from utils.utils import Utils

from ..actions import (CopyPath, FavAction, OpenInfo, OpenInView, ReloadGui,
                       Reveal, Save)


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
    path_to_wid: dict[str, "Thumbnail"] = {}

    def __init__(self, pixmap: QPixmap, src: str, coll: str, fav: int):
        super().__init__()
        self.setObjectName(Names.thumbnail_normal)
        self.setStyleSheet(Themes.current)

        self.img = pixmap

        self.src = src
        self.coll = coll
        self.fav = fav

        if fav == 0 or fav is None:
            self.name = os.path.basename(src)
        elif fav == 1:
            self.name = STAR_SYM + os.path.basename(src)
        
        self.row, self.col = 0, 0

        self.spacing = 5
        self.v_layout = LayoutVer()
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

        pixmap = Utils.pixmap_scale(self.img, PIXMAP_SIZE[JsonData.curr_size_ind])
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

    def change_fav(self, value: int):
        if value == 0:
            self.fav = value
            self.name = os.path.basename(self.src)
        elif value == 1:
            self.fav = value
            self.name = STAR_SYM + os.path.basename(self.src)

        self.name_label.name = self.name
        self.name_label.set_text()

        if value == 0 and JsonData.curr_coll == NAME_FAVS:
            SignalsApp.all_.grid_thumbnails_cmd.emit("reload")

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        self.select.emit(self.src)
        SignalsApp.all_.win_img_view_open_in.emit(self)
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
            menu_ = ContextCustom(event=ev)

            view = OpenInView(parent=self, src=self.src)
            menu_.addAction(view)

            info = OpenInfo(parent=self, src=self.src)
            menu_.addAction(info)

            self.fav_action = FavAction(parent=self, src=self.src, fav=self.fav)
            self.fav_action.finished_.connect(self.change_fav)
            menu_.addAction(self.fav_action)

            menu_.addSeparator()

            copy = CopyPath(parent=self, src=self.src)
            menu_.addAction(copy)

            reveal = Reveal(parent=self, src=self.src)
            menu_.addAction(reveal)

            save_as = Save(parent=self, src=self.src, save_as=True)
            menu_.addAction(save_as)

            save = Save(parent=self, src=self.src, save_as=False)
            menu_.addAction(save)

            menu_.addSeparator()

            reload = ReloadGui(parent=self, src=self.src)
            menu_.addAction(reload)

            self.select.emit(self.src)
            menu_.show_menu()

            # return super().contextMenuEvent(ev)

        except Exception as e:
            Utils.print_err(error=e)
