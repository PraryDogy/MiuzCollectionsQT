from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import QGridLayout, QScrollArea, QWidget

from base_widgets import ContextCustom, LayoutHor, LayoutVer
from cfg import MENU_W, THUMB_MARGIN, THUMB_W, Dynamic, JsonData, LIMIT
from signals import SignalsApp
from styles import Names, Themes
from utils.utils import Utils

from ..actions import ReloadGui, OpenWins
from ..win_smb import WinSmb
from .above_thumbs import AboveThumbs, AboveThumbsNoImages
from ._load_thumbs import DbImage, DbImages
from .limit_btn import LimitBtn
from .thumbnail import Thumbnail
from .title import Title
from .up_btn import UpBtn


class Grid(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.resize(JsonData.root_g["aw"] - MENU_W, JsonData.root_g["ah"])
        self.ww = JsonData.root_g["aw"] - MENU_W
        self.horizontalScrollBar().setDisabled(True)
        self.setObjectName(Names.th_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.topleft = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.curr_cell: tuple = (0, 0)
        self.cell_to_wid: dict[tuple, Thumbnail] = {}
        Thumbnail.path_to_wid.clear()
        self.current_widgets: dict[QGridLayout, list[Thumbnail]] = {}

        # Создаем фрейм для виджетов в области скролла
        self.main_wid = QWidget(parent=self)
        self.main_wid.setObjectName(Names.th_scroll_widget)
        self.main_wid.setStyleSheet(Themes.current)
        self.setWidget(self.main_wid)
        
        self.main_layout = LayoutVer(self.main_wid)
        self.main_wid.setLayout(self.main_layout)

        self.up_btn = UpBtn(self.main_wid)
        self.up_btn.hide()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.columns = self.get_columns()
        self.setup_grid_main()

        SignalsApp.all_.thumbnail_select.connect(self.select_new_widget)
        SignalsApp.all_.grid_thumbnails_cmd.connect(self.grid_thumbnails_cmd)
        SignalsApp.all_.win_img_view_open_in.connect(self.open_in_view)

    def grid_thumbnails_cmd(self, flag: str):
        if flag == "resize":
            self.resize_()
        elif flag == "to_top":
            self.scroll_top()
        elif flag == "reload":
            self.reload_thumbnails()
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

    def scroll_top(self):
        self.verticalScrollBar().setValue(0)

    def add_more_grids(self):
        self.thumbs_dict = DbImages()
        self.thumbs_dict.finished_.connect(self.add_more_grids_fin)
        self.thumbs_dict.get()

    def add_more_grids_fin(self, thumbs_dict: dict[str, list[DbImage]]):
        if thumbs_dict:
            for date, db_images in thumbs_dict.items():
                self.create_image_grid(date, db_images)

        ln_thumbs = sum(len(lst) for lst in thumbs_dict.values())

        if ln_thumbs // Dynamic.current_photo_limit == 0:
            h_wid = QWidget()
            h_layout = LayoutHor()
            h_wid.setLayout(h_layout)
            h_layout.setContentsMargins(0, 0, 0, 10)
            self.thumbnails_layout.addWidget(h_wid)

            limit_btn = LimitBtn()
            limit_btn._clicked.connect(self.add_more_grids)
            h_layout.addWidget(limit_btn)

    def setup_grid_main(self):
        
        if hasattr(self, "thumbnails_wid"):
            self.thumbnails_wid.deleteLater()

        self.reset_widget_data()
        self.current_widgets.clear()

        self.thumbnails_wid = QWidget()

        self.thumbnails_layout = LayoutVer()
        self.thumbnails_layout.setContentsMargins(5, 10, 5, 0)
        self.thumbnails_layout.setAlignment(self.topleft)

        self.thumbnails_wid.setLayout(self.thumbnails_layout)

        self.thumbs_dict = DbImages()
        self.thumbs_dict.finished_.connect(self.setup_grid_fin)
        self.thumbs_dict.get()

    def setup_grid_fin(self, thumbs_dict: dict[str, list[DbImage]]):
        if thumbs_dict:

            above_thumbs = AboveThumbs(self.width())
            above_thumbs.setContentsMargins(9, 0, 0, 0)
            self.thumbnails_layout.addWidget(above_thumbs)

            for date, db_images in thumbs_dict.items():
                self.create_image_grid(date, db_images)

        else:
            no_images = AboveThumbsNoImages(self.width())
            no_images.setContentsMargins(9, 0, 0, 0)
            self.thumbnails_layout.addWidget(no_images)

        ln_thumbs = sum(len(lst) for lst in thumbs_dict.values())

        if ln_thumbs == LIMIT:
            h_wid = QWidget()
            h_layout = LayoutHor()
            h_wid.setLayout(h_layout)
            h_layout.setContentsMargins(0, 0, 0, 10)
            self.thumbnails_layout.addWidget(h_wid)

            limit_btn = LimitBtn()
            limit_btn._clicked.connect(self.add_more_grids)
            h_layout.addWidget(limit_btn)

        self.main_layout.addWidget(self.thumbnails_wid)
        self.main_wid.setFocus()

    def reload_thumbnails(self):
        self.up_btn.hide()
        self.setup_grid_main()

    def create_image_grid(self, date: str, db_images: list[DbImage]):
        title_label = Title(title=date, db_images=db_images, width=self.width())
        title_label.setContentsMargins(5, 0, 0, 10)
        self.thumbnails_layout.addWidget(title_label)

        grid_widget = QWidget()
        self.thumbnails_layout.addWidget(grid_widget)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(self.topleft)
        grid_layout.setContentsMargins(0, 0, 0, 30)
        self.current_widgets[grid_layout] = []

        grid_widget.setLayout(grid_layout)

        row, col = 0, 0

        for x, db_image in enumerate(db_images):
        
            wid = Thumbnail(
                pixmap=db_image.pixmap,
                src=db_image.src,
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

    def add_widget_data(self, wid: Thumbnail, row: int, col: int):
        wid.row, wid.col = row, col
        self.cell_to_wid[row, col] = wid
        Thumbnail.path_to_wid[wid.src] = wid

    def reset_widget_data(self):
        self.curr_cell: tuple = (0, 0)
        self.all_grids_row = 0
        self.cell_to_wid.clear()
        Thumbnail.path_to_wid.clear()

    def open_in_view(self, wid: Thumbnail):
        wid = Thumbnail.path_to_wid.get(wid.src)

        if isinstance(wid, Thumbnail):
            from ..win_image_view import WinImageView
            self.win_image_view = WinImageView(src=wid.src)
            self.win_image_view.center_relative_parent(self)
            self.win_image_view.show()

    def get_columns(self):
        return max(self.ww // (THUMB_W[JsonData.curr_size_ind] + (THUMB_MARGIN)), 1)

    def resize_(self):
        for grid_layout, widgets in self.current_widgets.items():
            for widget in widgets:
                widget.setup()
        self.rearrange()

    def rearrange(self):

        if not hasattr(self, "first_load"):
            setattr(self, "first_load", True)
            return

        self.ww = self.width()
        self.columns = self.get_columns()

        self.reset_selection()
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

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        wid: Thumbnail

        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier and a0.key() == Qt.Key.Key_I:
            wid = self.cell_to_wid.get(self.curr_cell)

            if Utils.smb_check():
                OpenWins.info(self, wid.src)
            else:
                self.smb_win = WinSmb()
                self.smb_win.center_relative_parent(self)
                self.smb_win.show()

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
        self.menu_ = ContextCustom(event=a0)

        reload = ReloadGui(self.menu_, "")
        self.menu_.addAction(reload)

        self.menu_.show_menu()