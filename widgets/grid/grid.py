import os
from typing import Literal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
                             QScrollArea, QSizePolicy, QWidget)

from base_widgets import ContextCustom, LayoutHor, LayoutVer, SvgBtn
from cfg import Dynamic, Filters, JsonData, Static, ThumbData
from lang import Lang
from signals import SignalsApp
from utils.utils import UThreadPool, Utils

from ..actions import (CopyPath, FavActionDb, MenuTypes, OpenInfoDb,
                       OpenInView, OpenWins, Reveal, Save, ScanerRestart)
from ..bar_bottom import BarBottom
from ._db_images import DbImage, DbImages
from .cell_widgets import CellWid, ImgWid, TextWid, Thumbnail, Title

UP_SVG = os.path.join(Static.IMAGES, "up.svg")
UP_STYLE = f"""
    background: {Static.RGB_GRAY};
    border-radius: 22px;
"""


class NoImagesLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        self.setStyleSheet(Static.TITLE_NORMAL)

        enabled_filters = [
            filter.names[JsonData.lang_ind].lower()
            for filter in Filters.current
            if filter.value
            ]

        if Dynamic.date_start:
            noimg_t = [
                f"{Lang.no_photo}: ",
                f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"
            ]
            noimg_t = "".join(noimg_t)
            self.setText(noimg_t)

        elif enabled_filters:
            enabled_filters = ", ".join(enabled_filters)
            noimg_t = f"{Lang.no_photo}: {enabled_filters}"
            self.setText(noimg_t)

        elif Dynamic.search_widget_text:
            noimg_t = f"{Lang.no_photo}: {Dynamic.search_widget_text}"
            self.setText(noimg_t)


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
        self.resize(
            Dynamic.root_g["aw"] - Static.MENU_LEFT_WIDTH,
            Dynamic.root_g["ah"]
        )
        self.ww = Dynamic.root_g["aw"] - Static.MENU_LEFT_WIDTH
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.selected_widgets: list[Thumbnail] = []


        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.curr_cell: tuple = None
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

        if hasattr(self, "grid_wid"):
            self.grid_wid.deleteLater()

        self.deselect_wid()
        self.reset_grid_data()
        self.up_btn.hide()

        self.grid_wid = QWidget()
        self.scroll_layout.addWidget(self.grid_wid)

        self.grid_lay = QGridLayout()
        self.grid_lay.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.grid_lay.setSpacing(Static.GRID_SPACING)
        self.grid_wid.setLayout(self.grid_lay)

        if not db_images:

            error_title = NoImagesLabel()
            self.grid_lay.addWidget(error_title, self.row, self.col)

        else:
            Thumbnail.calculate_size()
            for date, db_images in db_images.items():
                self.single_grid(
                    date=date,
                    db_images=db_images,
                    max_col=self.get_max_col()
                )

    def single_grid(self, date: str, db_images: list[DbImage], max_col: int):

        title = Title(title=date, db_images=db_images)
        title.r_click.connect(self.deselect_wid)
        # self.set_cell_coords(title)
        self.grid_lay.addWidget(title, self.row, self.col, 1, max_col + 1)

        self.col = 0
        self.row += 1

        # Флаг, указывающий, нужно ли добавить последнюю строку в сетке.
        add_last_row = False

        for db_image in db_images:

            wid = Thumbnail(
                pixmap=db_image.pixmap,
                short_src=db_image.short_src,
                coll=db_image.coll,
                fav=db_image.fav
            )
            wid.select.connect(lambda w=wid: self.select_wid(w))
            self.set_cell_coords(wid)
            self.set_path_to_wid(wid)
            self.grid_lay.addWidget(wid, self.row, self.col)

            self.col += 1
            add_last_row = True

            # Если достигли максимального количества столбцов:
            # Сбрасываем индекс столбца.
            # Переходим к следующей строке.
            # Указываем, что текущая строка завершена.
            if self.col >= max_col:  
                self.col = 0
                self.row += 1
                add_last_row = False

        # Если после цикла остались элементы в неполной последней строке,
        # переходим к следующей строке для корректного добавления
        # новых элементов в будущем.
        if add_last_row:
            self.row += 1
            self.col = 0

    def grid_more(self, db_images: dict[str, list[DbImage]]):
        if db_images:
            for date, db_images in db_images.items():
                self.single_grid(
                    date=date,
                    db_images=db_images,
                    max_col=self.get_max_col()
                )

    def set_curr_sell(self, coords: tuple):
        self.curr_cell = coords

    def get_curr_cell(self):
        return self.cell_to_wid.get(self.curr_cell)
    
    def get_cell(self, coords: tuple):
        return self.cell_to_wid.get(coords)

    def set_cell_coords(self, wid: CellWid):
        coords = self.row, self.col
        self.cell_to_wid[coords] = wid
        wid.row, wid.col = coords

    def set_path_to_wid(self, wid: Thumbnail):
        Thumbnail.path_to_wid[wid.short_src] = wid

    def get_path_to_wid(self, src: str):
        return Thumbnail.path_to_wid.get(src)

    def reset_grid_data(self):
        self.cell_to_wid.clear()
        Thumbnail.path_to_wid.clear()
        self.row, self.col = 0, 0
        self.curr_cell = None

    def select_wid(self, data: tuple | str | Thumbnail):
        if isinstance(data, Thumbnail):
            coords = data.row, data.col
            new_wid = data

        elif isinstance(data, tuple):
            coords = data
            new_wid = self.get_cell(coords)

        elif isinstance(data, str):
            new_wid = self.get_path_to_wid(src=data)
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
            new_wid.set_frame()
            self.ensureWidgetVisible(new_wid)

            self.set_curr_sell(coords)

            if isinstance(BarBottom.path_label, QLabel):
                t = f"{new_wid.collection}: {new_wid.name}"
                BarBottom.path_label.setText(t)

            return new_wid

        return None

    def deselect_wid(self):

        wid = self.get_curr_cell()
        if isinstance(wid, Thumbnail | Title):
            wid.set_no_frame()

        assert isinstance(BarBottom.path_label, QLabel)
        BarBottom.path_label.setText("")

    def open_in_view(self, wid: Thumbnail):
        assert isinstance(wid, Thumbnail)
        from ..win_image_view import WinImageView
        self.win_image_view = WinImageView(short_src=wid.short_src)
        self.win_image_view.center_relative_parent(self.window())
        self.win_image_view.show()

    def get_max_col(self):
        return self.ww // (
            ThumbData.THUMB_W[Dynamic.thumb_size_ind] + ThumbData.OFFSET 
            )

    def resize_thumbnails(self):
        "изменение размера Thumbnail"

        Thumbnail.calculate_size()

        for thumb in self.grid_wid.findChildren(Thumbnail):
            thumb.setup()

        self.rearrange()

    def reselect_wid(func: callable):

        def wrapper(self, *args, **kwargs):

            assert isinstance(self, Grid)

            wid = self.get_curr_cell()
            src = wid.short_src if isinstance(wid, Thumbnail) else None

            func(self, *args, **kwargs)

            if src:
                wid = self.select_wid(src)  

                if wid:
                    coords = (wid.row, wid.col)
                    self.set_curr_sell(coords)

        return wrapper

    @reselect_wid
    def rearrange(self):
        "перетасовка сетки"

        if not hasattr(self, "first_load"):
            setattr(self, "first_load", True)
            return

        # высчитываем новый размер сетки и сбрасываем все данные прошлой сетки 
        self.deselect_wid()
        self.reset_grid_data()
        self.ww = self.width()
        max_col = self.get_max_col()

        add_last_row = False

        for wid in self.grid_wid.findChildren((Thumbnail, Title)):

            if isinstance(wid, Title):
                self.col = 0
                self.row += 1

                # self.set_cell_coords(wid)
                self.grid_lay.addWidget(wid, self.row, self.col, 1, max_col)

                self.col = 0
                self.row += 1

            elif isinstance(wid, Thumbnail):
                self.set_cell_coords(wid)
                self.set_path_to_wid(wid)
                self.grid_lay.addWidget(wid, self.row, self.col)
                self.col += 1
                add_last_row = True


            if self.col >= max_col:
                add_last_row = False
                self.col = 0
                self.row += 1       

        if add_last_row:
            self.col = 0
            self.row += 1
    
    def get_wid(self, a0: QMouseEvent) -> None | Thumbnail:
        wid = QApplication.widgetAt(a0.globalPos())
        if isinstance(wid, (ImgWid, TextWid)):
            return wid.parent()
        else:
            return None
            
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:

        command = Qt.KeyboardModifier.ControlModifier

        offsets = {
            Qt.Key.Key_Left: (0, -1),
            Qt.Key.Key_Right: (0, 1),
            Qt.Key.Key_Up: (-1, 0),
            Qt.Key.Key_Down: (1, 0)
        }

        if a0.modifiers() == command and a0.key() == Qt.Key.Key_I:

            if self.selected_widgets:
            
                wid = self.selected_widgets[-1]
                for i in self.selected_widgets:
                    i.set_no_frame()
                self.selected_widgets.clear()
                self.selected_widgets.append(wid)
                wid.set_frame()

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

            if self.selected_widgets:
                wid = self.selected_widgets[-1]
                for i in self.selected_widgets:
                    i.set_no_frame()
                self.selected_widgets.clear()
                self.selected_widgets.append(wid)
                wid.set_frame()
                self.open_in_view(wid=wid)

        elif a0.key() in offsets:

            print(self.cell_to_wid)

            if self.selected_widgets:

                wid = self.selected_widgets[-1]

                offset = offsets.get(a0.key())
                coords = (
                    wid.row + offset[0], 
                    wid.col + offset[1]
                )

                wid = self.cell_to_wid.get(coords)

                if wid and isinstance(wid, Thumbnail):
                    for i in self.selected_widgets:
                        i.set_no_frame()
                    self.selected_widgets.clear()
                    self.selected_widgets.append(wid)
                    wid.set_frame()

                else:
                    return

        return super().keyPressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:

        if a0.button() != Qt.MouseButton.LeftButton:
            return

        clicked_wid: Thumbnail | None = self.get_wid(a0=a0)

        # клик по сетке
        if not clicked_wid:

            for i in self.selected_widgets:
                i.set_no_frame()

            self.selected_widgets.clear()
            self.curr_cell = None
            return

        if a0.modifiers() == Qt.KeyboardModifier.ShiftModifier:

            # шифт клик: если не было выделенных виджетов
            if not self.selected_widgets:

                clicked_wid.set_frame()
                self.selected_widgets.append(clicked_wid)
                self.curr_cell = (clicked_wid.row, clicked_wid.col)

            # шифт клик: если уже был выделен один / несколько виджетов
            else:

                coords = list(self.cell_to_wid)

                # шифт клик: слева направо (по возрастанию)
                if coords.index((clicked_wid.row, clicked_wid.col)) > coords.index(self.curr_cell):
                    start = coords.index(self.curr_cell)
                    end = coords.index((clicked_wid.row, clicked_wid.col))
                    coords = coords[start : end + 1]

                # шифт клик: справа налево (по убыванию)
                else:
                    start = coords.index((clicked_wid.row, clicked_wid.col))
                    end = coords.index(self.curr_cell)
                    coords = coords[start : end]

                # выделяем виджеты по срезу координат coords
                for i in coords:

                    wid_ = self.cell_to_wid.get(i)

                    if wid_ not in self.selected_widgets:
                        wid_.set_frame()
                        self.selected_widgets.append(wid_)

        elif a0.modifiers() == Qt.KeyboardModifier.ControlModifier:

            # комманд клик: был выделен виджет, снять выделение
            if clicked_wid in self.selected_widgets:
                self.selected_widgets.remove(clicked_wid)
                clicked_wid.set_no_frame()

            # комманд клик: виджет не был виделен, выделить
            else:
                self.selected_widgets.append(clicked_wid)
                clicked_wid.set_frame()

        else:
            
            for i in self.selected_widgets:
                i.set_no_frame()

            self.selected_widgets.clear()

            self.curr_cell = (clicked_wid.row, clicked_wid.col)
            self.selected_widgets.append(clicked_wid)
            clicked_wid.set_frame()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.resize_timer.stop()
        self.resize_timer.start(500)
        self.up_btn.hide()
        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:

        self.menu_ = ContextCustom(event=a0)
        clicked_wid = self.get_wid(a0=a0)

        if not clicked_wid:

            for i in self.selected_widgets:
                i.set_no_frame()

            self.selected_widgets.clear()
            self.curr_cell = None

            reload = ScanerRestart(parent=self.menu_)
            self.menu_.addAction(reload)

            types_ = MenuTypes(parent=self.menu_)
            self.menu_.addMenu(types_)

        else:

            if not self.selected_widgets:

                clicked_wid.set_frame()
                self.selected_widgets.append(clicked_wid)
                self.curr_cell = (clicked_wid.row, clicked_wid.col)

            elif clicked_wid not in self.selected_widgets:

                for i in self.selected_widgets:
                    i.set_no_frame()
                self.selected_widgets.clear()

                clicked_wid.set_frame()
                self.selected_widgets.append(clicked_wid)
                self.curr_cell = (clicked_wid.row, clicked_wid.col)

            # cmd_ = lambda: SignalsApp.all_.win_img_view_open_in.emit(self)
            view = OpenInView(parent_=self.menu_)
            # view._clicked.connect(cmd_)
            self.menu_.addAction(view)

            info = OpenInfoDb(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src
                )
            self.menu_.addAction(info)

            self.fav_action = FavActionDb(
                parent=self.menu_,
                short_src=clicked_wid.short_src,
                fav_value=clicked_wid.fav_value
                )
            # self.fav_action.finished_.connect(self.change_fav)
            self.menu_.addAction(self.fav_action)

            self.menu_.addSeparator()

            copy = CopyPath(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src
            )
            self.menu_.addAction(copy)

            reveal = Reveal(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src
            )
            self.menu_.addAction(reveal)

            save_as = Save(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src,
                save_as=True
                )
            self.menu_.addAction(save_as)

            save = Save(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src,
                save_as=False
                )
            self.menu_.addAction(save)

            self.menu_.addSeparator()

            reload = ScanerRestart(parent=self.menu_)
            self.menu_.addAction(reload)

            types_ = MenuTypes(parent=self.menu_)
            self.menu_.addMenu(types_)

        self.menu_.show_menu()

    def checkScrollValue(self, value):
        self.up_btn.move(
            self.width() - 65,
            self.height() - 60 + value
            )
        if value > 0:
            self.up_btn.show()
            self.up_btn.raise_()
        elif value == 0:
            self.up_btn.hide()

        if value == self.verticalScrollBar().maximum():
            self.load_db_images(flag="more")