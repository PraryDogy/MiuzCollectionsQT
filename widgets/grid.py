import os

from PyQt6.QtCore import (QMimeData, QPoint, QRect, QSize, Qt, QTimer, QUrl,
                          pyqtSignal)
from PyQt6.QtGui import (QAction, QContextMenuEvent, QCursor, QDrag,
                         QFontMetrics, QKeyEvent, QMouseEvent, QPixmap,
                         QResizeEvent, QColor)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QFrame, QGraphicsOpacityEffect,
                             QGridLayout, QLabel, QRubberBand, QVBoxLayout,
                             QWidget)

from cfg import Dynamic, JsonData, Static
from system.items import DataItem, SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import SharedUtils
from system.tasks import DbImagesLoader, DbImagesLoaderItem, UThreadPool
from system.utils import Utils

from ._base_widgets import UMenu, USubMenu, VScrollArea
from .actions import (CollageAction, CopyFiles, CopyPath, OpenInView,
                      PasteFiles, RemoveFiles, RevealInFinder, Save,
                      ScanerRestart, SetFav, ShowInFolder, UpdateThumbAction,
                      WinInfoAction)


class ThumbBaseLabel(QLabel):
    FONT_SIZE = 11
    BLUE_TEXT_WID_COLOR = "#6199E4"

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def get_shorten_text(self, text: str, parent_width: int, offset = 5):
        metrics = QFontMetrics(self.font())
        text = metrics.elidedText(
            text,
            Qt.TextElideMode.ElideMiddle,
            parent_width - offset
        )
        return text


class ThumbImgWidget(ThumbBaseLabel):
    BORDER_RADIUS = 10
    RGBA_GRAY = "rgba(128, 128, 128, 0.5)"
    PADDING = 0

    def __init__(self):
        super().__init__()
        self.set_no_frame_style()

    def set_framed_style(self):
        self.setStyleSheet(
            f"""
                background: {self.RGBA_GRAY};
                border-radius: {self.BORDER_RADIUS}px;
                padding: {self.PADDING}px;
            """
        )
    
    def set_no_frame_style(self):
        self.setStyleSheet(
            f"""
                background: transparent;
                border-radius: {self.BORDER_RADIUS}px;
                padding: {self.PADDING}px;
            """
        )


class WhiteTextWid(ThumbBaseLabel):
    BORDER_RADIUS = 5

    def __init__(self, data_item: DataItem):
        super().__init__()
        self.data_item = data_item
        self.set_no_frame_style()

    def set_text(self, parent_width: int):
        text = self.get_shorten_text(self.data_item.filename, parent_width)
        self.setText(text)

    def set_framed_style(self):
        self.setStyleSheet(
            f"""
                background: palette(highlight);
                font-size: {self.FONT_SIZE}px;
                border-radius: {self.BORDER_RADIUS}px;
                padding: 2px;
            """
        )

    def set_no_frame_style(self):
        self.setStyleSheet(
            f"""
                background: transparent;
                font-size: {self.FONT_SIZE}px;
                border-radius: {self.BORDER_RADIUS}px;
                padding: 2px;
            """
        )
    
    
class BlueTextWid(ThumbBaseLabel):
    def __init__(self, data_item: DataItem):
        super().__init__()
        self.data_item = data_item
        self.set_style()

    def set_text(self, parent_width: int):
        root = self.data_item.rel_path.strip(os.sep).split(os.sep)
        if len(root) == 1:
            root = os.path.basename(Mf.current_mf.mf_alias)
        else:
            root = root[0]

        root = self.get_shorten_text(root, parent_width)
        day_month_year = self.data_item.day_month_year
        self.setText("\n".join((root, day_month_year)))

    def set_style(self):
        self.setStyleSheet(
            f"""
                font-size: {self.FONT_SIZE}px;
                color: {self.BLUE_TEXT_WID_COLOR};
            """
        )


class Thumb(QFrame):
    sym_star = "\U00002605"
    wid_width = 0
    wid_height = 0
    img_wid_size = 0
    img_wid_height = 0

    def __init__(self, data_item: DataItem):
        super().__init__()
        self.row, self.col = 0, 0
        self.data_item = data_item
        if self.data_item.fav:
            self.data_item.filename = f"{self.sym_star} {self.data_item.filename}"

        # --- Layout ---
        self.v_lay = QVBoxLayout(self)
        self.v_lay.setContentsMargins(0, 0, 0, 0)
        self.v_lay.setSpacing(3)
        self.v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Виджеты ---
        self.img_wid = ThumbImgWidget()
        self.v_lay.addWidget(self.img_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.white_text_wid = WhiteTextWid(self.data_item)
        self.v_lay.addWidget(self.white_text_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.blue_text_wid = BlueTextWid(self.data_item)
        self.v_lay.addWidget(self.blue_text_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        location = (
            f"{Lng.location[JsonData.lng_index]}: "
            f"{Mf.current_mf.mf_alias}{self.data_item.rel_path}"
        )
        modified = (
            f"{Lng.modified[JsonData.lng_index]}: "
            f"{self.data_item.day_month_year}"
        )
        self.setToolTip("\n".join([location, modified, ]))

        self.set_text_and_size()

    @classmethod
    def calculate_size(cls):
        ind = Dynamic.current_pixmap_size_index

        Thumb.img_wid_size = Static.thumb_widget_pixmap_size[ind] + Static.img_wid_border
        Thumb.wid_width = Thumb.img_wid_size + Static.thumb_widget_extra_w

    def set_pixmap_with_actual_size(self):
        qimage = self.data_item.qimages[Dynamic.current_pixmap_size_index]
        pixmap = QPixmap.fromImage(qimage)
        self.img_wid.clear()
        self.img_wid.setPixmap(pixmap)

    def set_text_and_size(self):
        if self.width() == Thumb.wid_width:
            return

        self.setFixedWidth(Thumb.wid_width)
        self.img_wid.setFixedSize(Thumb.img_wid_size, Thumb.img_wid_size)

        self.white_text_wid.set_text(Thumb.wid_width)
        self.blue_text_wid.set_text(Thumb.wid_width)
        self.set_pixmap_with_actual_size()

    def set_frame(self):
        self.img_wid.set_framed_style()
        self.white_text_wid.set_framed_style()

    def set_no_frame(self):
        self.img_wid.set_no_frame_style()
        self.white_text_wid.set_no_frame_style()

    def set_transparent_frame(self, value: float):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(value)
        self.setGraphicsEffect(effect)

    def set_fav(self, value: int):
        if value == 0:
            self.data_item.fav = 0
            self.data_item.filename = os.path.basename(self.data_item.rel_path)
        else:
            self.data_item.fav = 1
            self.data_item.filename = (
                f"{self.sym_star} "
                f"{os.path.basename(self.data_item.rel_path)}"
            )

        self.white_text_wid.data_item.filename = self.data_item.filename
        self.white_text_wid.set_text()


class UpBtn(QSvgWidget):
    scroll_to_top = pyqtSignal()
    icon_path = os.path.join(Static.common_icons, "scroll_up.svg")
    icon_size = 45

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(self.icon_size, self.icon_size)
        self.load(self.icon_path)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.scroll_to_top.emit()
        super().mouseReleaseEvent(ev)


class Grid(VScrollArea):
    load_st_grid = pyqtSignal()
    restart_scaner = pyqtSignal()
    remove_files = pyqtSignal(list)
    save_files = pyqtSignal(list)
    path_bar_update = pyqtSignal(str)
    open_img_view = pyqtSignal()
    open_info_win = pyqtSignal(list)
    copy_path = pyqtSignal(list)
    reveal_in_finder = pyqtSignal(list)
    set_fav = pyqtSignal(tuple)
    open_in_app = pyqtSignal(tuple)
    paste_files = pyqtSignal()
    set_files_to_copy = pyqtSignal(list)
    setup_mf = pyqtSignal(SettingsItem)
    update_thumb = pyqtSignal(list)
    show_in_app = pyqtSignal(str)
    finished_ = pyqtSignal()
    collage = pyqtSignal(list)

    grid_spacing = 7
    resize_ms = 10
    copy_files_path = os.path.join(Static.common_icons, "copy_files.svg")

    def __init__(self):
        super().__init__()
        _copy_files_icon = QPixmap(self.copy_files_path)
        self.copy_files_icon = Utils.qiconed_resize(_copy_files_icon, 80)

        # --- Состояние и данные ---
        self.wid_under_mouse: Thumb = None
        self.origin_pos = QPoint()
        self.selected_widgets: list[Thumb] = []
        self.cell_to_wid: dict[tuple, Thumb] = {}
        self.url_to_wid: dict[str, Thumb] = {}
        self.files_to_copy = set()

        self.image_apps = {
            i: os.path.basename(i)
            for i in SharedUtils.get_apps(Static.apps)
        }

        # --- Таймеры ---
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.date_timer = QTimer(self)
        self.date_timer.setSingleShot(True)

        # --- Вкладка прокрутки ---
        self.scroll_wid = QWidget()
        self.setWidget(self.scroll_wid)
        self.scroll_layout = QVBoxLayout(self.scroll_wid)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.up_btn = UpBtn(self.viewport())
        self.up_btn.scroll_to_top.connect(lambda: self.verticalScrollBar().setValue(0))
        self.up_btn.hide()

        self.grid_wid = QWidget()
        self.scroll_layout.addWidget(self.grid_wid)
        self.grid_lay = QGridLayout(self.grid_wid)
        self.grid_lay.setSpacing(self.grid_spacing)
        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())

        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

    def select_by_url(self, path: str):
        if path in self.url_to_wid:
            wid = self.url_to_wid.get(path)
            self.clear_selected_widgets()
            self.wid_to_selected_widgets(wid)

    def resize_thumbnails(self):
        Thumb.calculate_size()
        for _, wid in self.cell_to_wid.items():
            wid.set_text_and_size()
            if wid in self.selected_widgets:
                wid.set_frame()
        self.rearrange()

    def get_max_columns(self):
        try:
            # теперь виджет правильной ширины
            # но теперь есть лишние спейсинги справа и слева в концах сетки
            # что мы учитываем в total_w
            thumb_w = Thumb.wid_width + self.grid_spacing
            total_w = self.viewport().width() - (self.grid_spacing * 2)
            return total_w // thumb_w
        except ZeroDivisionError:
            return 1

    def rearrange(self):
        self.grid_wid.hide()
        # max_col = self.width() // Thumb.wid_width
        max_col = self.get_max_columns()
        self.cell_to_wid.clear()
        for x, thumb in enumerate(self.url_to_wid.values()):
            row, col = divmod(x, max_col)
            self.cell_to_wid[row, col] = thumb
            thumb.row, thumb.col = row, col
            self.grid_lay.addWidget(thumb, row, col)
        self.grid_wid.show()

    def get_clicked_widget(self, a0: QMouseEvent) -> None | Thumb:
        global_pos = QCursor.pos() 
        wid = QApplication.widgetAt(global_pos)
        if isinstance(wid, (ThumbImgWidget, WhiteTextWid)):
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

    def wid_to_selected_widgets(self, wid: Thumb):
        if isinstance(wid, Thumb):
            self.selected_widgets.append(wid)
            wid.set_frame()
                
    def set_thumb_fav(self, rel_path: str, value: int):
        if rel_path in self.url_to_wid:
            wid = self.url_to_wid.get(rel_path)
            wid.set_fav(value)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        def remove_files():
            self.remove_files.emit(
                [i.data_item.rel_path for i in self.selected_widgets]
            )

        def open_info():
            """Открывает окно информации для выбранных виджетов."""
            if self.selected_widgets:
                rel_paths = [self.wid_under_mouse.data_item.rel_path, ]
                self.open_info_win.emit(rel_paths)

        def select_all():
            """Выделяет все виджеты в сетке."""
            for wid in self.cell_to_wid.values():
                wid.set_frame()
                self.selected_widgets.append(wid)

        def open_last_selected():
            """Открывает просмотр последнего выбранного виджета."""
            if self.selected_widgets:
                self.open_img_view.emit()

        def navigate(offset: tuple[int, int]):
            """Перемещает выделение в сетке по заданному смещению."""
            # начальный виджет
            if not self.selected_widgets:
                self.wid_under_mouse = self.cell_to_wid.get((0, 0))
            else:
                self.wid_under_mouse = self.selected_widgets[-1]

            if not self.wid_under_mouse:
                return

            row, col = self.wid_under_mouse.row + offset[0], self.wid_under_mouse.col + offset[1]
            next_wid = self.cell_to_wid.get((row, col))

            # обработка перехода за пределы строки
            if next_wid is None:
                keys = list(self.cell_to_wid.keys())
                curr_idx = keys.index((self.wid_under_mouse.row, self.wid_under_mouse.col))

                if event.key() == Qt.Key.Key_Right:
                    row += 1
                    col = 0
                elif event.key() == Qt.Key.Key_Left:
                    if curr_idx > 0:
                        row, col = keys[curr_idx - 1]
                    else:
                        # достигли начала сетки, остаёмся на месте
                        row, col = self.wid_under_mouse.row, self.wid_under_mouse.col

                next_wid = self.cell_to_wid.get((row, col))

            if next_wid:
                self.clear_selected_widgets()
                self.wid_to_selected_widgets(next_wid)
                self.ensureWidgetVisible(next_wid)
                self.wid_under_mouse = next_wid

        # --- Основная логика ---
        CTRL = Qt.KeyboardModifier.ControlModifier
        KEY_NAVI = {
            Qt.Key.Key_Left: (0, -1),
            Qt.Key.Key_Right: (0, 1),
            Qt.Key.Key_Up: (-1, 0),
            Qt.Key.Key_Down: (1, 0)
        }

        if event.modifiers() == CTRL and event.key() == Qt.Key.Key_Backspace:
            if self.selected_widgets:
                remove_files()
        if event.modifiers() == CTRL and event.key() == Qt.Key.Key_I:
            open_info()
        elif event.modifiers() == CTRL and event.key() == Qt.Key.Key_A:
            select_all()
        elif event.modifiers() == CTRL and event.key() == Qt.Key.Key_C:
            self.set_files_to_copy.emit(
                [i.data_item.rel_path for i in self.selected_widgets]
            )
        elif event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
            if not event.isAutoRepeat():
                open_last_selected()
        elif event.key() in KEY_NAVI:
            navigate(KEY_NAVI[event.key()])

        super().keyPressEvent(event)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0.button() != Qt.MouseButton.LeftButton:
            return

        def handle_rubber_band_selection(rect: QRect):
            ctrl = a0.modifiers() == Qt.KeyboardModifier.ControlModifier

            for wid in self.cell_to_wid.values():
                widgets = wid.findChildren((WhiteTextWid, ThumbImgWidget))
                intersects = any(
                    rect.intersects(QRect(child.mapTo(self, QPoint(0, 0)), child.size()))
                    for child in widgets
                )

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

        def handle_shift_click():
            coords = list(self.cell_to_wid)
            start_pos = (self.selected_widgets[-1].row, self.selected_widgets[-1].col)
            target_pos = (self.wid_under_mouse.row, self.wid_under_mouse.col)

            if coords.index(target_pos) > coords.index(start_pos):
                start = coords.index(start_pos)
                end = coords.index(target_pos)
                slice_coords = coords[start : end + 1]
            else:
                start = coords.index(target_pos)
                end = coords.index(start_pos)
                slice_coords = coords[start : end + 1]

            for c in slice_coords:
                wid = self.cell_to_wid.get(c)
                if wid not in self.selected_widgets:
                    self.wid_to_selected_widgets(wid)

        def handle_control_click():
            if self.wid_under_mouse in self.selected_widgets:
                self.selected_widgets.remove(self.wid_under_mouse)
                self.wid_under_mouse.set_no_frame()
            else:
                self.wid_to_selected_widgets(self.wid_under_mouse)

        # --- Основная логика ---
        if self.rubberBand.isVisible():
            rect = QRect(self.origin_pos, a0.pos()).normalized()
            self.rubberBand.hide()
            handle_rubber_band_selection(rect)
            return

        self.wid_under_mouse = self.get_clicked_widget(a0)

        if not self.wid_under_mouse:
            self.clear_selected_widgets()
            return


        modifiers = a0.modifiers()
        if modifiers == Qt.KeyboardModifier.ShiftModifier and self.selected_widgets:
            handle_shift_click()
        elif modifiers == Qt.KeyboardModifier.ControlModifier:
            handle_control_click()
        elif not hasattr(self, "double_click"):
            self.clear_selected_widgets()
            self.wid_to_selected_widgets(self.wid_under_mouse)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.resize_timer.stop()
        self.resize_timer.start(self.resize_ms)

        self.up_btn.move(
            self.viewport().width() - self.up_btn.width() - 20,
            self.viewport().height() - self.up_btn.height() - 20
        )
        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        """Создаёт контекстное меню для пустой области или выбранных виджетов."""
        self.menu_ = UMenu(event=a0)
        clicked_wid = self.get_clicked_widget(a0)

        def menu_empty():
            self.clear_selected_widgets()

            # это костыль, может сломаться если мы переименуем buffer в main_win
            if self.files_to_copy:
                self.menu_.addSeparator()
                paste = PasteFiles(self.menu_)
                paste.triggered.connect(
                    lambda: self.paste_files.emit()
                )
                self.menu_.addAction(paste)
                self.menu_.addSeparator()

            update_grid = QAction(Lng.update_grid[JsonData.lng_index], self.menu_)
            update_grid.triggered.connect(
                lambda: self.load_st_grid.emit()
            )
            self.menu_.addAction(update_grid)

            reload = ScanerRestart(parent=self.menu_)
            reload.triggered.connect(
                lambda: self.restart_scaner.emit()
            )
            self.menu_.addAction(reload)

            self.menu_.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[JsonData.lng_index], self.menu_)
            reveal.triggered.connect(
                lambda: self.reveal_in_finder.emit([Dynamic.current_dir, ])
            )
            self.menu_.addAction(reveal)

        def menu_widget(clicked: Thumb):
            if not self.selected_widgets:
                self.wid_to_selected_widgets(clicked)
            elif clicked not in self.selected_widgets:
                self.clear_selected_widgets()
                self.wid_to_selected_widgets(clicked)

            data_items = [w.data_item for w in self.selected_widgets]
            rel_paths = [di.rel_path for di in data_items]

            # просмотр
            act = OpenInView(rel_paths, self.menu_)
            act.triggered.connect(
                lambda: self.open_img_view.emit()
            )
            self.menu_.addAction(act)

            # открыть в приложении
            if len(rel_paths) == 1:
                open_menu = USubMenu(
                    f"{Lng.open_in[JsonData.lng_index]}",
                    self.menu_
                )

                act = QAction(Lng.open_default[JsonData.lng_index], open_menu)
                act.triggered.connect(
                    lambda: self.open_in_app.emit((rel_paths, None))
                )
                open_menu.addAction(act)
                open_menu.addSeparator()

                for app_path, basename in self.image_apps.items():
                    act = QAction(basename, open_menu)
                    act.triggered.connect(
                        lambda _, x=app_path: self.open_in_app.emit((rel_paths, x))
                    )
                    open_menu.addAction(act)

                self.menu_.addMenu(open_menu)

                self.menu_.addSeparator()

                fav = SetFav(self.menu_, clicked.data_item.fav)
                fav.triggered.connect(
                    lambda: self.set_fav.emit((clicked.data_item.rel_path, not clicked.data_item.fav))
                )
                self.menu_.addAction(fav)

                show_in_app = ShowInFolder(self.menu_)
                show_in_app.triggered.connect(
                    lambda: self.show_in_app.emit(clicked.data_item.rel_path)
                )
                self.menu_.addAction(show_in_app)

                # инфо
                act = WinInfoAction(self.menu_)
                act.triggered.connect(
                    lambda: self.open_info_win.emit(rel_paths)
                )
                self.menu_.addAction(act)

            self.menu_.addSeparator()

            act = RevealInFinder(self.menu_, len(rel_paths))
            act.triggered.connect(
                lambda: self.reveal_in_finder.emit(rel_paths)
            )
            self.menu_.addAction(act)

            if len(rel_paths) > 1:
                collage = CollageAction(self.menu_)
                collage.triggered.connect(
                    lambda: self.collage.emit(data_items)
                )
                self.menu_.addAction(collage)

            update_thumb = UpdateThumbAction(self.menu_, rel_paths)
            update_thumb.triggered.connect(
                lambda: self.update_thumb.emit(rel_paths)
            )
            self.menu_.addAction(update_thumb)
            
            self.menu_.addSeparator()

            act = CopyFiles(self.menu_, rel_paths)
            act.triggered.connect(
                lambda: self.set_files_to_copy.emit(rel_paths)
            )
            self.menu_.addAction(act)

            act = CopyPath(self.menu_, len(rel_paths))
            act.triggered.connect(
                lambda: self.copy_path.emit(rel_paths)
            )
            self.menu_.addAction(act)

            self.menu_.addSeparator()

            act = Save(self.menu_, len(rel_paths))
            act.triggered.connect(
                lambda: self.save_files.emit(rel_paths)
            )
            self.menu_.addAction(act)

            act = RemoveFiles(self.menu_, len(self.selected_widgets))
            act.triggered.connect(
                lambda: self.remove_files.emit(rel_paths)
            )
            self.menu_.addAction(act)

            self.menu_.addSeparator()

        if not clicked_wid:
            menu_empty()
        else:
            menu_widget(clicked_wid)

        self.menu_.show_menu()

    def checkScrollValue(self, value: int):
        self.up_btn.setVisible(value > 0)

    def mouseDoubleClickEvent(self, a0):

        def fin(wid: Thumb):
            self.wid_to_selected_widgets(wid)

        if self.wid_under_mouse:
            self.open_img_view.emit()
            QTimer.singleShot(150, lambda w=self.wid_under_mouse: fin(w))

    def mousePressEvent(self, a0):
        self.origin_pos = a0.pos()
        self.wid_under_mouse = self.get_clicked_widget(a0)
        if self.wid_under_mouse:
            self.path_bar_update.emit(self.wid_under_mouse.data_item.rel_path)
        else:
            self.path_bar_update.emit(Dynamic.current_dir)
        return super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0):
        try:
            distance = (a0.pos() - self.origin_pos).manhattanLength()
        except AttributeError:
            Utils.print_error()
            return

        if distance < QApplication.startDragDistance():
            return

        def start_rubber_band():
            self.rubberBand.setGeometry(QRect(self.origin_pos, QSize()))
            self.rubberBand.show()

        def update_rubber_band():
            rect = QRect(self.origin_pos, a0.pos()).normalized()
            self.rubberBand.setGeometry(rect)

        def start_drag():
            # если виджет под курсором не выделен — выделяем его
            if self.wid_under_mouse and self.wid_under_mouse not in self.selected_widgets:
                self.clear_selected_widgets()
                self.wid_to_selected_widgets(self.wid_under_mouse)
                QTimer.singleShot(100, self.wid_under_mouse.set_frame)

            # собираем пути выбранных изображений
            paths = []
            avaiable_mf_path = Mf.current_mf.get_avaiable_mf_path()
            if avaiable_mf_path:
                Mf.current_mf.set_mf_current_path(avaiable_mf_path)
                paths = [
                    Utils.get_abs_any_path(Mf.current_mf.mf_current_path, wid.data_item.rel_path)
                    for wid in self.selected_widgets
                ]

            # создаём объект перетаскивания
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)

            drag.setPixmap(self.copy_files_icon)

            # назначаем urls
            mime_data.setUrls([QUrl.fromLocalFile(p) for p in paths])

            if not paths:
                drag.exec(Qt.DropAction.IgnoreAction)
            else:
                drag.exec(Qt.DropAction.CopyAction)

        # --- Основная логика ---
        if self.wid_under_mouse is None and not self.rubberBand.isVisible():
            start_rubber_band()
        elif self.rubberBand.isVisible():
            update_rubber_band()
        else:
            start_drag()

        return super().mouseMoveEvent(a0)


class GridStandart(Grid):
    upload_files = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.load_db_images_task()

    def load_more_thumbnails(self):
        Dynamic.loaded_thumbs += Static.thumbs_load_limit
        self.load_db_images_task()

    def load_db_images_task(self):
        self.task_ = DbImagesLoader()
        self.task_.sigs.finished_.connect(self.create_thumbnails)
        UThreadPool.start(self.task_)

    def create_thumbnails(self, db_images: list[DbImagesLoaderItem]):
        Thumb.calculate_size()
        for image_item in db_images:
            data_item = DataItem(
                qimages=image_item.qimages,
                rel_path=image_item.rel_img_path,
                fav=image_item.fav,
                month_year=image_item.month_year,
                day_month_year=image_item.day_month_year,
                filename=os.path.basename(image_item.rel_img_path)
            )
            thumbnail = Thumb(data_item)
            thumbnail.set_no_frame()
            self.url_to_wid[thumbnail.data_item.rel_path] = thumbnail
        if not self.url_to_wid:
            self.grid_wid.hide()
            self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(Lng.no_photo[JsonData.lng_index])
            self.scroll_layout.addWidget(lbl)
        else:
            self.rearrange()
        self.finished_.emit()

    def checkScrollValue(self, value: int):
        super().checkScrollValue(value)
        if value == self.verticalScrollBar().maximum():
            self.load_more_thumbnails()

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):

        if not a0.mimeData().hasUrls() or a0.source() is not None:
            return
        
        elif Dynamic.search_widget_text:
            return

        paths: list[str] = [
            i.toLocalFile().rstrip(os.sep)
            for i in a0.mimeData().urls()
            if os.path.isfile(i.toLocalFile())
        ]

        if paths:
            self.upload_files.emit(paths)
        return super().dropEvent(a0)