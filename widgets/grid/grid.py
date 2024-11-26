import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel, QScrollArea,
                             QSizePolicy, QWidget)

from base_widgets import ContextCustom, LayoutVer, SvgBtn
from cfg import MENU_LEFT_WIDTH, THUMB_MARGIN, THUMB_W, JsonData
from signals import SignalsApp
from utils.utils import UThreadPool, Utils

from ..actions import OpenWins, ScanerRestart
from ..bar_bottom import BarBottom
from ._db_images import DbImage, DbImages
from .above_thumbs import AboveThumbs, AboveThumbsNoImages
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
        self.cell_to_wid: dict[tuple, Thumbnail] = {}
        Thumbnail.path_to_wid.clear()
        self.current_widgets: dict[QGridLayout, list[Thumbnail]] = {}

        # Создаем фрейм для виджетов в области скролла
        self.main_wid = QWidget(parent=self)
        self.setWidget(self.main_wid)
        
        self.main_layout = LayoutVer(self.main_wid)
        self.main_wid.setLayout(self.main_layout)

        self.up_btn = UpBtn(self.main_wid)
        self.up_btn.hide()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.columns = self.get_columns()
        self.setup_grids_widget()

        SignalsApp.all_.thumbnail_select.connect(self.select_new_widget)
        SignalsApp.all_.grid_thumbnails_cmd.connect(self.grid_thumbnails_cmd)
        SignalsApp.all_.win_img_view_open_in.connect(self.open_in_view)

    def grid_thumbnails_cmd(self, flag: str):
        if flag == "resize":
            self.resize_()
        elif flag == "to_top":
            self.verticalScrollBar().setValue(0)
        elif flag == "reload":
            self.setup_grids_widget()
        else:
            raise Exception("widgets > grid > main > wrong flag", flag)

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
            self.load_db_images("more")

    def load_db_images(self, flag: str):
        """flag: first, more"""

        if flag == "first":
            cmd_ = lambda db_images: self.setup_db_images(db_images)
        elif flag == "more":
            cmd_ = lambda db_images: self.setup_more_grids(db_images)

        self.task_ = DbImages()
        self.task_.signals_.finished_.connect(cmd_)
        UThreadPool.pool.start(self.task_)

    def setup_grids_widget(self):
        
        if hasattr(self, "grids_widget"):
            self.grids_widget.deleteLater()

        self.reset_widget_data()
        self.current_widgets.clear()
        self.up_btn.hide()

        from PyQt5.QtWidgets import QFrame
        self.grids_widget = QWidget()

        self.grids_layout = LayoutVer()
        self.grids_layout.setContentsMargins(5, 10, 5, 10)
        self.grids_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grids_widget.setLayout(self.grids_layout)

        self.load_db_images("first")

    def setup_db_images(self, db_images: dict[str, list[DbImage]]):

        if db_images:

            above_thumbs = AboveThumbs()
            above_thumbs.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred
                )
            self.grids_layout.addWidget(above_thumbs)

            for date, db_images in db_images.items():
                self.setup_single_grid(date, db_images)

        else:
            no_images = AboveThumbsNoImages()
            no_images.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred
                )
            self.grids_layout.addWidget(no_images)

        self.main_layout.addWidget(self.grids_widget)
        self.main_wid.setFocus()

    def setup_single_grid(self, date: str, db_images: list[DbImage]):
        title_label = Title(title=date, db_images=db_images)
        # title_label.r_click.connect(self.reset_selection)
        self.grids_layout.addWidget(title_label)

        grid_widget = QWidget()
        self.grids_layout.addWidget(grid_widget)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid_layout.setContentsMargins(0, 0, 0, 30)
        self.current_widgets[grid_layout] = []

        grid_widget.setLayout(grid_layout)

        row, col = 0, 0

        for db_image in db_images:
        
            wid = Thumbnail(
                pixmap=db_image.pixmap,
                short_src=db_image.short_src,
                coll=db_image.coll,
                fav=db_image.fav
                )

            wid.select.connect(lambda w=wid: self.select_new_widget(w))

            self.add_widget_data(wid, self.all_grids_row, col)
            self.current_widgets[grid_layout].append(wid)
            grid_layout.addWidget(wid, row, col)

            col += 1
            if col >= self.columns:
                col = 0
                row += 1
                self.all_grids_row += 1

        if len(db_images) % self.columns != 0:
            self.all_grids_row += 1

    def setup_more_grids(self, db_images: dict[str, list[DbImage]]):

        if db_images:
            for date, db_images in db_images.items():
                self.setup_single_grid(date, db_images)

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

        prev_wid = self.cell_to_wid.get(self.curr_cell)

        if isinstance(new_wid, Thumbnail):
            prev_wid.regular_style()
            new_wid.selected_style()
            self.curr_cell = coords
            self.ensureWidgetVisible(new_wid)

            if isinstance(BarBottom.path_label, QLabel):
                t = f"{new_wid.collection}: {new_wid.name}"
                BarBottom.path_label.setText(t)

        else:
            try:
                prev_wid.selected_style()
            except AttributeError:
                pass

    def reset_selection(self):
        widget = self.cell_to_wid.get(self.curr_cell)

        if isinstance(widget, Thumbnail):
            widget.regular_style()
            self.curr_cell: tuple = (0, 0)

            if isinstance(BarBottom.path_label, QLabel):
                BarBottom.path_label.setText("")

    def add_widget_data(self, wid: Thumbnail, row: int, col: int):
        wid.row, wid.col = row, col
        self.cell_to_wid[row, col] = wid
        Thumbnail.path_to_wid[wid.short_src] = wid

    def reset_widget_data(self):
        self.curr_cell: tuple = (0, 0)
        self.all_grids_row = 0
        self.cell_to_wid.clear()
        Thumbnail.path_to_wid.clear()

    def open_in_view(self, wid: Thumbnail):
        wid = Thumbnail.path_to_wid.get(wid.short_src)

        if isinstance(wid, Thumbnail):
            from ..win_image_view import WinImageView
            self.win_image_view = WinImageView(short_src=wid.short_src)
            self.win_image_view.center_relative_parent(self.window())
            self.win_image_view.show()

    def get_columns(self):
        return max(self.ww // (THUMB_W[JsonData.curr_size_ind] + (THUMB_MARGIN)), 1)

    def resize_(self):
        for grid_layout, widgets in self.current_widgets.items():
            for widget in widgets:
                widget.setup()
        self.rearrange()

    def rearrange(self):
        prev_short_src: str = self.cell_to_wid[self.curr_cell].short_src

        if not hasattr(self, "first_load"):
            setattr(self, "first_load", True)
            return

        self.ww = self.width()
        self.columns = self.get_columns()

        self.reset_widget_data()

        for grid_layout, widgets in self.current_widgets.items():

            row, col = 0, 0

            for wid in widgets:
                self.add_widget_data(wid, self.all_grids_row, col)
                grid_layout.addWidget(wid, row, col)

                col += 1
                if col >= self.columns:
                    col = 0
                    row += 1
                    self.all_grids_row += 1

            if len(widgets) % self.columns != 0:
                self.all_grids_row += 1

        if Thumbnail.path_to_wid.get(prev_short_src):
            self.select_new_widget(Thumbnail.path_to_wid.get(prev_short_src))

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        wid: Thumbnail

        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier and a0.key() == Qt.Key.Key_I:
            wid = self.cell_to_wid.get(self.curr_cell)

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
            wid = self.cell_to_wid.get(self.curr_cell)
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