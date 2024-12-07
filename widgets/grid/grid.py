import os
from collections import defaultdict
from typing import Literal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel, QScrollArea,
                             QSizePolicy, QSpacerItem, QWidget)

from base_widgets import ContextCustom, LayoutVer, SvgBtn
from cfg import Dynamic, JsonData, Static
from signals import SignalsApp
from utils.utils import UThreadPool, Utils

from ..actions import MenuTypes, OpenWins, ScanerRestart
from ..bar_bottom import BarBottom
from ._db_images import DbImage, DbImages
from .above_thumbs import ErrorTitle, FilterTitle
from .cell_widgets import CellWid, Thumbnail, Title

UP_SVG = os.path.join(Static.IMAGES, "up.svg")
UP_STYLE = f"""
    background: rgba(125, 125, 125, 0.5);
    border-radius: 22px;
"""


class UpBtn(QFrame):
    def __init__(self, parent: QWidget):
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
        self.resize(
            Dynamic.root_g["aw"] - Static.MENU_LEFT_WIDTH,
            Dynamic.root_g["ah"]
        )
        self.ww = Dynamic.root_g["aw"] - Static.MENU_LEFT_WIDTH
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        # self.curr_cell: tuple = (0, 0)
        # self.cell_to_wid: dict[tuple, Thumbnail] = {}

        # для rearrange чтобы перетасовывать сетку
        self.grids: dict[QGridLayout, list[Thumbnail]] = defaultdict(list)

        # для навигации по сетке клавишами, мышью и из ImgViewer
        self.thumbs: list[Thumbnail] = []
        self.current_thumb: Thumbnail = None

        self.signals_cmd(flag="reload")

        SignalsApp.all_.thumbnail_select.connect(self.select_wid)
        SignalsApp.all_.grid_thumbnails_cmd.connect(self.signals_cmd)
        SignalsApp.all_.win_img_view_open_in.connect(self.open_in_view)

        # parent неверный
        self.up_btn = UpBtn(self)
        self.up_btn.hide()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

    def signals_cmd(self, flag: Literal["resize", "to_top", "reload"]):
        if flag == "resize":
            self.resize_thumbnails()
        elif flag == "to_top":
            self.verticalScrollBar().setValue(0)
        elif flag == "reload":
            self.load_db_images(flag="first")
        else:
            raise Exception("widgets > grid > main > wrong flag", flag)
        
        self.setFocus()

    def load_db_images(self, flag: Literal["first", "more"]):

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

        if hasattr(self, "main_wid"):
            self.main_wid.deleteLater()

        self.main_wid = QWidget()
        self.setWidget(self.main_wid)
        
        self.main_lay = LayoutVer()
        self.main_wid.setLayout(self.main_lay)

        self.reset_grids_data()


        # self.deselect_wid()
        # self.reset_grid_data()
        # self.up_btn.hide()

        # self.grid_wid = QWidget()
        # self.main_lay.addWidget(self.grid_wid)

        # self.grid_lay = QGridLayout()
        # self.grid_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        # self.grid_wid.setLayout(self.grid_lay)

        # max_col = self.get_max_col()

        # if not db_images:

        #     spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        #     self.grid_lay.addItem(spacer, self.row, self.col)

        #     self.col += 1
        #     error_title = ErrorTitle()
        #     self.grid_lay.addWidget(error_title, self.row, self.col)
        #     # добавляем новую строку так как это заголовок

        #     self.col += 1
        #     spacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
        #     self.grid_lay.addItem(spacer, self.row, self.col)

        #     self.col = 0
        #     self.row += 1
        #     return

        # filter_title = FilterTitle()
        # filter_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # self.grid_lay.addWidget(filter_title, self.row, self.col, 1, max_col)
        # self.row += 1

        Thumbnail.calculate_size()

        for date, db_images in db_images.items():
            self.single_grid(date, db_images)

        self.current_thumb = self.thumbs[0]

    def single_grid(self, date: str, db_images: list[DbImage]):

        title = Title(title=date, db_images=db_images)
        title.r_click.connect(self.deselect_current_thumb)
        self.main_lay.addWidget(title)

        grid_wid = QWidget()
        self.main_lay.addWidget(grid_wid)

        flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        grid_lay = QGridLayout()
        grid_lay.setAlignment(flags)
        grid_wid.setLayout(grid_lay)

        row, col = 0, 0

        for x, db_image in enumerate(db_images):

            wid = Thumbnail(
                pixmap=db_image.pixmap,
                short_src=db_image.short_src,
                coll=db_image.coll,
                fav=db_image.fav
            )

            wid.select.connect(lambda w=wid: self.select_wid(w))

            self.add_to_path_to_wid(wid)
            self.add_to_grids(grid=grid_lay, wid=wid)

            grid_lay.addWidget(wid, row, col)

            col += 1
            if col >= self.max_col:
                col = 0
                row += 1

    def add_to_grids(self, grid: QGridLayout, wid: Thumbnail):
        self.grids[grid].append(wid)
        self.thumbs.append(wid)

    def grid_more(self, db_images: dict[str, list[DbImage]]):
        for date, db_images in db_images.items():
            self.single_grid(date, db_images)

    def add_to_path_to_wid(self, wid: Thumbnail):
        Thumbnail.path_to_wid[wid.short_src] = wid

    def get_from_path_to_wid(self, src: str):
        return Thumbnail.path_to_wid.get(src)

    def select_wid(self, obj: str | int | Thumbnail):

        new_wid = None

        if isinstance(obj, str):
            new_wid = self.get_from_path_to_wid(src=obj)

        elif isinstance(obj, int):

            if len(self.thumbs) > obj > -1:
                new_wid = self.thumbs[obj]

        if new_wid:
            self.deselect_current_thumb()
            self.set_current_thumb(new_wid)
            self.select_current_thumb()
            self.ensureWidgetVisible(new_wid)

            if isinstance(BarBottom.path_label, QLabel):
                t = f"{new_wid.collection}: {new_wid.name}"
                BarBottom.path_label.setText(t)

            # return new_wid

        # return None

    def get_current_thumb(self):
        return self.current_thumb

    def set_current_thumb(self, thumb: Thumbnail):
        self.current_thumb = thumb

    def select_current_thumb(self):
        self.current_thumb.selected_style()

    def deselect_current_thumb(self):
        self.current_thumb.regular_style()
        assert isinstance(BarBottom.path_label, QLabel)
        BarBottom.path_label.setText("")

    def open_in_view(self, wid: Thumbnail):
        assert isinstance(wid, Thumbnail)
        from ..win_image_view import WinImageView
        self.win_image_view = WinImageView(short_src=wid.short_src)
        self.win_image_view.center_relative_parent(self.window())
        self.win_image_view.show()

    def get_max_col(self):
        sm = sum(
            (
                Static.THUMB_W[JsonData.curr_size_ind],
                Static.THUMB_MARGIN,
                10
            )
        )

        return max(self.ww // sm, 1)

    def resize_thumbnails(self):
        "изменение размера Thumbnail"

        Thumbnail.calculate_size()

        for grid, wid_list in self.grids.items():

            for wid in wid_list:
                wid.setup()

        self.rearrange()

    # def reselect_wid(func: callable):

    #     def wrapper(self, *args, **kwargs):

    #         assert isinstance(self, Grid)

    #         wid = self.get_curr_cell()
    #         src = wid.short_src if isinstance(wid, Thumbnail) else None

    #         func(self, *args, **kwargs)

    #         if src:
    #             wid = self.select_wid(src)  

    #             if wid:
    #                 coords = (wid.row, wid.col)
    #                 self.set_curr_sell(coords)

    #     return wrapper

    def reset_grids_data(self):
        self.max_col = self.get_max_col()
        self.current_path = None
        Thumbnail.path_to_wid.clear()

    # @reselect_wid
    def rearrange(self):

        # запрещаем в первую загрузку делать rearrange
        if not hasattr(self, "first_load"):
            setattr(self, "first_load", True)
            return

        print("rearrange")

        self.ww = self.width()
        self.reset_grids_data()

        for grid_lay, thumb_list in self.grids.items():

            row, col = 0, 0

            for wid in thumb_list:
                grid_lay.addWidget(wid, row, col)

                self.add_to_path_to_wid(wid)

                grid_lay.addWidget(wid, row, col)

                col += 1
                if col >= self.max_col:
                    col = 0
                    row += 1

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

            current_thumb = self.get_current_thumb()
            current_ind = self.thumbs.index(current_thumb)

            indexes = {
                Qt.Key.Key_Left: current_ind - 1,
                Qt.Key.Key_Right: current_ind + 1,
                Qt.Key.Key_Up: current_ind - self.max_col,
                Qt.Key.Key_Down: current_ind + self.max_col
            }

            new_ind = indexes.get(a0.key())
            self.select_wid(obj=new_ind)
        
        return super().keyPressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        self.deselect_current_thumb()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.resize_timer.stop()
        self.resize_timer.start(500)
        self.up_btn.hide()
        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.deselect_current_thumb()
        self.menu_ = ContextCustom(event=a0)

        reload = ScanerRestart(self.menu_)
        self.menu_.addAction(reload)

        types_ = MenuTypes(parent=self.menu_)
        self.menu_.addMenu(types_)

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