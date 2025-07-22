import gc
import os

from PyQt5.QtCore import (QMimeData, QPoint, QRect, QSize, Qt, QTimer, QUrl,
                          pyqtSignal)
from PyQt5.QtGui import (QColor, QContextMenuEvent, QDrag, QKeyEvent,
                         QMouseEvent, QPalette, QPixmap, QResizeEvent)
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsDropShadowEffect, QGridLayout, QLabel,
                             QRubberBand, QWidget)

from cfg import Dynamic, JsonData, Static, ThumbData
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadDbImagesItem, LoadDbImagesTask
from system.utils import MainUtils, PixmapUtils, UThreadPool

from ._base_widgets import SvgBtn, UMenu, UVBoxLayout, VScrollArea
from .actions import (CopyName, CopyPath, FavActionDb, MenuTypes, MoveFiles,
                      OpenDefault, OpenInView, RemoveFiles, Save,
                      ScanerRestart, ShowInFinder, WinInfoAction)
from .win_info import WinInfo
from .win_warn import WinWarn


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

    def mouseReleaseEvent(self, ev):
        return super().mouseReleaseEvent(ev)
    
    def contextMenuEvent(self, ev):
        return super().contextMenuEvent(ev)
    
    def mouseDoubleClickEvent(self, a0):
        return super().mouseDoubleClickEvent(a0)


class TextAdvancedWid(QLabel):
    def __init__(self, wid: "Thumbnail"):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        first_row = self.short_text(wid.collection)
        text = "\n".join((first_row, wid.f_mod))
        self.setText(text)
        self.blue_color = "#6199E4"
        self.setStyleSheet(
            f"""
            font-size: {11}px;
            color: {self.blue_color};
            """
        )

    def short_text(self, text: str, max_row: int = 18):
        if len(text) >= max_row:
            return f"{text[:max_row - 10]}...{text[-7:]}"
        else:
            return text


class Thumbnail(QFrame):
    reload_thumbnails = pyqtSignal()
    select = pyqtSignal(str)

    img_frame_size = 0
    pixmap_size = 0
    thumb_w = 0
    thumb_h = 0
    corner = 0

    def __init__(self, pixmap: QPixmap, rel_img_path: str, coll_name: str, fav: int, f_mod: str):
        super().__init__()
        self.setStyleSheet(Static.border_transparent_style)

        self.img = pixmap
        self.rel_img_path = rel_img_path
        self.collection = coll_name
        self.fav_value = fav
        self.f_mod = f_mod

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
        self.v_layout.addWidget(self.text_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text_adv = TextAdvancedWid(self)
        self.v_layout.addWidget(self.text_adv, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setup()

    @classmethod
    def calculate_size(cls):
        ind = Dynamic.thumb_size_ind
        cls.pixmap_size = ThumbData.PIXMAP_SIZE[ind]
        cls.img_frame_size = Thumbnail.pixmap_size + ThumbData.OFFSET
        cls.thumb_w = ThumbData.THUMB_W[ind]
        cls.thumb_h = ThumbData.THUMB_H[ind]
        cls.corner = ThumbData.CORNER[ind]

    def setup(self):
        # инициация текста
        self.text_wid.set_text()

        self.setFixedSize(Thumbnail.thumb_w, Thumbnail.thumb_h)

        # рамка вокруг pixmap при выделении Thumb
        size_ = Thumbnail.pixmap_size + ThumbData.OFFSET
        self.img_wid.setFixedSize(size_, size_)
        self.img_wid.setPixmap(PixmapUtils.pixmap_scale(self.img, self.pixmap_size))

    def set_frame(self):
        style_ = f"""
            border-radius: {Thumbnail.corner}px;
            color: rgb(255, 255, 255);
            background: {Static.gray_color};
            border: {Static.border_transparent};
            padding-left: 2px;
            padding-right: 2px;
        """
        self.img_wid.setStyleSheet(style_)
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


class UpBtn(QFrame):
    scroll_to_top = pyqtSignal()
    icon = os.path.join(Static.INNER_IMAGES, "up.svg")
    icon_size = 44

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(self.icon_size, self.icon_size)
        style_ = f"""
            background: {Static.gray_color};
            border-radius: 22px;
        """
        self.setStyleSheet(style_)

        v_layout = UVBoxLayout()
        self.setLayout(v_layout)

        self.svg = SvgBtn(self.icon, self.icon_size)
        v_layout.addWidget(self.svg)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() == Qt.MouseButton.LeftButton:
            self.scroll_to_top.emit()
        return super().mouseReleaseEvent(a0)


class DateWid(QLabel):
    def __init__(self, parent: QWidget, blue_color: bool = True):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)      

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 190))
        self.setGraphicsEffect(shadow)
        

class Grid(VScrollArea):
    restart_scaner = pyqtSignal()
    remove_files = pyqtSignal(list)
    move_files = pyqtSignal(list)
    save_files = pyqtSignal(tuple)
    update_bottom_bar = pyqtSignal()
    img_view = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        self.wid_under_mouse: Thumbnail = None
        self.origin_pos = QPoint()
        self.selected_widgets: list[Thumbnail] = []
        self.cell_to_wid: dict[tuple, Thumbnail] = {}
        self.path_to_wid: dict[str, Thumbnail] = {}
        self.max_col: int = 0
        self.glob_row, self.glob_col = 0, 0
        self.is_first_load = True

        self.image_apps = {
            i: os.path.basename(i)
            for i in MainUtils.image_apps(JsonData.apps)
        }

        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.date_timer = QTimer(self)
        self.date_timer.setSingleShot(True)
        self.date_timer.timeout.connect(lambda: self.date_wid.hide())

        self.scroll_wid = QWidget()
        self.setWidget(self.scroll_wid)
        
        self.scroll_layout = UVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_wid.setLayout(self.scroll_layout)

        self.date_wid = DateWid(parent=self.viewport())
        self.date_wid.hide()

        self.up_btn = UpBtn(self.viewport())
        self.up_btn.scroll_to_top.connect(lambda: self.scroll_to_top())
        self.up_btn.hide()

        self.load_grid_wid()
        self.load_rubber()
        self.reload_thumbnails()

    def scroll_to_top(self):
        self.verticalScrollBar().setValue(0)

    def reload_thumbnails(self):
        Dynamic.grid_offset = 0
        cmd_ = lambda db_images: self.first_grid(db_images)
        self.load_db_images_task(cmd_)

    def load_more_thumbnails(self):
        Dynamic.grid_offset += Static.GRID_LIMIT
        cmd_ = lambda db_images: self.grid_more(db_images)
        self.load_db_images_task(cmd_)

    def load_db_images_task(self, on_finish_cmd: callable):
        self.task_ = LoadDbImagesTask()
        self.task_.signals_.finished_.connect(on_finish_cmd)
        UThreadPool.start(self.task_)

    def load_rubber(self):
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.viewport())
        
    def load_grid_wid(self):
        self.grid_wid = QWidget()
        self.scroll_layout.addWidget(self.grid_wid)
        self.grid_lay = QGridLayout()
        self.grid_wid.setLayout(self.grid_lay)
                                
    def first_grid(self, db_images: dict[str, list[LoadDbImagesItem]]):
        for i in (self.grid_wid, self.rubberBand):
            i.deleteLater()
        
        self.clear_thumb_data()
        self.clear_cell_data()
        self.clear_selected_widgets()
        self.load_grid_wid()
        self.load_rubber()
        Thumbnail.calculate_size()

        self.grid_wid.hide()
        for date, db_images_list in db_images.items():
            self.single_grid(db_images_list)
        self.rearrange()
        self.grid_wid.show()
                        
    def add_thumb_data(self, wid: Thumbnail):
        self.path_to_wid[wid.rel_img_path] = wid
        self.cell_to_wid[self.glob_row, self.glob_col] = wid
        wid.row, wid.col = self.glob_row, self.glob_col        

    def single_grid(self, db_images: list[LoadDbImagesItem]):
        for db_image in db_images:
            wid = Thumbnail(
                pixmap=db_image.pixmap,
                rel_img_path=db_image.rel_img_path,
                coll_name=db_image.coll_name,
                fav=db_image.fav,
                f_mod=db_image.f_mod
            )
            wid.set_no_frame()
            wid.reload_thumbnails.connect(lambda: self.reload_thumbnails())
            self.add_thumb_data(wid)
            self.grid_lay.addWidget(wid, 0, 0)

    def grid_more(self, db_images: dict[str, list[LoadDbImagesItem]]):
        for date, db_images_list in db_images.items():
            self.single_grid(db_images_list)
        self.rearrange()

    def select_viewed_image(self, path: str):
        wid = self.path_to_wid.get(path)
        if wid:
            self.clear_selected_widgets()
            self.add_and_select_widget(wid)
    
    def clear_thumb_data(self):
        """
        Очищает:
        - cell to wid
        - path to wid
        """
        for i in (self.cell_to_wid, self.path_to_wid):
            i.clear()
            
    def clear_cell_data(self):
        """
        Сбрасывет:
        - max col
        - glob row
        - glob col
        """
        self.max_col = self.width() // (ThumbData.THUMB_W[Dynamic.thumb_size_ind])
        self.glob_row, self.glob_col = 0, 0

    def resize_thumbnails(self):
        """
        - Высчитывает новые размеры Thumbnail
        - Меняет размеры виджетов Thumbnail в текущей сетке
        - Переупорядочивает сетку в соотетствии с новыми размерами
        """
        Thumbnail.calculate_size()
        for cell, wid in self.cell_to_wid.items():
            wid.setup()
        self.rearrange()

    def rearrange(self):
        """
        Переупорядочивает все элементы сетки заново:
        - Очищает предыдущие данные по сетке
        - Расставляет виджеты Thumbnail
        """
        self.clear_thumb_data()
        self.clear_cell_data()
        thumbnails = self.grid_wid.findChildren(Thumbnail)
        if not thumbnails:
            return
        prev_f_mod = thumbnails[0].f_mod
        for wid in thumbnails:
            if wid.f_mod != prev_f_mod:
                self.glob_col = 0
                self.glob_row += 1

            self.add_thumb_data(wid)
            self.grid_lay.addWidget(wid, self.glob_row, self.glob_col)

            self.glob_col += 1
            if self.glob_col >= self.max_col:
                self.glob_col = 0
                self.glob_row += 1

            prev_f_mod = wid.f_mod

        if self.glob_col != 0:
            self.glob_col = 0
            self.glob_row += 1

    def get_wid_under_mouse(self, a0: QMouseEvent) -> None | Thumbnail:
        wid = QApplication.widgetAt(a0.globalPos())
        if isinstance(wid, (ImgWid, TextWid)):
            return wid.parent()
        else:
            return None
        
    def clear_selected_widgets(self):
        """
        - Убирает стиль выделенных виджетов
        - Очищает selected widgets
        """
        for i in self.selected_widgets:
            i.set_no_frame()
        self.selected_widgets.clear()

    def add_and_select_widget(self, wid: Thumbnail):
        """
        - Добавляет переданный виджет в selected widgets
        - Задает стиль переданному виджету
        """
        if isinstance(wid, Thumbnail):
            self.selected_widgets.append(wid)
            wid.set_frame()

    def open_info_win_delayed(self):
        self.win_info.adjustSize()
        self.win_info.center_relative_parent(self.window())
        self.win_info.show()

    def open_default_cmd(self, rel_img_path_list: list[str]):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            for i in rel_img_path_list:
                abs_path = MainUtils.get_abs_path(main_folder_path, i)
                MainUtils.open_in_app(abs_path)

    def open_in_app_cmd(self, rel_img_path_list: list[str], app_path: str):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            for i in rel_img_path_list:
                abs_path = MainUtils.get_abs_path(main_folder_path, i)
                MainUtils.open_in_app(abs_path, app_path)
            
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
                        MainUtils.get_abs_path(main_folder_path, i.rel_img_path)
                        for i in self.selected_widgets
                    ]
                    self.win_info = WinInfo(img_path_list)
                    self.win_info.finished_.connect(self.open_info_win_delayed)
                else:
                    self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
                    self.win_warn.adjustSize()
                    self.win_warn.center_relative_parent(self.window())
                    self.win_warn.show()

        elif a0.modifiers() == command and a0.key() == Qt.Key.Key_A:
            for i in self.cell_to_wid.values():
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
                        self.max_col - 1
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
        self.resize_timer.stop()
        self.resize_timer.start(10)

        self.up_btn.move(
            self.viewport().width() - self.up_btn.width() - 20,
            self.viewport().height() - self.up_btn.height() - 20
        )        

        self.date_wid.move(
            (self.viewport().width() - self.date_wid.width()) // 2,
            5
        )

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

            open_menu = UMenu(a0)
            open_menu.setTitle(f"{Lang.open_in} ({len(rel_img_path_list)})")
            self.menu_.addMenu(open_menu)

            for app_path, basename in self.image_apps.items():
                act = QAction(parent=open_menu, text=basename)
                cmd = lambda e, app_path=app_path: self.open_in_app_cmd(rel_img_path_list, app_path)
                act.triggered.connect(cmd)
                open_menu.addAction(act)

            # open_default = OpenDefault(self.menu_, rel_img_path_list)
            # open_default.triggered.connect(lambda: self.open_default_cmd(rel_img_path_list))
            # self.menu_.addAction(open_default)

            self.menu_.addSeparator()

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

            reveal = ShowInFinder(self.menu_, self.window(), rel_img_path_list)
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

        self.menu_.show_()

    def checkScrollValue(self, value):
        if value > 0:            
            self.up_btn.show()
            
            point = QPoint(50, 50)
            mapped_pos = self.scroll_wid.mapFrom(self.viewport(), point)
            wid: Thumbnail = self.scroll_wid.childAt(mapped_pos).parent()
            if isinstance(wid, Thumbnail):
                self.date_wid.setText(wid.f_mod)
                self.date_wid.adjustSize()
                
                self.date_wid.move(
                    (self.viewport().width() - self.date_wid.width()) // 2,
                    5
                )
                if self.date_wid.isHidden():
                    palete = QApplication.palette()
                    color = QPalette.windowText(palete).color().name()
                
                    bg_style_data = {
                        "#000000": "rgba(220, 220, 220, 1)",
                        "#ffffff": "rgba(80, 80, 80, 1)",
                    }

                    self.date_wid.setStyleSheet(f"""
                        QLabel {{
                            background: {bg_style_data.get(color)};
                            font-weight: bold;
                            font-size: 20pt;
                            border-radius: 10px;
                            padding: 5px;
                        }}
                    """)

                    self.date_wid.show()
                    self.date_timer.stop()
                    self.date_timer.start(3000)
     
        elif value == 0:
            self.date_wid.hide()
            self.up_btn.hide()

        if value == self.verticalScrollBar().maximum():
            self.load_more_thumbnails()

    def mouseDoubleClickEvent(self, a0):
        if self.wid_under_mouse:
            self.clear_selected_widgets()
            self.add_and_select_widget(self.wid_under_mouse)
            self.img_view.emit()

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
                MainUtils.get_abs_path(main_folder_path, i.rel_img_path)
                for i in self.selected_widgets
            ]
        else:
            img_path_list = []

        self.drag = QDrag(self)
        self.mime_data = QMimeData()
        img = os.path.join(Static.INNER_IMAGES, "copy_files.png")
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
            self.win_smb = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_smb.adjustSize()
            self.win_smb.center_relative_parent(self.window())
            self.win_smb.show()

        return super().mouseMoveEvent(a0)
