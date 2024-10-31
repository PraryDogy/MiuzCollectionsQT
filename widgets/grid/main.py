from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import QGridLayout, QScrollArea, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from signals import signals_app
from styles import Names, Themes
from utils.main_utils import MainUtils

from ..win_info import WinInfo
from ..win_smb import WinSmb
from .above_thumbs import AboveThumbs, AboveThumbsNoImages
from .db_images import DbImages, DbImage
from .limit_btn import LimitBtn
from .thumbnail import SmallThumbnail, Thumbnail
from .title import Title
from .up_btn import UpBtn


class Thumbnails(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.resize(cnf.root_g["aw"] - cnf.MENU_W, cnf.root_g["ah"])
        self.ww = cnf.root_g["aw"] - cnf.MENU_W
        self.horizontalScrollBar().setDisabled(True)
        self.setObjectName(Names.th_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.curr_cell: tuple = (0, 0)
        self.cell_to_wid: dict[tuple, Thumbnail | SmallThumbnail] = {}
        self.path_to_wid: dict[str, Thumbnail | SmallThumbnail] = {}
        self.ordered_widgets: list[Thumbnail | SmallThumbnail] = []

        # Создаем фрейм для виджетов в области скролла
        self.scroll_area_widget = QWidget(parent=self)
        self.scroll_area_widget.setObjectName(Names.th_scroll_widget)
        self.scroll_area_widget.setStyleSheet(Themes.current)
        
        # Основной лейаут фрейма в области скролла
        frame_layout = LayoutV(self.scroll_area_widget)

        thumbnails_wid = QWidget()
        self.thumbnails_layout = LayoutV()
        thumbnails_wid.setLayout(self.thumbnails_layout)
        self.thumbnails_layout.setContentsMargins(5, 10, 5, 0)
        frame_layout.addWidget(thumbnails_wid)

        self.columns = self.get_columns()
        self.init_ui()

        frame_layout.addStretch(1)
        self.setWidget(self.scroll_area_widget)

        signals_app.reload_thumbnails.connect(self.reload_thumbnails)
        signals_app.scroll_top.connect(self.scroll_top)
        signals_app.move_to_wid.connect(self.move_to_wid)
        signals_app.select_new_wid.connect(self.select_new_widget)

    def checkScrollValue(self, value):
        self.up_btn.move(
            self.width() - 60,
            self.height() - 60 + value
            )
        self.up_btn.setVisible(value > 0)
        self.up_btn.raise_()

    def scroll_top(self):
        self.verticalScrollBar().setValue(0)

    def init_ui(self):
        thumbs_dict = DbImages()
        thumbs_dict = thumbs_dict.get()
        cnf.images.clear()

        if thumbs_dict:
            above_thumbs = AboveThumbs(self.width())
            above_thumbs.setContentsMargins(9, 0, 0, 0)
            self.thumbnails_layout.addWidget(above_thumbs)

            self.curr_cell: tuple = (0, 0)
            # self.main_row, self.main_col = 0, 0
            self.all_grids_row = 0
            self.cell_to_wid.clear()
            self.path_to_wid.clear()
            self.ordered_widgets.clear()

            for date, db_images in thumbs_dict.items():
                self.images_grid(date, db_images)

        else:
            no_images = AboveThumbsNoImages(self.width())
            no_images.setContentsMargins(9, 0, 0, 0)
            self.thumbnails_layout.addWidget(no_images)

        ln_thumbs = sum(len(lst) for lst in thumbs_dict.values())
        if ln_thumbs == cnf.current_photo_limit:
            h_wid = QWidget()
            h_layout = LayoutH()
            h_wid.setLayout(h_layout)
            h_layout.setContentsMargins(0, 0, 0, 10)
            self.thumbnails_layout.addWidget(h_wid)
            h_layout.addWidget(LimitBtn())

        self.up_btn = UpBtn(self.scroll_area_widget)
        self.up_btn.setVisible(False)
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.scroll_area_widget.setFocus()

    def reload_thumbnails(self):
        MainUtils.clear_layout(self.thumbnails_layout)
        self.up_btn.deleteLater()
        self.init_ui()

    def images_grid(self, date: str, db_images: list[DbImage]):
        img_src_list = [db_image.src for db_image in db_images]
        title_label = Title(title=date, images=img_src_list, width=self.width())
        title_label.setContentsMargins(9, 0, 0, 0)
        self.thumbnails_layout.addWidget(title_label)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_widget.setLayout(grid_layout)
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        grid_layout.setContentsMargins(0, 0, 0, 30)

        row, col = 0, 0

        if cnf.small_view:
            thumb = SmallThumbnail
        else:
            thumb = Thumbnail

        for db_image in db_images:
            wid = thumb(img=db_image.img, src=db_image.src, coll=db_image.coll, images_date=date)
            wid.select.connect(lambda w=wid: self.select_new_widget(w))
            wid.open_in_view.connect(lambda src, w=wid: self.open_in_view(w))

            self.add_widget_data(wid, self.all_grids_row, col)
            grid_layout.addWidget(wid, row, col)

            col += 1
            if col >= self.columns:
                col = 0
                row += 1
                self.all_grids_row += 1

        self.all_grids_row += 1

        self.thumbnails_layout.addWidget(grid_widget)

    def select_new_widget(self, data: tuple | str | Thumbnail | SmallThumbnail):
        if isinstance(data, (Thumbnail, SmallThumbnail)):
            coords = data.row, data.col
            new_wid = data

        elif isinstance(data, tuple):
            coords = data
            new_wid = self.cell_to_wid.get(data)

        elif isinstance(data, str):
            new_wid = self.path_to_wid.get(data)
            coords = new_wid.row, new_wid.col

        prev_wid = self.cell_to_wid.get(self.curr_cell)

        if isinstance(new_wid, (Thumbnail, SmallThumbnail)):
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

        if isinstance(widget, (Thumbnail, SmallThumbnail)):
            widget.regular_style()
            self.curr_cell: tuple = (0, 0)

    def add_widget_data(self, wid: Thumbnail | SmallThumbnail, row: int, col: int):
        wid.row, wid.col = row, col
        self.cell_to_wid[row, col] = wid
        self.path_to_wid[wid.src] = wid
        self.ordered_widgets.append(wid)

    def open_in_view(self, wid: Thumbnail | SmallThumbnail):
        wid = self.path_to_wid.get(wid.src)

        if isinstance(wid, (Thumbnail, SmallThumbnail)):
            from ..win_image_view import WinImageView
            self.win_image_view = WinImageView(parent=self, src=wid.src)
            self.win_image_view.show()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        wid: Thumbnail

        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier and a0.key() == Qt.Key.Key_I:
            wid = self.cell_to_wid.get(self.curr_cell)

            if MainUtils.smb_check():
                self.win_info = WinInfo(src=wid.src, parent=self)
                self.win_info.show()
            else:
                self.smb_win = WinSmb(parent=self.my_parent)
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
        self.up_btn.setVisible(False)

        if abs(a0.size().width() - self.ww) >= cnf.THUMBSIZE - cnf.THUMBPAD - cnf.THUMBPAD:
            self.ww = a0.size().width()
            self.columns = self.get_columns()
            self.reload_thumbnails()
        return super().resizeEvent(a0)

    def get_columns(self):
        return max(self.width() // (cnf.THUMBSIZE + cnf.THUMBPAD), 1)
    
    def move_to_wid(self, wid):
        self.ensureWidgetVisible(wid)