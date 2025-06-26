import gc
import os

from PyQt5.QtCore import (QEvent, QMimeData, QPoint, QRect, QSize, Qt, QTimer,
                          QUrl, pyqtSignal)
from PyQt5.QtGui import (QContextMenuEvent, QDrag, QKeyEvent, QMouseEvent,
                         QPixmap, QResizeEvent)
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
                             QRubberBand, QScrollArea, QSizePolicy, QWidget)

from cfg import Dynamic, JsonData, Static, ThumbData
from system.filters import Filter
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadDbImagesItem, LoadDbImagesTask
from system.utils import MainUtils, PixmapUtils, UThreadPool

from ._base_widgets import SvgBtn, UMenu, UVBoxLayout
from .actions import (CopyName, CopyPath, FavActionDb, MenuTypes, MoveFiles,
                      OpenInView, RemoveFiles, Reveal, Save, ScanerRestart,
                      WinInfoAction)
from .win_info import WinInfo
from .win_warn import WinWarn

UP_SVG = os.path.join(Static.images_dir, "up.svg")
UP_STYLE = f"""
    background: {Static.gray_color};
    border-radius: 22px;
"""
FIRST_LOAD = "first_load"
MORE = "more"
FIRST = "first"


class CellWid:
    def __init__(self):
        super().__init__()
        self.row = 0
        self.col = 0


class Title(QLabel, CellWid):
    r_click = pyqtSignal()
    style_ = f"""
        font-size: 18pt;
        font-weight: bold;
        border: {Static.border_transparent};
    """

    def __init__(self, title: str):
        CellWid.__init__(self)
        QLabel.__init__(self, text=title)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
            )

        self.setStyleSheet(self.style_)

    def set_frame(self):
        return

    def set_no_frame(self):
        return
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)


class TextWid(QLabel):
    def __init__(self, parent, name: str, coll: str):
        super().__init__(parent)
        self.name = name
        self.coll = coll

    def set_text(self) -> list[str]:
        name: str | list = self.name
        ind = Dynamic.thumb_size_ind
        max_row = ThumbData.MAX_ROW[ind]
        lines: list[str] = []

        if len(name) > max_row:

            first_line = name[:max_row]
            second_line = name[max_row:]

            if len(second_line) > max_row:

                second_line = self.short_text(
                    text=second_line,
                    max_row=max_row
                )

            for i in (first_line, second_line):
                lines.append(i)

        else:
            name = lines.append(name)

        self.setText("\n".join(lines))

    def short_text(self, text: str, max_row: int):
        return f"{text[:max_row - 10]}...{text[-7:]}"

    def mouseReleaseEvent(self, ev):
        return super().mouseReleaseEvent(ev)
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)
    
    def mouseDoubleClickEvent(self, a0):
        return super().mouseDoubleClickEvent(a0)
    
    
class ImgWid(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def test(self):
        ev = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            self.cursor().pos(),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        super().mouseReleaseEvent(ev)

    def mouseReleaseEvent(self, ev):
        return super().mouseReleaseEvent(ev)
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)
    
    def mouseDoubleClickEvent(self, a0):
        return super().mouseDoubleClickEvent(a0)


class Thumbnail(QFrame, CellWid):
    reload_thumbnails = pyqtSignal()
    select = pyqtSignal(str)
    path_to_wid: dict[str, "Thumbnail"] = {}

    img_frame_size = 0
    pixmap_size = 0
    thumb_w = 0
    thumb_h = 0

    style_ = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: {Static.gray_color};
        border: {Static.border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """

    def __init__(self, pixmap: QPixmap, rel_img_path: str, coll_name: str, fav: int):
        CellWid.__init__(self)
        QFrame.__init__(self)
        self.setStyleSheet(Static.border_transparent_style)

        self.img = pixmap
        self.rel_img_path = rel_img_path
        self.collection = coll_name
        self.fav_value = fav

        if fav == 0 or fav is None:
            self.name = os.path.basename(rel_img_path)
        elif fav == 1:
            self.name = Static.STAR_SYM + os.path.basename(rel_img_path)

        self.v_layout = UVBoxLayout()
        self.v_layout.setSpacing(ThumbData.SPACING)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.v_layout)

        self.img_wid = ImgWid()
        self.v_layout.addWidget(self.img_wid, alignment=Qt.AlignmentFlag.AlignCenter)
        self.text_wid = TextWid(self, self.name, coll_name)
        self.text_wid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(
            self.text_wid,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.setup()
        # self.setStyleSheet("background: BLACK;")

    @classmethod
    def calculate_size(cls):
        ind = Dynamic.thumb_size_ind
        cls.pixmap_size = ThumbData.PIXMAP_SIZE[ind]
        cls.img_frame_size = Thumbnail.pixmap_size + ThumbData.OFFSET
        cls.thumb_w = ThumbData.THUMB_W[ind]
        cls.thumb_h = ThumbData.THUMB_H[ind]

    def setup(self):
        # инициация текста
        self.text_wid.set_text()

        self.setFixedSize(Thumbnail.thumb_w, Thumbnail.thumb_h)

        # рамка вокруг pixmap при выделении Thumb
        self.img_wid.setFixedSize(Thumbnail.pixmap_size + ThumbData.OFFSET, Thumbnail.pixmap_size + ThumbData.OFFSET)
        self.img_wid.setPixmap(PixmapUtils.pixmap_scale(self.img, self.pixmap_size))

    def set_frame(self):
        self.img_wid.setStyleSheet(self.style_)
        text_style = Static.blue_bg_style + "font-size: 11px;"
        self.text_wid.setStyleSheet(text_style)

    def set_no_frame(self):
        self.img_wid.setStyleSheet(Static.border_transparent_style)
        text_style = Static.border_transparent_style + "font-size: 11px;"
        self.text_wid.setStyleSheet(text_style)

    def change_fav(self, value: int):
        if value == 0:
            self.fav_value = value
            self.name = os.path.basename(self.rel_img_path)
        elif value == 1:
            self.fav_value = value
            self.name = Static.STAR_SYM + os.path.basename(self.rel_img_path)

        self.text_wid.name = self.name
        self.text_wid.set_text()

        # удаляем из избранного и если это избранные то обновляем сетку
        if value == 0 and Dynamic.curr_coll_name == Static.NAME_FAVS:
            self.reload_thumbnails.emit()


class NoImagesLabel(QLabel):
    def __init__(self):
        super().__init__()

        enabled_filters = [
            filter.names[JsonData.lang_ind].lower()
            for filter in Filter.list_
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
    scroll_to_top = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setStyleSheet(UP_STYLE)

        v_layout = UVBoxLayout()
        self.setLayout(v_layout)

        self.svg = SvgBtn(UP_SVG, 44)
        v_layout.addWidget(self.svg)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:
            self.scroll_to_top.emit()
        return super().mouseReleaseEvent(a0)
    

class GridWidget(QWidget):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class Grid(QScrollArea):
    restart_scaner = pyqtSignal()
    remove_files = pyqtSignal(list)
    move_files = pyqtSignal(list)
    save_files = pyqtSignal(tuple)
    update_bottom_bar = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; }")
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.col_count: int = 0
        self.wid_under_mouse: Thumbnail = None
        self.origin_pos = QPoint()

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.scroll_wid = QWidget()
        self.setWidget(self.scroll_wid)
        
        self.scroll_layout = UVBoxLayout()
        self.scroll_wid.setLayout(self.scroll_layout)

        self.load_rubber()
        self.reload_thumbnails()

    def scroll_to_top(self):
        self.verticalScrollBar().setValue(0)

    def reload_thumbnails(self):
        Dynamic.grid_offset = 0
        cmd_ = lambda db_images: self.create_grid(db_images)
        self.start_load_db_images_task(cmd_)

    def load_more_thumbnails(self):
        Dynamic.grid_offset += Static.GRID_LIMIT
        cmd_ = lambda db_images: self.grid_more(db_images)
        self.start_load_db_images_task(cmd_)

    def start_load_db_images_task(self, on_finish_cmd: callable):
        self.task_ = LoadDbImagesTask()
        self.task_.signals_.finished_.connect(on_finish_cmd)
        UThreadPool.start(self.task_)

    def load_rubber(self):
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.viewport())

    def reload_rubber(self):
        self.rubberBand.deleteLater()
        self.load_rubber()

    def create_grid(self, db_images: dict[str, list[LoadDbImagesItem]]):
        widgets = self.scroll_wid.findChildren(QWidget)
        if self.rubberBand in widgets:
            widgets.remove(self.rubberBand)
        for wid in widgets:
            wid.deleteLater()
        self.reload_rubber()
        self.up_btn = UpBtn(self.scroll_wid)
        self.up_btn.scroll_to_top.connect(lambda: self.scroll_to_top())
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
                self.single_grid(date, db_images_list)
            spacer = QWidget()
            self.scroll_layout.addWidget(spacer)

    def single_grid(self, date: str, db_images: list[LoadDbImagesItem]):
        title = Title(date)
        self.scroll_layout.addWidget(title)
        grid_wid = GridWidget(date)
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
                rel_img_path=db_image.rel_img_path,
                coll_name=db_image.coll_name,
                fav=db_image.fav
            )
            wid.set_no_frame()
            wid.reload_thumbnails.connect(lambda: self.reload_thumbnails())
            Thumbnail.path_to_wid[wid.rel_img_path] = wid
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

    def grid_more(self, db_images: dict[str, list[LoadDbImagesItem]]):
        if db_images:
            for date, db_images_list in db_images.items():
                self.single_grid(date, db_images_list)
    
    def open_in_view(self, wid: Thumbnail):
        assert isinstance(wid, Thumbnail)
        from .win_image_view import WinImageView
        if len(self.selected_widgets) == 1:
            path_to_wid = Thumbnail.path_to_wid
            is_selection = False
        else:
            path_to_wid = {i.rel_img_path: i for i in self.selected_widgets}
            is_selection = True
        self.win_image_view = WinImageView(wid.rel_img_path, path_to_wid, is_selection)
        self.win_image_view.closed_.connect(lambda: gc.collect())
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
        return self.width() // (ThumbData.THUMB_W[Dynamic.thumb_size_ind])

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
                Thumbnail.path_to_wid[wid.rel_img_path] = wid
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
                main_folder_path = MainFolder.current.is_available()
                if main_folder_path:
                    img_path_list = [
                        MainUtils.get_img_path(main_folder_path, i.rel_img_path)
                        for i in self.selected_widgets
                    ]
                    self.info_win = WinInfo(img_path_list)
                    self.info_win.finished_.connect(self.open_info_win_delayed)
                else:
                    self.smb_win = WinWarn(Lang.no_connection, Lang.choose_coll_smb)
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

        self.menu_ = UMenu(event=a0)
        clicked_wid = self.get_wid_under_mouse(a0=a0)

        # клик по пустому пространству
        if not clicked_wid:
            self.clear_selected_widgets()
            reload = ScanerRestart(parent=self.menu_)
            reload.triggered.connect(lambda: self.restart_scaner.emit())
            self.menu_.addAction(reload)
            self.menu_.addSeparator()
            types_ = MenuTypes(parent=self.menu_)
            types_.reload_thumbnails.connect(lambda: self.reload_thumbnails_())
            types_.update_bottom_bar.connect(lambda: self.update_bottom_bar.emit())
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

            rel_img_path_list = [
                i.rel_img_path
                for i in self.selected_widgets
            ]

            cmd_ = lambda: self.open_in_view(wid=clicked_wid)
            view = OpenInView(self.menu_)
            view._clicked.connect(cmd_)
            self.menu_.addAction(view)


            info = WinInfoAction(self.menu_, self.window(), rel_img_path_list)
            self.menu_.addAction(info)

            self.fav_action = FavActionDb(self.menu_, clicked_wid.rel_img_path, clicked_wid.fav_value)
            self.fav_action.finished_.connect(clicked_wid.change_fav)
            self.menu_.addAction(self.fav_action)

            self.menu_.addSeparator()

            copy = CopyPath(self.menu_, self.window(), rel_img_path_list)
            self.menu_.addAction(copy)

            copy_name = CopyName(self.menu_, self.window(), rel_img_path_list)
            self.menu_.addAction(copy_name)

            reveal = Reveal(self.menu_, self.window(), rel_img_path_list)
            self.menu_.addAction(reveal)

            save_as = Save(self.menu_, self.window(), rel_img_path_list, True)
            save_as.save_files.connect(lambda data: self.save_files.emit(data))
            self.menu_.addAction(save_as)

            save = Save(self.menu_, self.window(), rel_img_path_list, False)
            save.save_files.connect(lambda data: self.save_files.emit(data))
            self.menu_.addAction(save)

            self.menu_.addSeparator()

            move_files = MoveFiles(self.menu_, rel_img_path_list)
            move_files.triggered.connect(lambda: self.move_files.emit(rel_img_path_list))
            self.menu_.addAction(move_files)

            rem = RemoveFiles(self.menu_, len(self.selected_widgets))
            rem.triggered.connect(lambda: self.remove_files.emit(rel_img_path_list))
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
            self.load_more_thumbnails()

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
            MainUtils.print_error()
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

        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, i.rel_img_path)
                for i in self.selected_widgets
            ]
        else:
            img_path_list = []

        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        img = os.path.join(Static.images_dir, "copy_files.png")
        img = QPixmap(img)
        self.drag.setPixmap(img)
        
        img_path_list = [
            QUrl.fromLocalFile(i)
            for i in img_path_list
            ]

        if img_path_list:
            self.mime_data.setUrls(img_path_list)

        self.drag.setMimeData(self.mime_data)
        self.drag.exec_(Qt.DropAction.CopyAction)

        if not img_path_list:
            self.win_smb = WinWarn(Lang.no_connection, Lang.choose_coll_smb)
            self.win_smb.adjustSize()
            self.win_smb.center_relative_parent(self.window())
            self.win_smb.show()

        return super().mouseMoveEvent(a0)
