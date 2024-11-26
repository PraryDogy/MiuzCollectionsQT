import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel, QScrollArea,
                             QSizePolicy, QWidget)

from base_widgets import ContextCustom, LayoutVer, SvgBtn
from cfg import MENU_LEFT_WIDTH, THUMB_MARGIN, THUMB_W, JsonData, Dynamic, GRID_LIMIT
from signals import SignalsApp
from utils.utils import UThreadPool, Utils

from ..actions import OpenWins, ScanerRestart
from ..bar_bottom import BarBottom
from ._db_images import DbImage, DbImages
from .above_thumbs import FilterTitle, ErrorTitle
from .thumbnail import Thumbnail
from .title import Title

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
        self.resize(JsonData.root_g["aw"] - MENU_LEFT_WIDTH, JsonData.root_g["ah"])
        self.ww = JsonData.root_g["aw"] - MENU_LEFT_WIDTH
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.curr_cell: tuple = (0, 0)
        self.curr_short_src: str = None
        self.cell_to_wid: dict[tuple, Thumbnail] = {}
        # self.current_widgets: dict[QGridLayout, list[Thumbnail]] = {}

        scroll_wid = QWidget(parent=self)
        self.setWidget(scroll_wid)
        
        self.scroll_layout = LayoutVer()
        scroll_wid.setLayout(self.scroll_layout)

        self.up_btn = UpBtn(scroll_wid)
        self.up_btn.hide()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.signals_cmd(flag="reload")

        SignalsApp.all_.thumbnail_select.connect(self.select_new_widget)
        SignalsApp.all_.grid_thumbnails_cmd.connect(self.signals_cmd)
        SignalsApp.all_.win_img_view_open_in.connect(self.open_in_view)

    def signals_cmd(self, flag: str):
        if flag == "resize":
            self.resize_thumbnails()
        elif flag == "to_top":
            self.verticalScrollBar().setValue(0)
        elif flag == "reload":
            self.load_db_data(flag="first")
        else:
            raise Exception("widgets > grid > main > wrong flag", flag)

    def load_db_data(self, flag: str):
        """flag: first, more"""

        if flag == "first":
            Dynamic.grid_offset = 0
            cmd_ = lambda db_images: self.create_grid(db_images)

        elif flag == "more":
            Dynamic.grid_offset += GRID_LIMIT
            cmd_ = lambda db_images: self.grid_more(db_images)
        
        else: 
            raise Exception("wrong flag", flag)

        self.task_ = DbImages()
        self.task_.signals_.finished_.connect(cmd_)
        UThreadPool.pool.start(self.task_)

    def create_grid(self, db_images: dict[str, list[DbImage]]):

        if hasattr(self, "grid_widget"):
            self.grid_wid.deleteLater()

        self.curr_cell: tuple = (0, 0)
        self.curr_short_src = None
        self.cell_to_wid.clear()
        Thumbnail.path_to_wid.clear()
        self.up_btn.hide()

        self.grid_wid = QWidget()
        self.scroll_layout.addWidget(self.grid_wid)

        self.grid_lay = QGridLayout()
        self.grid_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.grid_wid.setLayout(self.grid_lay)

        self.row, self.col = 0, 0
        max_col = self.get_max_col()

        if not db_images:
            no_images = ErrorTitle()
            # no_images.setSizePolicy(
            #     QSizePolicy.Policy.Expanding,
            #     QSizePolicy.Policy.Preferred
            #     )
            self.grid_lay.addWidget(no_images, self.row, self.col, 1, max_col)
            self.row += 1
            return

        filter_title = FilterTitle()
        # above_thumbs.setSizePolicy(
        #     QSizePolicy.Policy.Expanding,
        #     QSizePolicy.Policy.Preferred
        #     )
        self.grid_lay.addWidget(filter_title, self.row, self.col,1,max_col)
        self.row += 1

        for date, db_images in db_images.items():
            self.single_grid(date, db_images)
            self.row += 1
            self.col = 0

        # scroll_wid.setFocus()

    def single_grid(self, date: str, db_images: list[DbImage]):
        max_col = self.get_max_col()

        self.col = 0
        self.row += 1
        title = Title(title=date, db_images=db_images)
        title.r_click.connect(self.reset_selection)
        title.row, title.col = self.row, self.col
        self.grid_lay.addWidget(title, self.row, self.col, 1, max_col)

        self.cell_to_wid[self.row, self.col] = title
        self.row += 1

        for db_image in db_images:

            wid = Thumbnail(
                pixmap=db_image.pixmap,
                short_src=db_image.short_src,
                coll=db_image.coll,
                fav=db_image.fav
            )
            wid.select.connect(lambda w=wid: self.select_new_widget(w))
            wid.row, wid.col = self.row, self.col
            self.cell_to_wid[self.row, self.col] = wid
            Thumbnail.path_to_wid[wid.short_src] = wid

            self.grid_lay.addWidget(wid, self.row, self.col)

            self.col += 1

            if self.col >= max_col:
                self.col = 0
                self.row += 1

    def grid_more(self, db_images: dict[str, list[DbImage]]):
        if db_images:
            for date, db_images in db_images.items():
                self.single_grid(date, db_images)

    def select_prev_widget(self):
        """
        после изменения сетки попытаться найти виджет из предыдущей сетки
        """
        wid = Thumbnail.path_to_wid.get(self.curr_short_src)
        if wid:
            self.select_new_widget(wid)

    def select_new_widget(self, data: tuple | str | Thumbnail):
        if isinstance(data, Thumbnail):
            coords = data.row, data.col
            new_wid = data

        elif isinstance(data, tuple):
            coords = data
            new_wid = self.cell_to_wid.get(data)

        elif isinstance(data, str):
            new_wid = Thumbnail.path_to_wid.get(data)
            coords = new_wid.row, new_wid.col

        if isinstance(new_wid, Title):
            if self.curr_cell > coords:
                offset = -1
            else:
                offset = 1
            
            data = (data[0] + offset, data[1])
            self.select_new_widget(data)

        elif isinstance(new_wid, Thumbnail):
            self.reset_selection()
            new_wid.selected_style()
            self.ensureWidgetVisible(new_wid)

            self.curr_cell = coords
            self.curr_short_src = new_wid.short_src

            if isinstance(BarBottom.path_label, QLabel):
                t = f"{new_wid.collection}: {new_wid.name}"
                BarBottom.path_label.setText(t)

    def reset_selection(self):
        widget = self.cell_to_wid.get(self.curr_cell)

        if isinstance(widget, Thumbnail | Title):
            widget.regular_style()

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
        return max(
            self.ww // (THUMB_W[JsonData.curr_size_ind] + (THUMB_MARGIN)),
            1
        )

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
        self.cell_to_wid.clear()
        Thumbnail.path_to_wid.clear()

        max_col = self.get_max_col()
        self.row, self.col = 0, 0

        for wid in self.grid_wid.findChildren((Thumbnail, Title)):

            if isinstance(wid, Title):
                self.col = 0
                self.row += 1
                wid.row, wid.col = self.row, self.col
                self.cell_to_wid[self.row, self.col] = wid
                self.grid_lay.addWidget(wid, self.row, self.col, 1, max_col)
                self.row += 1

            elif isinstance(wid, Thumbnail):
                wid.row, wid.col = self.row, self.col
                self.cell_to_wid[self.row, self.col] = wid
                Thumbnail.path_to_wid[wid.short_src] = wid
                self.grid_lay.addWidget(wid, self.row, self.col)
                self.col += 1

            if self.col >= max_col:
                self.col = 0
                self.row += 1        
        
        self.select_prev_widget()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier and a0.key() == Qt.Key.Key_I:
            wid = Thumbnail.path_to_wid.get(self.curr_short_src)
            coll_folder = Utils.get_coll_folder(JsonData.brand_ind)

            if coll_folder:
                OpenWins.info_db(
                    parent_=self.window(), 
                    short_src=wid.short_src,
                    coll_folder=coll_folder
                    )
            else:
                OpenWins.smb(self.window())

        elif a0.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
            wid = Thumbnail.path_to_wid.get(self.curr_short_src)
            if wid:
                self.open_in_view(wid)

        elif a0.key() == Qt.Key.Key_Left:
            coords = (self.curr_cell[0], self.curr_cell[1] - 1)
            self.select_new_widget(coords)

        elif a0.key() == Qt.Key.Key_Right:
            coords = (self.curr_cell[0], self.curr_cell[1] + 1)
            self.select_new_widget(coords)

        elif a0.key() == Qt.Key.Key_Up:
            coords = (self.curr_cell[0] - 1, self.curr_cell[1])
            self.select_new_widget(coords)

        elif a0.key() == Qt.Key.Key_Down:
            coords = (self.curr_cell[0] + 1, self.curr_cell[1])
            self.select_new_widget(coords)
        
        return super().keyPressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        self.reset_selection()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.resize_timer.stop()
        self.resize_timer.start(500)
        self.up_btn.hide()
        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.reset_selection()
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
            self.load_db_data(flag="more")