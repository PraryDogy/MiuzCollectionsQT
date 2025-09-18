import gc
import os
import subprocess

from PyQt5.QtCore import (QMimeData, QPoint, QRect, QSize, Qt, QTimer, QUrl,
                          pyqtSignal)
from PyQt5.QtGui import (QColor, QContextMenuEvent, QDrag, QKeyEvent,
                         QMouseEvent, QPalette, QPixmap, QResizeEvent)
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
                             QGridLayout, QLabel, QPushButton, QRubberBand,
                             QWidget)

from cfg import Cfg, Dynamic, Static, ThumbData
from system.lang import Lng
from system.main_folder import MainFolder
from system.shared_utils import SharedUtils
from system.tasks import DbImagesLoader, UThreadPool
from system.utils import MainUtils

from ._base_widgets import (ClipBoardItem, NotifyWid, SettingsItem, SvgBtn,
                            UMenu, USubMenu, UVBoxLayout, VScrollArea)
from .actions import (CopyFiles, CopyName, CopyPath, CutFiles, OpenInView,
                      PasteFiles, RemoveFiles, RevealInFinder, Save, SaveAs,
                      ScanerRestart, SetFav, WinInfoAction)


class FilenameWid(QLabel):
    """
    QLabel для отображения текста с ограничением по длине и разбиением на строки.

    Атрибуты:
        name (str): основной текст.
    """

    def __init__(self, parent: QWidget, name: str, coll: str):
        super().__init__(parent)
        self.name = name

    def set_text(self) -> None:
        """
        Устанавливает текст QLabel с учетом максимальной длины строки.
        Делит длинный текст на две строки и сокращает, если необходимо.
        """
        name: str = self.name
        ind = Dynamic.thumb_size_index
        max_row = ThumbData.MAX_ROW[ind]
        lines: list[str] = []

        if len(name) > max_row:
            first_line = name[:max_row]
            second_line = name[max_row:]

            if len(second_line) > max_row:
                second_line = self.short_text(second_line, max_row)

            lines.extend([first_line, second_line])
        else:
            lines.append(name)

        self.setText("\n".join(lines))

    def short_text(self, text: str, max_row: int) -> str:
        """
        Сокращает текст, оставляя начало и конец, вставляя "..." посередине.
        """
        return f"{text[:max_row - 10]}...{text[-7:]}"

    # --- Передача событий родительскому QLabel ---
    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)

    def contextMenuEvent(self, ev):
        super().contextMenuEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(ev)
    
    
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


class BelowTextWid(QLabel):
    """
    QLabel для отображения расширенной информации о миниатюре.

    Особенности:
        - Показывает сокращённое название коллекции и дату/модификацию.
        - Текст центрирован.
        - Цвет текста синий (#6199E4).
    """

    STYLE = """
        font-size: 11px;
        color: #6199E4;
    """

    sep = " | "

    def __init__(self, wid: "Thumbnail"):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wid = wid
        self.set_text()

    def set_text(self):
        root = os.path.dirname(self.wid.rel_img_path).strip("/").replace("/", self.sep)
        if not root:
            root = self.wid.collection
        first_row = self.short_text(root)
        text = "\n".join((first_row, self.wid.f_mod))
        self.setText(text)

        self.setStyleSheet(self.STYLE)

    # def short_text(self, text: str) -> str:
    #     """
    #     Сокращает текст, оставляя начало и конец, вставляя '...' посередине.
    #     """
    #     max_row = ThumbData.MAX_ROW[Dynamic.thumb_size_index]
    #     if len(text) >= max_row:
    #         return f"{text[:max_row - 10]}...{text[-7:]}"
    #     return text
    
    def short_text(self, text: str) -> str:
        """
        Сокращает текст, оставляя начало и конец, вставляя '...' посередине.
        """
        max_row = ThumbData.MAX_ROW[Dynamic.thumb_size_index]
        if len(text) > max_row:
            return f"{text[:max_row]}..."
        return text


class Thumbnail(QFrame):
    """
    Виджет миниатюры изображения с текстовой информацией и визуальной рамкой.

    Сигналы:
        reload_thumbnails (pyqtSignal): испускается при изменении избранного в текущей коллекции.
        select (pyqtSignal[str]): испускается при выборе миниатюры, передает путь к файлу.

    Атрибуты класса (настраиваемые):
        sym_star (str): символ для избранного.
        img_frame_size, pixmap_size, thumb_w, thumb_h, corner (int): размеры элементов миниатюры.
        IMG_FRAME_STYLE, TEXT_FRAME_STYLE, IMG_NO_FRAME_STYLE, TEXT_NO_FRAME_STYLE (str): стили для рамки и текста.
    """

    # --- Сигналы ---
    reload_thumbnails = pyqtSignal()

    # --- Константы ---
    sym_star = "\U00002605"

    # --- Параметры размеров (будут изменяться при calculate_size) ---
    img_frame_size = 0
    pixmap_size = 0
    thumb_w = 0
    thumb_h = 0
    corner = 0

    # --- Стили (f-строки с тройными кавычками) ---
    # bg_color будет ссылаться на Static.rgba_gray и Static.rgba_blue
    IMG_FRAME_STYLE = f"""
        border-radius: {{corner}}px;
        color: rgb(255,255,255);
        background: {{bg_color}};
        border: 2px solid transparent;
        padding-left: 2px;
        padding-right: 2px;
    """
    TEXT_FRAME_STYLE = f"""
        border-radius: 7px;
        color: rgb(255,255,255);
        background: {{bg_color}};
        border: 2px solid transparent;
        padding-left: 2px;
        padding-right: 2px;
        font-size: 11px;
    """
    IMG_NO_FRAME_STYLE = """
        border: 2px solid transparent;
        padding-left: 2px;
        padding-right: 2px;
    """
    TEXT_NO_FRAME_STYLE = """
        border: 2px solid transparent;
        font-size: 11px;
    """

    def __init__(self, pixmap: QPixmap, rel_img_path: str, coll_name: str, fav: int, f_mod: str):
        super().__init__()

        # --- Исходные данные ---
        self.img = pixmap
        self.rel_img_path = rel_img_path
        self.collection = coll_name
        self.fav_value = fav
        self.f_mod = f_mod
        self.name = f"{self.sym_star} {os.path.basename(rel_img_path)}" if fav else os.path.basename(rel_img_path)

        # --- Layout ---
        self.v_layout = UVBoxLayout()
        self.v_layout.setSpacing(ThumbData.SPACING)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.v_layout)

        # --- Виджеты ---
        self.img_wid = ImgWid()
        self.v_layout.addWidget(self.img_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.text_wid = FilenameWid(self, self.name, coll_name)
        self.text_wid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(self.text_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.below_text = BelowTextWid(self)
        self.v_layout.addWidget(self.below_text, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setToolTip("\n".join([
                self.name,
                os.path.dirname(self.rel_img_path),
                self.f_mod,
            ])
        )

        self.setup()

    @classmethod
    def calculate_size(cls):
        """Пересчет размеров миниатюр в зависимости от индекса размера."""
        ind = Dynamic.thumb_size_index
        cls.pixmap_size = ThumbData.PIXMAP_SIZE[ind]
        cls.img_frame_size = ThumbData.PIXMAP_SIZE[ind] + ThumbData.MARGIN
        cls.thumb_w = ThumbData.THUMB_W[ind]
        cls.thumb_h = ThumbData.THUMB_H[ind]
        cls.corner = ThumbData.CORNER[ind]

    def setup(self):
        """Настройка миниатюры: текст, размеры, изображение."""
        self.text_wid.set_text()
        self.below_text.set_text()
        self.setFixedSize(self.thumb_w, self.thumb_h)

        size_ = self.pixmap_size + ThumbData.MARGIN
        self.img_wid.setFixedSize(size_, size_)
        self.img_wid.setPixmap(MainUtils.pixmap_scale(self.img, self.pixmap_size))

    def set_frame(self):
        """Устанавливает рамку и фон для выделенной миниатюры."""
        self.img_wid.setStyleSheet(self.IMG_FRAME_STYLE.format(corner=self.corner, bg_color=Static.rgba_gray))
        self.text_wid.setStyleSheet(self.TEXT_FRAME_STYLE.format(bg_color=Static.rgba_blue))

    def set_no_frame(self):
        """Снимает рамку и фон для миниатюры."""
        self.img_wid.setStyleSheet(self.IMG_NO_FRAME_STYLE)
        self.text_wid.setStyleSheet(self.TEXT_NO_FRAME_STYLE)

    def set_transparent_frame(self, value: float):
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(value)
        self.setGraphicsEffect(effect)

    def set_fav(self, value: int):
        """Добавляет или удаляет миниатюру из избранного и обновляет текст."""
        if value == 0:
            self.fav_value = 0
            self.name = os.path.basename(self.rel_img_path)
        else:
            self.fav_value = 1
            self.name = f"{self.sym_star} {os.path.basename(self.rel_img_path)}"

        self.text_wid.name = self.name
        self.text_wid.set_text()

        if value == 0 and Dynamic.current_dir == Static.NAME_FAVS:
            self.reload_thumbnails.emit()


class UpBtn(QFrame):
    """
    Кнопка для прокрутки вверх с круглой серой фоном и SVG-иконкой.

    Сигналы:
        scroll_to_top (pyqtSignal): испускается при нажатии кнопки.

    Атрибуты класса:
        icon (str): путь к SVG-иконке.
        icon_size (int): размер кнопки и иконки.
        bg_color (str): цвет фона кнопки.
        radius (int): радиус скругления кнопки.
        STYLE (str): стиль кнопки в формате f-строки.
    """

    scroll_to_top = pyqtSignal()

    # Настраиваемые параметры
    icon = "./images/up.svg"
    icon_size = 44
    radius = 22

    # --- Стиль кнопки ---
    STYLE = f"""
        background: {Static.rgba_gray};
        border-radius: {radius}px;
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(self.icon_size, self.icon_size)
        self.setStyleSheet(self.STYLE)

        v_layout = UVBoxLayout()
        self.setLayout(v_layout)

        self.svg = SvgBtn(self.icon, self.icon_size)
        v_layout.addWidget(self.svg, alignment=Qt.AlignmentFlag.AlignCenter)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.scroll_to_top.emit()
        super().mouseReleaseEvent(ev)


class DateWid(QLabel):
    """
    QLabel с тенью для отображения даты.

    Атрибуты класса:
        SHADOW_BLUR (int): радиус размытия тени.
        SHADOW_OFFSET (tuple[int, int]): смещение тени (x, y).
        SHADOW_COLOR (QColor): цвет тени.
        COLOR_DATA (dict): соответствие цвета текста палитры → фону.
    """

    SHADOW_BLUR = 20
    SHADOW_OFFSET = (0, 2)
    SHADOW_COLOR = QColor(0, 0, 0, 190)

    TEXT_TO_BG_COLOR = {
        "#000000": "#dcdcdc",
        "#ffffff": "#505050",
    }

    def __init__(self, parent: QWidget, blue_color: bool = True):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(self.SHADOW_BLUR)
        shadow.setOffset(*self.SHADOW_OFFSET)
        shadow.setColor(self.SHADOW_COLOR)
        self.setGraphicsEffect(shadow)
        self.setText("Date wid text")

    def apply_style(self):
        palette = QApplication.palette()
        text_color = QPalette.windowText(palette).color().name()
        if text_color in self.TEXT_TO_BG_COLOR:
            bg_color = self.TEXT_TO_BG_COLOR[text_color]
        else:
            raise Exception(
                "DateWid.apply_style: цвет текста "
                f"'{text_color}' не найден в COLOR_DATA"
            )

        self.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                font-weight: bold;
                font-size: 18pt;
                border-radius: 10px;
                padding: 5px;
            }}
        """)
        

class Grid(VScrollArea):
    """Сетка миниатюр с сигналами для действий с файлами и интерфейсом."""

    # --- Сигналы ---
    restart_scaner = pyqtSignal()
    remove_files = pyqtSignal(list)
    save_files = pyqtSignal(tuple)
    update_bottom_bar = pyqtSignal()
    open_img_view = pyqtSignal()
    no_connection = pyqtSignal()
    open_info_win = pyqtSignal(list)
    copy_path = pyqtSignal(list)
    copy_name = pyqtSignal(list)
    reveal_in_finder = pyqtSignal(list)
    set_fav = pyqtSignal(tuple)
    open_in_app = pyqtSignal(tuple)
    paste_files = pyqtSignal()
    copy_files = pyqtSignal(tuple)
    setup_main_folder = pyqtSignal(SettingsItem)
    
    resize_ms = 10
    date_wid_ms = 3000
    png_copy_files = "./images/copy_files.png"

    def __init__(self):
        super().__init__()

        # --- Состояние и данные ---
        self.wid_under_mouse: Thumbnail = None
        self.origin_pos = QPoint()
        self.selected_widgets: list[Thumbnail] = []
        self.cell_to_wid: dict[tuple, Thumbnail] = {}
        self.path_to_wid: dict[str, Thumbnail] = {}
        self.max_col: int = 0
        self.glob_row, self.glob_col = 0, 0
        self.is_first_load = True
        self.clipboard_item: ClipBoardItem = None

        self.image_apps = {i: os.path.basename(i) for i in SharedUtils.get_apps(Cfg.apps)}

        # --- Таймеры ---
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.rearrange)

        self.date_timer = QTimer(self)
        self.date_timer.setSingleShot(True)
        self.date_timer.timeout.connect(lambda: self.date_wid.hide())

        # --- Вкладка прокрутки ---
        self.scroll_wid = QWidget()
        self.setWidget(self.scroll_wid)
        self.scroll_layout = UVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_wid.setLayout(self.scroll_layout)

        # --- Виджеты ---
        self.date_wid = DateWid(parent=self.viewport())
        self.date_wid.hide()

        self.up_btn = UpBtn(self.viewport())
        self.up_btn.scroll_to_top.connect(lambda: self.verticalScrollBar().setValue(0))
        self.up_btn.hide()

        # --- Сборка ---
        self.load_grid_container()
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

    def reload_thumbnails(self):
        Dynamic.thumbnails_count = 0
        self.load_db_images_task(self.load_initial_grid)

    def load_more_thumbnails(self):
        Dynamic.thumbnails_count += Static.thumbnails_step
        self.load_db_images_task(self.add_more_thumbnails)

    def load_db_images_task(self, on_finish: callable):
        self.task_ = DbImagesLoader()
        self.task_.sigs.finished_.connect(on_finish)
        UThreadPool.start(self.task_)
        
    def load_grid_container(self):
        self.grid_wid = QWidget()
        self.scroll_layout.addWidget(self.grid_wid)
        self.grid_lay = QGridLayout()
        self.grid_lay.setSpacing(1)
        self.grid_wid.setLayout(self.grid_lay)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self.viewport())
        
    def remove_grid_container(self):
        self.grid_wid.deleteLater()
        self.rubberBand.deleteLater()

    def load_initial_grid(self, db_images: dict[str, list[DbImagesLoader.Item]]):

        def create_item():
            item = SettingsItem()
            item.action_type = item.type_edit_folder
            item.content = MainFolder.current
            return item

        def load_grid_delayed():
            self.remove_grid_container()
            self.load_grid_container()
            self.reset_grid_properties()
            self.clear_selected_widgets()
            Thumbnail.calculate_size()
            if not db_images:
                for i in Dynamic.current_dir.split("/"):
                    if i in MainFolder.current.stop_list:
                        settings_wid = QWidget()
                        settings_lay = UVBoxLayout()
                        settings_lay.setSpacing(15)
                        settings_wid.setLayout(settings_lay)
                        self.grid_lay.addWidget(settings_wid, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
                        self.grid_lay.setRowStretch(0, 1)
                        self.grid_lay.setColumnStretch(0, 1)

                        text = f"\"{i}\" {Lng.on_ignore_list[Cfg.lng].lower()}"
                        lbl = QLabel(text)
                        settings_lay.addWidget(lbl)

                        settings = QPushButton(Lng.setup[Cfg.lng])
                        settings.setFixedWidth(110)
                        settings.clicked.connect(
                            lambda: self.setup_main_folder.emit(create_item())
                        )
                        settings_lay.addWidget(settings, alignment=Qt.AlignmentFlag.AlignCenter)
                        break
                else:
                    lbl = QLabel(Lng.no_photo[Cfg.lng])
                    self.grid_lay.addWidget(lbl, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
                    self.grid_lay.setRowStretch(0, 1)
                    self.grid_lay.setColumnStretch(0, 1)
            else:
                for _, db_images_list in db_images.items():
                    self.add_thumbnails_to_grid(db_images_list)
                self.rearrange()
                self.grid_wid.show()
                QTimer.singleShot(100, self.setFocus)

        self.grid_wid.hide()
        QTimer.singleShot(50, load_grid_delayed)
                        
    def add_thumb_data(self, wid: Thumbnail):
        self.path_to_wid[wid.rel_img_path] = wid
        self.cell_to_wid[self.glob_row, self.glob_col] = wid
        wid.row, wid.col = self.glob_row, self.glob_col        

    def add_thumbnails_to_grid(self, db_images: list[DbImagesLoader.Item]):

        def create_thumb(image_item: DbImagesLoader.Item):
            thumbnail = Thumbnail(
                pixmap=pixmap,
                rel_img_path=image_item.rel_img_path,
                coll_name=image_item.coll_name,
                fav=image_item.fav,
                f_mod=image_item.f_mod
            )
            thumbnail.set_no_frame()
            thumbnail.reload_thumbnails.connect(self.reload_thumbnails)

            if pixmap is None:
                print(image_item.rel_img_path)

            return thumbnail

        for image_item in db_images:
            pixmap = QPixmap.fromImage(image_item.qimage)
            thumbnail = create_thumb(image_item)
            self.add_thumb_data(thumbnail)
            self.grid_lay.addWidget(thumbnail, 0, 0)

    def add_more_thumbnails(self, db_images: dict[str, list[DbImagesLoader.Item]]):
        for _, db_images_list in db_images.items():
            self.add_thumbnails_to_grid(db_images_list)
        self.rearrange()

    def select_viewed_image(self, path: str):
        if path in self.path_to_wid:
            wid = self.path_to_wid.get(path)
            self.clear_selected_widgets()
            self.wid_to_selected_widgets(wid)
    
    def reset_grid_properties(self):
        self.max_col = self.width() // (ThumbData.THUMB_W[Dynamic.thumb_size_index])
        self.glob_row, self.glob_col = 0, 0
        for i in (self.cell_to_wid, self.path_to_wid):
            i.clear()

    def resize_thumbnails(self):
        """
        - Высчитывает новые размеры Thumbnail
        - Меняет размеры виджетов Thumbnail в текущей сетке
        - Переупорядочивает сетку в соотетствии с новыми размерами
        """
        Thumbnail.calculate_size()
        for _, wid in self.cell_to_wid.items():
            wid.setup()
            if wid in self.selected_widgets:
                wid.set_frame()
        self.rearrange()

    def rearrange(self):
        """
        Переупорядочивает все миниатюры в сетке заново.

        Логика:
            - Сбрасывает свойства сетки (строки и столбцы)
            - Находит все Thumbnail в контейнере
            - Расставляет их по рядам и колонкам
            - Если сортировка по модификации включена, начинает новый ряд при смене модификации
        """

        def _next_row():
            """Сдвигает счетчики сетки на новый ряд."""
            self.glob_col = 0
            self.glob_row += 1

        self.reset_grid_properties()
        thumbnails = self.grid_wid.findChildren(Thumbnail)
        if not thumbnails:
            return

        prev_f_mod = thumbnails[0].f_mod
        for thumb in thumbnails:
            # Проверка на смену модификации при сортировке по модификации
            if Dynamic.sort_by_mod and thumb.f_mod != prev_f_mod:
                _next_row()

            # Добавляем миниатюру в сетку и обновляем координаты
            self.add_thumb_data(thumb)
            self.grid_lay.addWidget(thumb, self.glob_row, self.glob_col)

            # Переходим к следующей колонке, если достигнут максимум, переход к следующему ряду
            self.glob_col += 1
            if self.glob_col >= self.max_col:
                _next_row()

            prev_f_mod = thumb.f_mod

        # Если последний ряд не завершен, начинаем новый ряд для следующих элементов
        if self.glob_col != 0:
            _next_row()

    def get_clicked_widget(self, a0: QMouseEvent) -> None | Thumbnail:
        wid = QApplication.widgetAt(a0.globalPos())
        if isinstance(wid, (ImgWid, FilenameWid)):
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

    def wid_to_selected_widgets(self, wid: Thumbnail):
        """
        - Добавляет переданный виджет в selected widgets
        - Задает стиль переданному виджету
        """
        if isinstance(wid, Thumbnail):
            self.selected_widgets.append(wid)
            wid.set_frame()
                
    def set_thumb_fav(self, rel_img_path: str, value: int):
        if rel_img_path in self.path_to_wid:
            wid = self.path_to_wid.get(rel_img_path)
            wid.set_fav(value)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        """
        Обрабатывает навигацию и горячие клавиши в сетке:
            - Ctrl+I: открыть информацию по выбранным элементам
            - Ctrl+A: выделить все элементы
            - Space / Enter: открыть просмотр последнего выбранного элемента
            - Стрелки: навигация по элементам сетки
        """

        def remove_files():
            self.remove_files.emit(
                [i.rel_img_path for i in self.selected_widgets]
            )

        def open_info():
            """Открывает окно информации для выбранных виджетов."""
            if self.selected_widgets:
                self.open_info_win.emit([i.rel_img_path for i in self.selected_widgets])

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
            remove_files()
        if event.modifiers() == CTRL and event.key() == Qt.Key.Key_I:
            open_info()
        elif event.modifiers() == CTRL and event.key() == Qt.Key.Key_A:
            select_all()
        elif event.modifiers() == CTRL and event.key() == Qt.Key.Key_C:
            self.copy_files.emit(
                (ClipBoardItem.type_copy, [i.rel_img_path for i in self.selected_widgets])
            )
        elif event.modifiers() == CTRL and event.key() == Qt.Key.Key_X:
            self.copy_files.emit(
                (ClipBoardItem.type_cut, [i.rel_img_path for i in self.selected_widgets])
            )
        elif event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
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
                widgets = wid.findChildren((FilenameWid, ImgWid))
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
        else:
            self.clear_selected_widgets()
            self.wid_to_selected_widgets(self.wid_under_mouse)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.resize_timer.stop()
        self.resize_timer.start(self.resize_ms)

        self.up_btn.move(
            self.viewport().width() - self.up_btn.width() - 20,
            self.viewport().height() - self.up_btn.height() - 20
        )        

        self.date_wid.move(
            (self.viewport().width() - self.date_wid.width()) // 2,
            NotifyWid.yy
        )

        return super().resizeEvent(a0)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        """Создаёт контекстное меню для пустой области или выбранных виджетов."""
        self.menu_ = UMenu(event=a0)
        clicked_wid = self.get_clicked_widget(a0)

        def menu_empty():
            self.clear_selected_widgets()

            update_grid = QAction(Lng.update_grid[Cfg.lng], self.menu_)
            update_grid.triggered.connect(self.reload_thumbnails)
            self.menu_.addAction(update_grid)

            reload = ScanerRestart(parent=self.menu_)
            reload.triggered.connect(lambda: self.restart_scaner.emit())
            self.menu_.addAction(reload)

            if self.clipboard_item:
                self.menu_.addSeparator()
                paste = PasteFiles(self.menu_)
                paste.triggered.connect(self.paste_files.emit)
                self.menu_.addAction(paste)
                self.menu_.addSeparator()

            self.menu_.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], self.menu_)
            reveal.triggered.connect(lambda: self.reveal_in_finder.emit([Dynamic.current_dir]))
            self.menu_.addAction(reveal)

        def menu_widget(clicked: Thumbnail):
            if not self.selected_widgets:
                self.wid_to_selected_widgets(clicked)
            elif clicked not in self.selected_widgets:
                self.clear_selected_widgets()
                self.wid_to_selected_widgets(clicked)

            rel_paths = [w.rel_img_path for w in self.selected_widgets]

            # просмотр
            act = OpenInView(self.menu_)
            act.triggered.connect(lambda: self.open_img_view.emit())
            self.menu_.addAction(act)

            # открыть в приложении
            open_menu = USubMenu(
                f"{Lng.open_in[Cfg.lng]} ({len(rel_paths)})",
                self.menu_
            )

            act = QAction(Lng.open_default[Cfg.lng], open_menu)
            act.triggered.connect(lambda: self.open_in_app.emit((rel_paths, None)))
            open_menu.addAction(act)
            open_menu.addSeparator()

            for app_path, basename in self.image_apps.items():
                act = QAction(basename, open_menu)
                act.triggered.connect(lambda _, x=app_path: self.open_in_app.emit((rel_paths, x)))
                open_menu.addAction(act)

            self.menu_.addMenu(open_menu)

            # избранное
            if len(rel_paths) == 1:
                fav = SetFav(self.menu_, clicked.fav_value)
                fav.triggered.connect(lambda: self.set_fav.emit((clicked.rel_img_path, not clicked.fav_value)))
                self.menu_.addAction(fav)

            # инфо
            act = WinInfoAction(self.menu_)
            act.triggered.connect(lambda: self.open_info_win.emit(rel_paths))
            self.menu_.addAction(act)
            self.menu_.addSeparator()

            # reveal / copy
            act = RevealInFinder(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.reveal_in_finder.emit(rel_paths))
            self.menu_.addAction(act)

            act = CopyPath(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.copy_path.emit(rel_paths))
            self.menu_.addAction(act)

            act = CopyName(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.copy_name.emit(rel_paths))
            self.menu_.addAction(act)
            self.menu_.addSeparator()

            # cut / copy / paste
            act = CutFiles(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.copy_files.emit((ClipBoardItem.type_cut, rel_paths)))
            self.menu_.addAction(act)

            act = CopyFiles(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.copy_files.emit((ClipBoardItem.type_copy, rel_paths)))
            self.menu_.addAction(act)

            self.menu_.addSeparator()

            # save / remove
            act = Save(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.save_files.emit((os.path.expanduser("~/Downloads"), rel_paths)))
            self.menu_.addAction(act)

            act = SaveAs(self.menu_, len(rel_paths))
            act.triggered.connect(lambda: self.save_files.emit((None, rel_paths)))
            self.menu_.addAction(act)

            act = RemoveFiles(self.menu_, len(self.selected_widgets))
            act.triggered.connect(lambda: self.remove_files.emit(rel_paths))
            self.menu_.addAction(act)

        if not clicked_wid:
            menu_empty()
        else:
            menu_widget(clicked_wid)

        self.menu_.show_umenu()

    def checkScrollValue(self, value: int):
        """Обрабатывает прокрутку: показывает кнопку вверх, дату и подгружает миниатюры."""

        def thumbnail_under_point(point: QPoint) -> Thumbnail | None:
            mapped_pos = self.scroll_wid.mapFrom(self.viewport(), point)
            wid = self.scroll_wid.childAt(mapped_pos)
            if wid and isinstance(wid.parent(), Thumbnail):
                return wid.parent()
            return None

        def update_date_wid(wid: Thumbnail):
            self.date_wid.setText(wid.f_mod)
            self.date_wid.adjustSize()
            self.date_wid.move(
                (self.viewport().width() - self.date_wid.width()) // 2,
                NotifyWid.yy
            )

            if self.date_wid.isHidden() and Dynamic.sort_by_mod:
                self.date_wid.apply_style()
                self.date_wid.show()
                self.date_timer.start(self.date_wid_ms)

        # --- кнопка вверх ---
        self.up_btn.setVisible(value > 0)

        # --- дата ---
        if value > 0:
            wid = thumbnail_under_point(QPoint(50, 50))
            if wid:
                update_date_wid(wid)
        else:
            self.date_wid.hide()

        # --- конец списка ---
        if value == self.verticalScrollBar().maximum():
            self.load_more_thumbnails()

    def mouseDoubleClickEvent(self, a0):
        if self.wid_under_mouse:
            self.clear_selected_widgets()
            self.wid_to_selected_widgets(self.wid_under_mouse)
            self.open_img_view.emit()

    def mousePressEvent(self, a0):
        self.origin_pos = a0.pos()
        self.wid_under_mouse = self.get_clicked_widget(a0)
        return super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0):
        try:
            distance = (a0.pos() - self.origin_pos).manhattanLength()
        except AttributeError:
            MainUtils.print_error()
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
            main_folder_path = MainFolder.current.get_curr_path()
            img_paths = []
            if main_folder_path:
                img_paths = [
                    MainUtils.get_abs_path(main_folder_path, wid.rel_img_path)
                    for wid in self.selected_widgets
                ]

            if not img_paths:
                return self.no_connection.emit()

            # создаём объект перетаскивания
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)

            # иконка для drag
            drag_icon = QPixmap(self.png_copy_files)
            drag.setPixmap(drag_icon)

            # назначаем urls
            mime_data.setUrls([QUrl.fromLocalFile(p) for p in img_paths])
            drag.exec_(Qt.DropAction.CopyAction)

        # --- Основная логика ---
        if self.wid_under_mouse is None and not self.rubberBand.isVisible():
            start_rubber_band()
        elif self.rubberBand.isVisible():
            update_rubber_band()
        else:
            start_drag()

        return super().mouseMoveEvent(a0)

