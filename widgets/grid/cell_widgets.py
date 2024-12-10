import os

from PyQt5.QtCore import QMimeData, Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QDrag, QMouseEvent, QPixmap
from PyQt5.QtWidgets import QAction, QApplication, QFrame, QLabel, QSizePolicy

from base_widgets import ContextCustom, LayoutVer
from base_widgets.context import ContextCustom
from cfg import Dynamic, JsonData, Static, ThumbData
from lang import Lang
from signals import SignalsApp
from utils.copy_files import CopyFiles
from utils.utils import UThreadPool, Utils

from ..actions import (CopyPath, FavActionDb, MenuTypes, OpenInfoDb,
                       OpenInView, OpenWins, Reveal, Save, ScanerRestart)
from ._db_images import DbImage


class CellWid:
    def __init__(self):
        super().__init__()
        self.row = 0
        self.col = 0


class Title(QLabel, CellWid):
    r_click = pyqtSignal()

    def __init__(self, title: str, db_images: list[DbImage]):
        CellWid.__init__(self)
        QLabel.__init__(
            self,
            text=title
        )
        self.db_images = db_images

        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
            )

        self.setStyleSheet(Static.TITLE_NORMAL)

    def save_cmd(self, is_layers: bool, save_as: bool):

        coll_folder = Utils.get_coll_folder(brand_ind=JsonData.brand_ind)

        if coll_folder:

            if is_layers:
                images = [
                    Utils.get_full_src(coll_folder, i.short_src)
                    for i in self.db_images
                    if i.short_src.endswith(Static.LAYERS_EXT)
                    ]
            else:
                images = [
                    Utils.get_full_src(coll_folder, i.short_src)
                    for i in self.db_images
                    if not i.short_src.endswith(Static.LAYERS_EXT)
                    ]

            if save_as:
                dialog = OpenWins.dialog_dirs()
                dest = dialog.getExistingDirectory()

                if not dest:
                    return

            else:
                dest = Dynamic.down_folder
            
            self.copy_files_cmd(dest, images)

        else:
            OpenWins.smb(self.window())

    def copy_files_cmd(self, dest: str, files: list):
        coll_folder = Utils.get_coll_folder(brand_ind=JsonData.brand_ind)
        if coll_folder:
            self.copy_files_cmd_(dest, files)
        else:
            OpenWins.smb(self.window())

    def copy_files_cmd_(self, dest: str, files: list):
        files = [i for i in files if os.path.exists(i)]

        if len(files) == 0:
            return

        cmd_ = lambda files: self.copy_files_fin(files=files)
        copy_task = CopyFiles(dest=dest, files=files)
        copy_task.signals_.finished_.connect(cmd_)

        SignalsApp.all_.btn_downloads_toggle.emit("show")
        UThreadPool.pool.start(copy_task)

    def copy_files_fin(self, files: list):
        self.reveal_files = Utils.reveal_files(files)
        if len(CopyFiles.current_threads) == 0:
            SignalsApp.all_.btn_downloads_toggle.emit("hide")

    def selected_style(self):
        self.setStyleSheet(Static.TITLE_SOLID)

    def regular_style(self):
        self.setStyleSheet(Static.TITLE_NORMAL)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        self.r_click.emit()

        menu_ = ContextCustom(ev)

        cmd_ = lambda: self.save_cmd(is_layers=False, save_as=False)
        save_jpg = QAction(text=Lang.save_all_JPG, parent=menu_)
        save_jpg.triggered.connect(cmd_)
        menu_.addAction(save_jpg)

        cmd_ = lambda: self.save_cmd(is_layers=True, save_as=False)
        save_layers = QAction(text=Lang.save_all_layers, parent=menu_)
        save_layers.triggered.connect(cmd_)
        menu_.addAction(save_layers)

        menu_.addSeparator()

        cmd_ = lambda: self.save_cmd(is_layers=False, save_as=True)
        save_as_jpg = QAction(text=Lang.save_all_JPG_as, parent=menu_)
        save_as_jpg.triggered.connect(cmd_)
        menu_.addAction(save_as_jpg)

        cmd_ = lambda: self.save_cmd(is_layers=True, save_as=True)
        save_as_layers = QAction(text=Lang.save_all_layers_as, parent=menu_)
        save_as_layers.triggered.connect(cmd_)
        menu_.addAction(save_as_layers)

        menu_.addSeparator()

        reload = ScanerRestart(parent=menu_)
        menu_.addAction(reload)

        types_ = MenuTypes(parent=menu_)
        menu_.addMenu(types_)

        self.selected_style()
        menu_.show_menu()
        self.regular_style()


class NameLabel(QLabel):
    def __init__(self, parent, name: str, coll: str):
        super().__init__(parent)
        self.name = name
        self.coll = coll

    def set_text(self):
        ind = Dynamic.pixmap_size_ind
        max_row = ThumbData.MAX_ROW[ind]

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


class Thumbnail(QFrame, CellWid):
    select = pyqtSignal(str)
    path_to_wid: dict[str, "Thumbnail"] = {}

    pixmap_size = 0
    thumb_w = 0
    thumb_h = 0

    def __init__(self, pixmap: QPixmap, short_src: str, coll: str, fav: int):
        CellWid.__init__(self)
        QFrame.__init__(self)
        self.setStyleSheet(Static.NORMAL_STYLE)

        self.img = pixmap
        self.short_src = short_src
        self.collection = coll
        self.fav_value = fav

        if fav == 0 or fav is None:
            self.name = os.path.basename(short_src)
        elif fav == 1:
            self.name = Static.STAR_SYM + os.path.basename(short_src)

        self.v_layout = LayoutVer()
        self.v_layout.setSpacing(ThumbData.SPACING)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.v_layout)

        self.img_wid = QLabel()
        self.img_wid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(
            self.img_wid,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.text_wid = NameLabel(parent=self, name=self.name, coll=coll)
        self.text_wid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(
            self.text_wid,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.setup()

    @classmethod
    def calculate_size(cls):
        ind = Dynamic.pixmap_size_ind
        cls.pixmap_size = ThumbData.PIXMAP_SIZE[ind]
        cls.thumb_w = ThumbData.THUMB_W[ind]
        cls.thumb_h = ThumbData.THUMB_H[ind]

    def setup(self):
        # инициация текста
        self.text_wid.set_text()

        self.setFixedSize(
            self.thumb_w,
            self.thumb_h
        )

        # рамка вокруг pixmap при выделении Thumb
        self.img_wid.setFixedSize(
            self.pixmap_size + ThumbData.OFFSET,
            self.pixmap_size + ThumbData.OFFSET
        )

        self.img_wid.setPixmap(
            Utils.pixmap_scale(
                pixmap=self.img,
                size=self.pixmap_size
            )
        )

    def selected_style(self):
        self.setStyleSheet(Static.SOLID_STYLE)

    def regular_style(self):
        self.setStyleSheet(Static.NORMAL_STYLE)

    def change_fav(self, value: int):
        if value == 0:
            self.fav_value = value
            self.name = os.path.basename(self.short_src)
        elif value == 1:
            self.fav_value = value
            self.name = Static.STAR_SYM + os.path.basename(self.short_src)

        self.text_wid.name = self.name
        self.text_wid.set_text()

        # удаляем из избранного и если это избранные то обновляем сетку
        if value == 0 and Dynamic.curr_coll_name == Static.NAME_FAVS:
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
        
        coll_folder = Utils.get_coll_folder(JsonData.brand_ind)
        if coll_folder:
            full_src = Utils.get_full_src(coll_folder, self.short_src)
        else:
            return

        self.select.emit(self.short_src)
        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        self.drag.setPixmap(self.img_wid.pixmap())
        
        url = [QUrl.fromLocalFile(full_src)]
        self.mime_data.setUrls(url)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        return super().mouseMoveEvent(a0)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
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

        copy = CopyPath(
            parent=menu_,
            win=self.window(),
            short_src=self.short_src
        )
        menu_.addAction(copy)

        reveal = Reveal(
            parent=menu_,
            win=self.window(),
            short_src=self.short_src
        )
        menu_.addAction(reveal)

        save_as = Save(
            parent=menu_,
            win=self.window(),
            short_src=self.short_src,
            save_as=True
            )
        menu_.addAction(save_as)

        save = Save(
            parent=menu_,
            win=self.window(),
            short_src=self.short_src,
            save_as=False
            )
        menu_.addAction(save)

        menu_.addSeparator()

        reload = ScanerRestart(parent=menu_)
        menu_.addAction(reload)

        types_ = MenuTypes(parent=menu_)
        menu_.addMenu(types_)

        self.select.emit(self.short_src)
        menu_.show_menu()
