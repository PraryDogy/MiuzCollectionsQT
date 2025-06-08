import gc
import os

from PyQt5.QtCore import QMimeData, QPoint, QRect, QSize, Qt, QTimer, QUrl
from PyQt5.QtGui import (QContextMenuEvent, QDrag, QKeyEvent, QMouseEvent,
                         QPixmap, QResizeEvent)
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
                             QRubberBand, QScrollArea, QSizePolicy, QWidget)

from base_widgets import ContextCustom, LayoutVer, SvgBtn
from cfg import Dynamic, JsonData, Static, ThumbData
from filters import Filter
from lang import Lang
from main_folders import MainFolder
from signals import SignalsApp
from utils.utils import Utils

from .._runnable import UThreadPool
from ..actions import (CopyName, CopyPath, FavActionDb, MenuTypes, WinInfoAction,
                       OpenInView, RemoveFiles, Reveal, Save, ScanerRestart)
from ..win_info import WinInfo
from ..win_remove_files import RemoveFilesWin
from ..win_smb import WinSmb
from ._db_images import DbImage, DbImages
from .cell_widgets import ImgWid, TextWid, Thumbnail, Title

UP_SVG = os.path.join(Static.images_dir, "up.svg")
UP_STYLE = f"""
    background: {Static.gray_color};
    border-radius: 22px;
"""
FIRST_LOAD = "first_load"
MORE = "more"
FIRST = "first"

class NoImagesLabel(QLabel):
    def __init__(self):
        super().__init__()

        enabled_filters = [
            filter.names[JsonData.lang_ind].lower()
            for filter in Filter.filters_list
            if filter.value
            ]

        if Dynamic.date_start:
            noimg_t = [
                f"{Lang.no_photo}: ",
                f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"
            ]
            noimg_t = "".join(noimg_t)

        elif enabled_filters:
            enabled_filters = ", ".join(enabled_filters)
            noimg_t = f"{Lang.no_photo}: {enabled_filters}"

        elif Dynamic.search_widget_text:
            noimg_t = f"{Lang.no_photo}: {Dynamic.search_widget_text}"
        
        else:
            noimg_t = Lang.no_photo

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
        SignalsApp.instance.grid_thumbnails_cmd.emit("to_top")
        return super().mouseReleaseEvent(a0)
    

class Grid(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setStyleSheet("QScrollArea { border: none; }")

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.scroll_wid = QWidget()
        self.setWidget(self.scroll_wid)
        
        self.scroll_layout = LayoutVer()
        self.scroll_wid.setLayout(self.scroll_layout)

        self.col_count: int = 0

        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)
        SignalsApp.instance.grid_thumbnails_cmd.connect(self.signals_cmd)
        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")

        self.origin_pos = QPoint()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.scroll_wid)

        self.wid_under_mouse: Thumbnail = None

    def signals_cmd(self, flag: str):
        if flag == "resize":
            self.resize_thumbnails()
        elif flag == "to_top":
            self.verticalScrollBar().setValue(0)
        elif flag == "reload":
            self.load_db_images(flag=FIRST)
        else:
            raise Exception("widgets > grid > main > wrong flag", flag)
        
        self.setFocus()

    def load_db_images(self, flag: str):

        if flag == FIRST:
            Dynamic.grid_offset = 0
            cmd_ = lambda db_images: self.create_grid(db_images)

        elif flag == MORE:
            Dynamic.grid_offset += Static.GRID_LIMIT
            cmd_ = lambda db_images: self.grid_more(db_images)
        
        else: 
            raise Exception("wrong flag", flag)
        
        self.task_ = DbImages()
        self.task_.signals_.finished_.connect(cmd_)
        UThreadPool.start(self.task_)

    def reload_rubber(self):
        self.rubberBand.deleteLater()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.scroll_wid)

    def create_grid(self, db_images: dict[str, list[DbImage]]):
        widgets = self.scroll_wid.findChildren(QWidget)
        if self.rubberBand in widgets:
            widgets.remove(self.rubberBand)
        for wid in widgets:
            wid.deleteLater()

        self.up_btn = UpBtn(self.scroll_wid)
        self.up_btn.hide()

        self.selected_widgets: list[Thumbnail] = []
        self.grid_widgets: list[QGridLayout] = []
        self.cell_to_wid: dict[tuple, Thumbnail] = {}
        self.global_row = 0
        Thumbnail.path_to_wid.clear()
    
        if not db_images:
            self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_title = NoImagesLabel()
            self.scroll_layout.addWidget(error_title, alignment=Qt.AlignmentFlag.AlignCenter)

        else:
            self.scroll_layout.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )

            Thumbnail.calculate_size()
            self.col_count = self.get_max_col()

            for date, db_images_list in db_images.items():
                self.single_grid(
                    date=date,
                    db_images=db_images_list
                )

            spacer = QWidget()
            self.scroll_layout.addWidget(spacer)

    def single_grid(self, date: str, db_images: list[DbImage]):

        title = Title(title=date, db_images=db_images)
        self.scroll_layout.addWidget(title)

        grid_wid = QWidget()
        self.scroll_layout.addWidget(grid_wid)
        self.grid_widgets.append(grid_wid)

        grid_lay = QGridLayout()
        grid_lay.setContentsMargins(0, 0, 0, 40)
        grid_lay.setSpacing(2)
        grid_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid_wid.setLayout(grid_lay)

        # Флаг, указывающий, нужно ли добавить последнюю строку в сетке.
        add_last_row = False
        row, col = 0, 0


        for db_image in db_images:

            wid = Thumbnail(
                pixmap=db_image.pixmap,
                short_src=db_image.short_src,
                coll=db_image.coll,
                fav=db_image.fav
            )
            wid.set_no_frame()
            Thumbnail.path_to_wid[wid.short_src] = wid
            self.cell_to_wid[self.global_row, col] = wid
            wid.row, wid.col = self.global_row, col
            grid_lay.addWidget(wid, row, col)
            col += 1

            add_last_row = True

            # Если достигли максимального количества столбцов:
            # Сбрасываем индекс столбца.
            # Переходим к следующей строке.
            # Указываем, что текущая строка завершена.
            if col >= self.col_count:  

                col = 0

                row += 1
                self.global_row += 1

                add_last_row = False

        # Если после цикла остались элементы в неполной последней строке,
        # переходим к следующей строке для корректного добавления
        # новых элементов в будущем.
        if add_last_row:
            self.global_row += 1
            row += 1
            col = 0

    def grid_more(self, db_images: dict[str, list[DbImage]]):
        if db_images:
            for date, db_images_list in db_images.items():
                self.single_grid(
                    date=date,
                    db_images=db_images_list
                )
    
    def open_in_view(self, wid: Thumbnail):

        assert isinstance(wid, Thumbnail)
        from ..win_image_view import WinImageView

        if len(self.selected_widgets) == 1:
            path_to_wid = Thumbnail.path_to_wid
            is_selection = False
        else:
            path_to_wid = {i.short_src: i for i in self.selected_widgets}
            is_selection = True

        self.win_image_view = WinImageView(wid.short_src, path_to_wid, is_selection)
        self.win_image_view.center_relative_parent(self.window())

        self.win_image_view.switch_image_sig.connect(
            lambda img_path: self.select_viewed_image(img_path)
        )

        self.win_image_view.closed_.connect(
            lambda: self.img_view_closed(self.win_image_view)
        )

        self.win_image_view.show()

    def img_view_closed(self, win: QWidget):

        del win
        gc.collect()

    def select_viewed_image(self, path: str):
        wid = Thumbnail.path_to_wid.get(path)

        if wid:
            self.clear_selected_widgets()
            self.add_and_select_widget(wid=wid)

    def get_max_col(self):
        return self.width() // (
            ThumbData.THUMB_W[Dynamic.thumb_size_ind] # + ThumbData.OFFSET 
            )

    def resize_thumbnails(self):
        "изменение размера Thumbnail"

        Thumbnail.calculate_size()

        for path, wid in Thumbnail.path_to_wid.items():
            wid.setup()

        self.rearrange()

    def rearrange(self):
        "перетасовка сетки"

        if not hasattr(self, FIRST_LOAD):
            setattr(self, FIRST_LOAD, False)
            return

        Thumbnail.path_to_wid.clear()
        self.cell_to_wid.clear()
        self.global_row = 0

        self.col_count = self.get_max_col()
        add_last_row = False

        for grid_wid in self.grid_widgets:

            row, col = 0, 0
            grid_lay = grid_wid.layout()

            for wid in grid_wid.findChildren(Thumbnail):

                Thumbnail.path_to_wid[wid.short_src] = wid
                self.cell_to_wid[self.global_row, col] = wid
                wid.row, wid.col = self.global_row, col
                grid_lay.addWidget(wid, row, col)

                col += 1

                add_last_row = True

                if col >= self.col_count:

                    add_last_row = False

                    col = 0

                    self.global_row += 1
                    row += 1       

            if add_last_row:

                col = 0

                self.global_row += 1
                row += 1

    def get_wid_under_mouse(self, a0: QMouseEvent) -> None | Thumbnail:
        wid = QApplication.widgetAt(a0.globalPos())
        if isinstance(wid, (ImgWid, TextWid)):
            return wid.parent()
        else:
            return None
        
    def clear_selected_widgets(self):
        for i in self.selected_widgets:
            i.set_no_frame()
        self.selected_widgets.clear()

    def add_and_select_widget(self, wid: Thumbnail):
        if isinstance(wid, Thumbnail):
            self.selected_widgets.append(wid)
            wid.set_frame()

    def remove_files(self):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        urls = [
            Utils.get_full_src(coll_folder, i.short_src)
            for i in self.selected_widgets
        ]

        self.rem_win = RemoveFilesWin(urls)
        self.rem_win.center_relative_parent(self.window())
        self.rem_win.finished_.connect(lambda urls: self.remove_finished(self.selected_widgets.copy()))
        self.rem_win.show()

    def remove_finished(self, widgets: list[Thumbnail]):
        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")

    def open_info_win_delayed(self):
        self.info_win.adjustSize()
        self.info_win.center_relative_parent(self.window())
        self.info_win.show()
            
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:

        command = Qt.KeyboardModifier.ControlModifier

        KEY_NAVI = {
            Qt.Key.Key_Left: (0, -1),
            Qt.Key.Key_Right: (0, 1),
            Qt.Key.Key_Up: (-1, 0),
            Qt.Key.Key_Down: (1, 0)
        }

        if a0.modifiers() == command and a0.key() == Qt.Key.Key_I:
            if self.selected_widgets:

                MainFolder.current.set_current_path()
                coll_folder = MainFolder.current.get_current_path()
                if coll_folder:
                    urls = [
                        Utils.get_full_src(coll_folder, i.short_src)
                        for i in self.selected_widgets
                    ]
                    self.info_win = WinInfo(urls)
                    self.info_win.finished_.connect(self.open_info_win_delayed)
                else:
                    self.smb_win = WinSmb()
                    self.smb_win.adjustSize()
                    self.smb_win.center_relative_parent(self.window())
                    self.smb_win.show()

        elif a0.modifiers() == command and a0.key() == Qt.Key.Key_A:
            for i in Thumbnail.path_to_wid.values():
                i.set_frame()
                self.selected_widgets.append(i)

        elif a0.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):

            if self.selected_widgets:
                wid = self.selected_widgets[-1]
                self.open_in_view(wid=wid)

        elif a0.key() in KEY_NAVI:
            offset = KEY_NAVI.get(a0.key())

            # если не выделено ни одного виджета
            if not self.selected_widgets:
                self.wid_under_mouse = self.cell_to_wid.get((0, 0))
            else:
                self.wid_under_mouse = self.selected_widgets[-1]

            # если нет даже первого виджета значит сетка пуста
            if not self.wid_under_mouse:
                return

            coords = (
                self.wid_under_mouse.row + offset[0], 
                self.wid_under_mouse.col + offset[1]
            )

            next_wid = self.cell_to_wid.get(coords)

            if next_wid is None:
                if a0.key() == Qt.Key.Key_Right:
                    coords = (
                        self.wid_under_mouse.row + 1, 
                        0
                    )
                elif a0.key() == Qt.Key.Key_Left:
                    coords = (
                        self.wid_under_mouse.row - 1,
                        self.col_count - 1
                    )
                next_wid = self.cell_to_wid.get(coords)

            if next_wid:
                self.clear_selected_widgets()
                self.add_and_select_widget(next_wid)
                self.ensureWidgetVisible(next_wid)
                self.wid_under_mouse = next_wid

        return super().keyPressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() != Qt.MouseButton.LeftButton:
            return

        if self.rubberBand.isVisible():
            rect = QRect(self.origin_pos, a0.pos()).normalized()
            self.rubberBand.hide()
            ctrl = a0.modifiers() == Qt.KeyboardModifier.ControlModifier

            for wid in self.cell_to_wid.values():
                
                widgets = wid.findChildren((TextWid, ImgWid))

                intersects = False
                for child in widgets:
                    top_left = child.mapTo(self, QPoint(0, 0))
                    child_rect = QRect(top_left, child.size())
                    if rect.intersects(child_rect):
                        intersects = True
                        break

                if intersects:
                    if ctrl:
                        if wid in self.selected_widgets:
                            wid.set_no_frame()
                            self.selected_widgets.remove(wid)
                        else:
                            wid.set_frame()
                            self.selected_widgets.append(wid)
                    else:
                        if wid not in self.selected_widgets:
                            wid.set_frame()
                            self.selected_widgets.append(wid)
                else:
                    if not ctrl and wid in self.selected_widgets:
                        wid.set_no_frame()
                        self.selected_widgets.remove(wid)
            return

        self.wid_under_mouse = self.get_wid_under_mouse(a0)

        # клик по сетке
        if not self.wid_under_mouse:
            self.clear_selected_widgets()
            return

        if a0.modifiers() == Qt.KeyboardModifier.ShiftModifier:

            # шифт клик: если не было выделенных виджетов
            if not self.selected_widgets:

                self.add_and_select_widget(self.wid_under_mouse)

            # шифт клик: если уже был выделен один / несколько виджетов
            else:

                coords = list(self.cell_to_wid)
                start_pos = (self.selected_widgets[-1].row, self.selected_widgets[-1].col)

                # шифт клик: слева направо (по возрастанию)
                if coords.index((self.wid_under_mouse.row, self.wid_under_mouse.col)) > coords.index(start_pos):
                    start = coords.index(start_pos)
                    end = coords.index((self.wid_under_mouse.row, self.wid_under_mouse.col))
                    coords = coords[start : end + 1]

                # шифт клик: справа налево (по убыванию)
                else:
                    start = coords.index((self.wid_under_mouse.row, self.wid_under_mouse.col))
                    end = coords.index(start_pos)
                    coords = coords[start : end]

                # выделяем виджеты по срезу координат coords
                for i in coords:

                    wid_ = self.cell_to_wid.get(i)

                    if wid_ not in self.selected_widgets:
                        self.add_and_select_widget(wid=wid_)

        elif a0.modifiers() == Qt.KeyboardModifier.ControlModifier:

            # комманд клик: был выделен виджет, снять выделение
            if self.wid_under_mouse in self.selected_widgets:
                self.selected_widgets.remove(self.wid_under_mouse)
                self.wid_under_mouse.set_no_frame()

            # комманд клик: виджет не был виделен, выделить
            else:
                self.add_and_select_widget(self.wid_under_mouse)

        else:
            self.clear_selected_widgets()
            self.add_and_select_widget(self.wid_under_mouse)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:

        if not hasattr(self, FIRST_LOAD):
            setattr(self, FIRST_LOAD, False)
            return

        self.resize_timer.stop()
        self.resize_timer.start(10)
        self.up_btn.hide()
        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:

        self.menu_ = ContextCustom(event=a0)
        clicked_wid = self.get_wid_under_mouse(a0=a0)

        # клик по пустому пространству
        if not clicked_wid:
            self.clear_selected_widgets()
            reload = ScanerRestart(parent=self.menu_)
            self.menu_.addAction(reload)
            self.menu_.addSeparator()
            types_ = MenuTypes(parent=self.menu_)
            self.menu_.addMenu(types_)

        # клик по виджету
        else:

            # если не было выделено ни одного виджет ранее
            # то выделяем кликнутый
            if not self.selected_widgets:
                self.add_and_select_widget(wid=clicked_wid)

            # если есть выделенные виджеты, но кликнутый виджет не выделены
            # то снимаем выделение с других и выделяем кликнутый
            elif clicked_wid not in self.selected_widgets:
                self.clear_selected_widgets()
                self.add_and_select_widget(wid=clicked_wid)

            urls = [
                i.short_src
                for i in self.selected_widgets
            ]

            cmd_ = lambda: self.open_in_view(wid=clicked_wid)
            view = OpenInView(parent_=self.menu_)
            view._clicked.connect(cmd_)
            self.menu_.addAction(view)


            info = WinInfoAction(
                parent=self.menu_,
                win=self.window(),
                urls=urls
            )
            self.menu_.addAction(info)

            self.fav_action = FavActionDb(
                parent=self.menu_,
                short_src=clicked_wid.short_src,
                fav_value=clicked_wid.fav_value
                )
            self.fav_action.finished_.connect(clicked_wid.change_fav)
            self.menu_.addAction(self.fav_action)

            self.menu_.addSeparator()

            copy = CopyPath(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src
            )
            self.menu_.addAction(copy)

            copy_name = CopyName(
                parent=self.menu_,
                win=self.window(),
                short_src=clicked_wid.short_src
            )
            self.menu_.addAction(copy_name)

            reveal = Reveal(
                parent=self.menu_,
                win=self.window(),
                short_src=urls
            )
            self.menu_.addAction(reveal)

            save_as = Save(
                parent=self.menu_,
                win=self.window(),
                short_src=urls,
                save_as=True
                )
            self.menu_.addAction(save_as)

            save = Save(
                parent=self.menu_,
                win=self.window(),
                short_src=urls,
                save_as=False
                )
            self.menu_.addAction(save)

            self.menu_.addSeparator()

            rem = RemoveFiles(self.menu_, len(self.selected_widgets))
            rem.triggered.connect(self.remove_files)
            self.menu_.addAction(rem)

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
            self.load_db_images(flag=MORE)

    def mouseDoubleClickEvent(self, a0):
        if self.wid_under_mouse:
            self.clear_selected_widgets()
            self.add_and_select_widget(self.wid_under_mouse)
            self.open_in_view(self.wid_under_mouse)

    def mousePressEvent(self, a0):
        self.origin_pos = a0.pos()
        self.wid_under_mouse = self.get_wid_under_mouse(a0)
        return super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0):
        try:
            distance = (a0.pos() - self.origin_pos).manhattanLength()
        except AttributeError as e:
            Utils.print_error(e)
            return

        if distance < QApplication.startDragDistance():
            return

        if self.wid_under_mouse is None and not self.rubberBand.isVisible():
            self.rubberBand.setGeometry(QRect(self.origin_pos, QSize()))
            self.rubberBand.show()

        if self.rubberBand.isVisible():
            origin = self.origin_pos
            current = a0.pos()
            rect = QRect(origin, current).normalized()
            self.rubberBand.setGeometry(rect)
            return

        if self.wid_under_mouse and self.wid_under_mouse not in self.selected_widgets:
            self.clear_selected_widgets()
            self.add_and_select_widget(self.wid_under_mouse)
            QTimer.singleShot(100, self.wid_under_mouse.set_frame)

        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        if coll_folder:
            urls = [
                Utils.get_full_src(coll_folder, i.short_src)
                for i in self.selected_widgets
            ]
        else:
            urls = []

        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        img = os.path.join(Static.images_dir, "copy_files.png")
        img = QPixmap(img)
        self.drag.setPixmap(img)
        
        urls = [
            QUrl.fromLocalFile(i)
            for i in urls
            ]

        if urls:
            self.mime_data.setUrls(urls)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        if not urls:
            self.win_smb = WinSmb()
            self.win_smb.adjustSize()
            self.win_smb.center_relative_parent(self.window())
            self.win_smb.show()

        return super().mouseMoveEvent(a0)
