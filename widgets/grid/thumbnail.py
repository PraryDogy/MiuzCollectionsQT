import os

from PyQt5.QtCore import QMimeData, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QDrag, QMouseEvent, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QLabel

from base_widgets import LayoutVer
from base_widgets.context import ContextCustom
from cfg import (NAME_FAVS, NORMAL_STYLE, PIXMAP_SIZE, SOLID_STYLE, STAR_SYM,
                 TEXT_LENGTH, THUMB_MARGIN, THUMB_W, JsonData)
from signals import SignalsApp
from utils.utils import Utils

from ..actions import (CopyPath, FavActionDb, OpenInfoDb, OpenInView, Reveal,
                       Save, ScanerRestart)


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

    def __init__(self, pixmap: QPixmap, short_src: str, coll: str, fav: int):
        super().__init__()
        self.setStyleSheet(NORMAL_STYLE)

        self.img = pixmap

        self.short_src = short_src
        self.coll = coll
        self.fav_value = fav

        if fav == 0 or fav is None:
            self.name = os.path.basename(short_src)
        elif fav == 1:
            self.name = STAR_SYM + os.path.basename(short_src)
        
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
        name_label_h = 35
        thumb_h = PIXMAP_SIZE[JsonData.curr_size_ind] + name_label_h + THUMB_MARGIN + self.spacing
        thumb_w = THUMB_W[JsonData.curr_size_ind] + THUMB_MARGIN

        self.img_label.setFixedHeight(PIXMAP_SIZE[JsonData.curr_size_ind])
        self.name_label.setFixedHeight(name_label_h)

        self.setFixedSize(thumb_w, thumb_h)

        pixmap = Utils.pixmap_scale(self.img, PIXMAP_SIZE[JsonData.curr_size_ind])
        self.img_label.setPixmap(pixmap)

        self.name_label.set_text()

    def selected_style(self):
        self.setStyleSheet(SOLID_STYLE)

    def regular_style(self):
        self.setStyleSheet(NORMAL_STYLE)

    def change_fav(self, value: int):
        if value == 0:
            self.fav_value = value
            self.name = os.path.basename(self.short_src)
        elif value == 1:
            self.fav_value = value
            self.name = STAR_SYM + os.path.basename(self.short_src)

        self.name_label.name = self.name
        self.name_label.set_text()

        if value == 0 and JsonData.curr_coll == NAME_FAVS:
            SignalsApp.all_.grid_thumbnails_cmd.emit("reload")

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        self.select.emit(self.short_src)
        SignalsApp.all_.win_img_view_open_in.emit(self)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        self.select.emit(self.short_src)

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

        self.select.emit(self.short_src)
        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        self.drag.setPixmap(self.img_label.pixmap())
        
        fullpath = Utils.get_full_src(self.short_src)
        url = [QUrl.fromLocalFile(fullpath)]
        self.mime_data.setUrls(url)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        return super().mouseMoveEvent(a0)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            menu_ = ContextCustom(event=ev)

            cmd_ = lambda: SignalsApp.all_.win_img_view_open_in.emit(self)
            view = OpenInView(parent_=menu_)
            view._clicked.connect(cmd_)
            menu_.addAction(view)

            info = OpenInfoDb(
                parent=menu_,
                win=self.window(),
                short_src=self.short_src
                )
            menu_.addAction(info)

            self.fav_action = FavActionDb(
                parent=menu_,
                short_src=self.short_src,
                fav_value=self.fav_value
                )
            self.fav_action.finished_.connect(self.change_fav)
            menu_.addAction(self.fav_action)

            menu_.addSeparator()

            full_src = Utils.get_full_src(self.short_src)

            copy = CopyPath(parent=menu_, win=self.window(), full_src=full_src)
            menu_.addAction(copy)

            reveal = Reveal(parent=menu_, win=self.window(), full_src=full_src)
            menu_.addAction(reveal)

            save_as = Save(
                parent=menu_,
                win=self.window(),
                full_src=full_src,
                save_as=True
                )
            menu_.addAction(save_as)

            save = Save(
                parent=menu_,
                win=self.window(),
                full_src=full_src,
                save_as=False
                )
            menu_.addAction(save)

            menu_.addSeparator()

            reload = ScanerRestart(parent=menu_)
            menu_.addAction(reload)

            self.select.emit(self.short_src)
            menu_.show_menu()

            # return super().contextMenuEvent(ev)

        except Exception as e:
            Utils.print_err(error=e)
