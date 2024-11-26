import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel, QScrollArea,
                             QSizePolicy, QSpacerItem, QWidget)

from base_widgets import ContextCustom, LayoutVer, SvgBtn
from cfg import Dynamic, JsonData, Static
from signals import SignalsApp
from utils.utils import UThreadPool, Utils

from ..actions import OpenWins, ScanerRestart
from ..bar_bottom import BarBottom
from ._db_images import DbImage, DbImages
from .above_thumbs import ErrorTitle, FilterTitle
from .cell_widgets import CellWid, Thumbnail, Title

IMAGES = "images"
UP_SVG = os.path.join(IMAGES, "up.svg")
UP_STYLE = f"""
    background: rgba(125, 125, 125, 0.5);
    border-radius: 22px;
"""


class UpBtn(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setStyleSheet(UP_STYLE)

        v_layout = LayoutVer()
        self.setLayout(v_layout)

        self.svg = SvgBtn(UP_SVG, 44)
        v_layout.addWidget(self.svg)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")
        return super().mouseReleaseEvent(a0)
    

class Grid(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.resize(JsonData.root_g["aw"] - Static.MENU_LEFT_WIDTH, JsonData.root_g["ah"])
        self.ww = JsonData.root_g["aw"] - Static.MENU_LEFT_WIDTH
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.curr_cell: tuple = (0, 0)
        self.cell_to_wid: dict[tuple, Thumbnail] = {}

        scroll_wid = QWidget(parent=self)
        self.setWidget(scroll_wid)
        
        self.scroll_layout = LayoutVer()
        scroll_wid.setLayout(self.scroll_layout)

        self.up_btn = UpBtn(scroll_wid)
        self.up_btn.hide()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.signals_cmd(flag="reload")

        SignalsApp.all_.thumbnail_select.connect(self.select_wid)
        SignalsApp.all_.grid_thumbnails_cmd.connect(self.signals_cmd)
        SignalsApp.all_.win_img_view_open_in.connect(self.open_in_view)

    def signals_cmd(self, flag: str):
        if flag == "resize":
            self.resize_thumbnails()
        elif flag == "to_top":
            self.verticalScrollBar().setValue(0)
        elif flag == "reload":
            self.load_db_images(flag="first")
        else:
            raise Exception("widgets > grid > main > wrong flag", flag)
        
        self.setFocus()

    def load_db_images(self, flag: str):
        """flag: first, more"""

        if flag == "first":
            Dynamic.grid_offset = 0
            cmd_ = lambda db_images: self.create_grid(db_images)

        elif flag == "more":
            Dynamic.grid_offset += Static.GRID_LIMIT
            cmd_ = lambda db_images: self.grid_more(db_images)
        
        else: 
            raise Exception("wrong flag", flag)

        self.task_ = DbImages()
        self.task_.signals_.finished_.connect(cmd_)
        UThreadPool.pool.start(self.task_)

    def create_grid(self, db_images: dict[str, list[DbImage]]):

        if hasattr(self, "grid_wid"):
            self.grid_wid.deleteLater()

        self.deselect_wid()
        self.reset_curr_cell()
        self.clear_grid_data()
        self.up_btn.hide()

        self.grid_wid = QWidget()
        self.scroll_layout.addWidget(self.grid_wid)

        self.grid_lay = QGridLayout()
        self.grid_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.grid_wid.setLayout(self.grid_lay)

        self.row, self.col = 0, 0
        max_col = self.get_max_col()

        if not db_images:

            spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
            self.grid_lay.addItem(spacer, 0, 0)

            no_images = ErrorTitle()
            no_images.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred
                )
            self.grid_lay.addWidget(no_images, self.row, self.col, 1, max_col)
            self.row += 1
            return

        filter_title = FilterTitle()
        filter_title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
            )
        self.grid_lay.addWidget(filter_title, self.row, self.col, 1, max_col)
        self.row += 1

        for date, db_images in db_images.items():
            self.single_grid(date, db_images)

    def single_grid(self, date: str, db_images: list[DbImage]):
        max_col = self.get_max_col()

        self.col = 0
        title = Title(title=date, db_images=db_images)
        title.r_click.connect(self.deselect_wid)

        self.set_coords(title)

        self.grid_lay.addWidget(title, self.row, self.col, 1, max_col)
        self.row += 1

        for db_image in db_images:

            wid = Thumbnail(
                pixmap=db_image.pixmap,
                short_src=db_image.short_src,
                coll=db_image.coll,
                fav=db_image.fav
            )
            wid.select.connect(lambda w=wid: self.select_wid(w))

            self.set_coords(wid)
            Thumbnail.path_to_wid[wid.short_src] = wid

            self.grid_lay.addWidget(wid, self.row, self.col)

            self.col += 1

            if self.col >= max_col:
                self.col = 0
                self.row += 1

        self.row += 1
        self.col = 0

    def grid_more(self, db_images: dict[str, list[DbImage]]):
        self.row -= 1
        if db_images:
            for date, db_images in db_images.items():
                self.single_grid(date, db_images)

    def get_curr_cell(self):
        return self.cell_to_wid.get(self.curr_cell)
    
    def get_cell(self, coords: tuple):
        return self.cell_to_wid.get(coords)

    def reset_curr_cell(self):
        self.curr_cell = (0, 0)

    def set_coords(self, wid: CellWid):
        coords = self.row, self.col
        self.cell_to_wid[coords] = wid
        wid.row, wid.col = coords

    def select_old_wid(self):
        wid = self.get_curr_cell()
        if wid:
            self.select_wid(wid)

    def clear_grid_data(self):
        self.cell_to_wid.clear()
        Thumbnail.path_to_wid.clear()

    def select_wid(self, data: tuple | str | Thumbnail):
        if isinstance(data, Thumbnail):
            coords = data.row, data.col
            new_wid = data

        elif isinstance(data, tuple):
            coords = data
            new_wid = self.get_cell(coords)

        elif isinstance(data, str):
            new_wid = Thumbnail.path_to_wid.get(data)
            coords = new_wid.row, new_wid.col

        # вычисляем это движение вверх или вниз
        if self.curr_cell > coords:
            offset = -1
        else:
            offset = 1

        # если виджет по движению не найден, пробуем назначить новую строку
        if not new_wid:
            coords = (coords[0] + offset, 0)
            new_wid = self.get_cell(coords)

        # если это заголовок, прибавляем/убавляем строку чтобы пропустить его
        if isinstance(new_wid, Title):
            coords = (data[0] + offset, data[1])
            new_wid = self.get_cell(coords)

        if isinstance(new_wid, Thumbnail):
            self.deselect_wid()
            new_wid.selected_style()
            self.ensureWidgetVisible(new_wid)

            self.curr_cell = coords

            if isinstance(BarBottom.path_label, QLabel):
                t = f"{new_wid.collection}: {new_wid.name}"
                BarBottom.path_label.setText(t)

    def deselect_wid(self):
        wid = self.get_curr_cell()

        if isinstance(wid, Thumbnail | Title):
            wid.regular_style()

        if isinstance(BarBottom.path_label, QLabel):
            BarBottom.path_label.setText("")

    def open_in_view(self, wid: Thumbnail):
        wid = Thumbnail.path_to_wid.get(wid.short_src)

        if isinstance(wid, Thumbnail):
            from ..win_image_view import WinImageView
            self.win_image_view = WinImageView(short_src=wid.short_src)
            self.win_image_view.center_relative_parent(self.window())
            self.win_image_view.show()

    def get_max_col(self):
        sm = sum(
            (
                Static.THUMB_W[JsonData.curr_size_ind],
                Static.THUMB_MARGIN
            )
        )

        return max(self.ww // sm, 1)

    def resize_thumbnails(self):
        "изменение размера Thumbnail"
        for thumb in self.grid_wid.findChildren(Thumbnail):
            thumb.setup()

        self.rearrange()

    def rearrange(self):
        "перетасовка сетки"

        if not hasattr(self, "first_load"):
            setattr(self, "first_load", True)
            return

        self.ww = self.width()
        self.clear_grid_data()

        max_col = self.get_max_col()
        self.row, self.col = 0, 0

        for wid in self.grid_wid.findChildren((Thumbnail, Title)):

            if isinstance(wid, Title):
                self.col = 0
                self.row += 1

                self.set_coords(wid)

                self.grid_lay.addWidget(wid, self.row, self.col, 1, max_col)
                self.row += 1

            elif isinstance(wid, Thumbnail):

                self.set_coords(wid)

                Thumbnail.path_to_wid[wid.short_src] = wid
                self.grid_lay.addWidget(wid, self.row, self.col)
                self.col += 1

            if self.col >= max_col:
                self.col = 0
                self.row += 1        
        
        self.select_old_wid()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if (
            a0.modifiers() == Qt.KeyboardModifier.ControlModifier
            and
            a0.key() == Qt.Key.Key_I
        ):

            wid = self.get_curr_cell()
            coll_folder = Utils.get_coll_folder(JsonData.brand_ind)

            if coll_folder:
                OpenWins.info_db(
                    parent_=self.window(), 
                    short_src=wid.short_src,
                    coll_folder=coll_folder
                    )
            else:
                OpenWins.smb(self.window())

        elif a0.key() in (
            Qt.Key.Key_Space, Qt.Key.Key_Return
        ):

            wid = self.get_curr_cell()
            if wid:
                self.open_in_view(wid)

        elif a0.key() in (
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down
        ):

            offsets = {
                Qt.Key.Key_Left: (0, -1),
                Qt.Key.Key_Right: (0, 1),
                Qt.Key.Key_Up: (-1, 0),
                Qt.Key.Key_Down: (1, 0)
            }

            offset = offsets.get(a0.key())
            coords = (
                self.curr_cell[0] + offset[0], 
                self.curr_cell[1] + offset[1]
            )

            self.select_wid(coords)
        
        return super().keyPressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        self.deselect_wid()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.resize_timer.stop()
        self.resize_timer.start(500)
        self.up_btn.hide()
        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.deselect_wid()
        self.menu_ = ContextCustom(event=a0)

        reload = ScanerRestart(self.menu_)
        self.menu_.addAction(reload)

        self.menu_.show_menu()

    def checkScrollValue(self, value):
        self.up_btn.move(
            self.width() - 60,
            self.height() - 60 + value
            )
        if value > 0:
            self.up_btn.show()
            self.up_btn.raise_()
        elif value == 0:
            self.up_btn.hide()

        if value == self.verticalScrollBar().maximum():
            self.load_db_images(flag="more")