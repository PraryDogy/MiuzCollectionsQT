import os
import re

from PyQt6.QtCore import (QDate, QLocale, QMimeData, QPoint, QRect, QSize, Qt,
						  QTimer, QUrl, pyqtSignal)
from PyQt6.QtGui import (QAction, QColor, QContextMenuEvent, QCursor, QDrag,
						 QFontMetrics, QIcon, QImage, QKeyEvent, QMouseEvent,
						 QPixmap, QResizeEvent, QPainter, QFont)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout,
							 QRubberBand, QSizePolicy, QVBoxLayout)

from cfg import Dynamic, JsonData, Static
from system.items import DataItem, SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import SharedUtils
from system.tasks import DbImagesLoader, DbImagesLoaderItem, UThreadPool, AppsScanner
from system.utils import Utils

from ._base_widgets import (FlowLayout, GrayTextLabel, TransparentFrame,
							TransparentLabel, TransparentWidget, UMenu,
							UPushButton, UScrollVerticalArea, USep, UTagWidget)
from .actions import (CollageAction, CopyFiles, CopyPath, OpenInView,
					  PasteFiles, RemoveFiles, RevealInFinder, Save,
					  ScanerRestart, SetFav, ShowInFolder, UpdateThumbAction,
					  WinInfoAction)
from .win_filters import DatesWidget


CONTROLS_MARGIN = 10


class ThumbImgWidget(TransparentLabel):
	_badge_font = None  # общий для всех миниатюр, создаётся лениво

	def __init__(self):
		super().__init__()
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self._saved_pixmap = None
		self.badge_text = ""
		self._badge_rect: QRect | None = None  # пересчитывается при смене текста или размера

	@classmethod
	def _get_font(cls) -> QFont:
		if cls._badge_font is None:
			f = QFont(QApplication.font())
			f.setBold(True)
			f.setPointSizeF(max(7.0, f.pointSizeF() * 0.85))
			cls._badge_font = f
		return cls._badge_font

	def set_badge_text(self, text: str):
		self.badge_text = text
		self._badge_rect = None  # пересчитаем в paintEvent

	def _calc_badge_rect(self, painter: QPainter) -> QRect:
		painter.setFont(self._get_font())
		fm = painter.fontMetrics()
		w = fm.horizontalAdvance(self.badge_text) + 8
		h = fm.height() + 4
		return QRect(self.width() - w - 4, 4, w, h)

	def paintEvent(self, event):
		super().paintEvent(event)
		if not self.badge_text or self.pixmap() is None or self.pixmap().isNull():
			return
		p = QPainter(self)
		p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
		if self._badge_rect is None or self._badge_rect.right() + 4 != self.width():
			self._badge_rect = self._calc_badge_rect(p)
		rect = self._badge_rect
		p.setPen(Qt.PenStyle.NoPen)
		p.setBrush(QColor(0, 0, 0, 170))
		p.drawRoundedRect(rect, 3, 3)
		p.setPen(QColor(255, 255, 255))
		p.setFont(self._get_font())
		p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.badge_text)
		p.end()

	def show_updating(self):
		"""Показывает текст 'обновление' вместо изображения."""
		self._saved_pixmap = self.pixmap()
		self.setPixmap(QPixmap())
		self.setText(Lng.updating[JsonData.lng_index])

	def restore_image(self):
		"""Удаляет текст и возвращает исходное изображение."""
		self.setText("")
		if self._saved_pixmap:
			self.setPixmap(self._saved_pixmap)


class ThumbFilenameWid(TransparentLabel):
	def __init__(self, filename: str):
		super().__init__(filename)
		self.set_elide(True)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class ThumbBlueTextWidget(GrayTextLabel):
	def __init__(self, data_item: DataItem):
		day_month_year = f"{Lng.changed_short[JsonData.lng_index]} {data_item.day_month_year}"
		super().__init__(day_month_year)
		self.set_elide(True)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class ThumbMiuzBlueTextWidget(GrayTextLabel):
	COLLECTION_RE = re.compile(r"^/+(?:\d+\s+)?([^/]+)")

	def __init__(self, data_item: DataItem):
		root = os.path.dirname(data_item.rel_path)
		if len(root) == 1:
			miuz_collection_name = Mf.current_mf.mf_alias
		else:
			paths_list = root.split(os.sep)
			miuz_collection_name = paths_list[1]
		day_month_year = f"{Lng.changed_short[JsonData.lng_index]} {data_item.day_month_year}"
		super().__init__(f"{day_month_year}\n{miuz_collection_name}")
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.set_elide(True)


class Thumb(TransparentFrame):
	sym_star = "\U00002605"
	thumb_width = 0
	thumb_offset = 0
	img_w = 0       # ширина области картинки
	img_h = 0       # высота области картинки
	frame_w = 0     # полная ширина виджета Thumb
	frame_h = 0     # полная высота виджета Thumb
	blue_text_class = ThumbBlueTextWidget
	BORDER_W = 2  # должна совпадать с border в QSS для Thumb и SquareThumb
	fast_scale = False

	# не передавай PARENT в Thumb, иначе не отображаются

	def __init__(self, data_item: DataItem):
		super().__init__()
		self.row, self.col, self.idx = 0, 0, 0   # idx — линейный индекс в сетке
		self.data_item = data_item
		if self.data_item.fav:
			self.data_item.filename = f"{self.sym_star} {self.data_item.filename}"

		self._size_key = None
		self._pixmap_index = None
		self._framed = False
		self._pixmap_fast = False  # картинка сейчас нарисована быстрым методом

		# --- Layout ---
		self.v_lay = QVBoxLayout(self)
		self.v_lay.setSpacing(3)
		self.v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

		self.img_wid = ThumbImgWidget()
		self.v_lay.addWidget(self.img_wid, alignment=Qt.AlignmentFlag.AlignCenter)
		self.img_wid.set_badge_text(os.path.splitext(data_item.rel_path)[1].lstrip(".").upper())

		self._add_captions()

		filename = f"{Lng.file_name[JsonData.lng_index]}: {self.data_item.filename}"
		location = f"{Lng.location[JsonData.lng_index]}: {Mf.current_mf.mf_paths[0]}{self.data_item.rel_path}"
		modified = f"{Lng.modified[JsonData.lng_index]}: {self.data_item.day_month_year} {self.data_item.hour_min_sec}"
		self.setToolTip("\n".join([filename, location, modified]))

		self.set_text_and_size()

	# --- Геометрия: считается один раз в calculate_size ---

	@classmethod
	def _img_box_size(cls) -> tuple[int, int]:
		return (cls.thumb_width + cls.thumb_offset, cls.thumb_width)

	@classmethod
	def _margins(cls) -> tuple[int, int, int, int]:
		return (10, 10, 10, 5)

	@classmethod
	def _captions_height(cls) -> int:
		# Оценка по метрикам шрифта: имя файла + строки даты,
		# плюс spacing и addSpacing(5) между элементами лейаута
		fm = QFontMetrics(QApplication.font())
		lines = 2 if cls.blue_text_class is ThumbMiuzBlueTextWidget else 1
		return fm.height() * (1 + lines) + 5 + 3 * 3

	@classmethod
	def calculate_size(cls):
		ind = Dynamic.current_pixmap_size_index
		cls.thumb_width = Static.THUMB_WIDTHS[ind]
		cls.thumb_offset = Static.THUMB_OFFSETS[ind]
		if Static.MIUZ_ZIP.exists():
			Thumb.blue_text_class = ThumbMiuzBlueTextWidget

		cls.img_w, cls.img_h = cls._img_box_size()
		left, top, right, bottom = cls._margins()
		b = cls.BORDER_W * 2
		cls.frame_w = cls.img_w + left + right + b
		cls.frame_h = cls.img_h + top + bottom + cls._captions_height() + b

	# --- Построение лейаута ---

	def _add_captions(self):
		self.v_lay.setContentsMargins(*self._margins())
		self.v_lay.addSpacing(2)
		self.white_text_wid = ThumbFilenameWid(self.data_item.filename)
		self.v_lay.addWidget(self.white_text_wid, alignment=Qt.AlignmentFlag.AlignCenter)
		self.blue_text_wid = self.blue_text_class(self.data_item)
		self.v_lay.addWidget(self.blue_text_wid, alignment=Qt.AlignmentFlag.AlignCenter)

	# --- Стили ---

	def _update_style(self):
		# Принудительное обновление QSS-стиля виджета
		self.style().unpolish(self)
		self.style().polish(self)

	# --- Стили ---

	def _update_style(self):
		# Принудительное обновление QSS-стиля виджета
		self.style().unpolish(self)
		self.style().polish(self)

	def _set_framed(self, value: bool):
		# polish дорогой, поэтому вызываем только при реальном изменении
		if self._framed == value:
			return
		self._framed = value
		self.setProperty("framed", value)
		self._update_style()

	def set_frame(self):
		self._set_framed(True)

	def set_no_frame(self):
		self._set_framed(False)

	# --- Картинка и размер ---

	def set_pixmap_with_actual_size(self, force: bool = False):
		idx = Dynamic.current_pixmap_size_index
		fast = Thumb.fast_scale

		# перерисовываем, если сменился размер, принудительно, или нужна сглаженная версия
		need = force or self._pixmap_index != idx or (self._pixmap_fast and not fast)
		if not need:
			return

		cached = self.data_item.resized_qimages[idx]
		if cached is not None:
			qimg, is_fast = cached, False
		elif fast:
			# быстрый вариант не кладём в resized_qimages, иначе он останется после перетаскивания
			qimg = Utils.scale_qimage_dpr(self.data_item.base_qimage,
										Static.THUMB_WIDTHS[idx], smooth=False)
			is_fast = True
		else:
			qimg = Utils.scale_qimage_dpr(self.data_item.base_qimage,
										Static.THUMB_WIDTHS[idx])
			self.data_item.resized_qimages[idx] = qimg
			is_fast = False

		self._pixmap_index = idx
		self._pixmap_fast = is_fast
		self.img_wid.setPixmap(QPixmap.fromImage(qimg))

	def set_text_and_size(self):
		# только геометрия, картинку не трогаем
		key = (self.img_w, self.img_h, self.frame_w, self.frame_h)
		if key != self._size_key:
			self._size_key = key
			self.img_wid.setFixedSize(self.img_w, self.img_h)
			self.setFixedWidth(self.frame_w)

	# --- Избранное ---

	def _set_fav_data(self, value: int):
		self.data_item.fav = 1 if value else 0
		base = os.path.basename(self.data_item.rel_path)
		self.data_item.filename = f"{self.sym_star} {base}" if value else base

	def _update_caption(self):
		self.white_text_wid.setText(self.data_item.filename)

	def set_fav(self, value: int):
		self._set_fav_data(value)
		self._update_caption()


class SquareThumb(Thumb):
	@classmethod
	def _img_box_size(cls) -> tuple[int, int]:
		return (cls.thumb_width, cls.thumb_width)

	@classmethod
	def _margins(cls) -> tuple[int, int, int, int]:
		return (3, 3, 3, 3)  # запас под рамку выделения, зазор задаёт spacing

	@classmethod
	def _captions_height(cls) -> int:
		return 0

	def _add_captions(self):
		# Подписей в квадратном режиме нет
		self.v_lay.setContentsMargins(*self._margins())

	def _update_caption(self):
		# Подписи нет, обновлять нечего
		pass


class UpBtnLabel(TransparentLabel):
	widget_size = (36, 36)
	def __init__(self):
		super().__init__()
		self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
		self.setFixedSize(*self.widget_size)


class UpBtn(TransparentWidget):
	scroll_to_top = pyqtSignal()
	icon_path = Static.COMMON_ICONS / "arrow_up.svg"
	icon_size = (28, 28)

	def __init__(self, parent: TransparentWidget | None = None):
		super().__init__(parent)
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setFixedSize(*UpBtnLabel.widget_size)

		# 1. Отдельный класс подложки
		self.label = UpBtnLabel()

		# 2. Фиксированная SVG-иконка
		self.svg_widget = QSvgWidget(str(self.icon_path), self)
		self.svg_widget.setFixedSize(*self.icon_size)
		self.svg_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

		# 3. Наслоение через сетку
		layout = QGridLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		layout.addWidget(self.label, 0, 0)
		layout.addWidget(self.svg_widget, 0, 0, Qt.AlignmentFlag.AlignCenter)

		# Гарантируем, что подложка всегда строго под SVG
		self.label.stackUnder(self.svg_widget)

	def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
		if ev and ev.button() == Qt.MouseButton.LeftButton:
			if self.rect().contains(ev.pos()):
				self.scroll_to_top.emit()
		super().mouseReleaseEvent(ev)


class GridModeWidget(UPushButton):
	load_st_grid = pyqtSignal()
	view_mode_svg = Static.COMMON_ICONS / "view_mode.svg"
	icon_offset = 35  # иконка слева и стрелка справа

	def __init__(self):
		self.MODES = {
			False: Lng.captions_on[JsonData.lng_index],
			True: Lng.captions_off[JsonData.lng_index]
		}

		current = JsonData.square_thumbs
		super().__init__(self.MODES[current])

		self.setIcon(QIcon(str(self.view_mode_svg)))

		self.menu_ = UMenu(parent=self)
		self.setMenu(self.menu_)

		self.actions_ = {}
		for square, text in self.MODES.items():
			act = QAction(text, self.menu_)
			act.setCheckable(True)
			act.triggered.connect(lambda _, s=square: self.change_mode(s))
			self.menu_.addAction(act)
			self.actions_[square] = act

		self.actions_[current].setChecked(True)

		self._fix_width()

	def _fix_width(self):
		metrics = QFontMetrics(self.font())
		text_width = max(metrics.horizontalAdvance(text) for text in self.MODES.values())
		self.setFixedWidth(text_width + self.icon_offset + self.iconSize().width())

	def change_mode(self, square: bool):
		if JsonData.square_thumbs == square:
			return
		JsonData.square_thumbs = square
		self.setText(self.MODES[square])
		self.load_st_grid.emit()


class GridSortWidget(TransparentWidget):
	sort_icon_svg = Static.COMMON_ICONS / "sort.svg"
	load_st_grid = pyqtSignal()

	def __init__(self):
		super().__init__()

		self.sort_icon = QIcon(str(self.sort_icon_svg))

		self.h_lay = QHBoxLayout(self)
		self.h_lay.setContentsMargins(0, 0, 0, 0)
		self.h_lay.setSpacing(5)
		self.h_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

		self.button = UPushButton("")
		self.set_button_width()
		self.set_sort_button_text()
		self.button.setIcon(self.sort_icon)
		self.h_lay.addWidget(self.button)

		self.button_menu = UMenu(parent=self)
		self.button.setMenu(self.button_menu)

		mod_action = QAction(Lng.sort_by_mod[JsonData.lng_index], self.button_menu)
		mod_action.triggered.connect(lambda: self.sort_btn_cmd(True))
		self.button_menu.addAction(mod_action)

		recent_action = QAction(Lng.sort_by_recent[JsonData.lng_index], self.button_menu)
		recent_action.triggered.connect(lambda: self.sort_btn_cmd(False))
		self.button_menu.addAction(recent_action)

	def set_button_width(self):
		ind = JsonData.lng_index
		word = max((Lng.sort_by_mod[ind], Lng.sort_by_recent[ind]), key=len)
		self.button.setText(word)
		self.button.adjustSize()
		offset = 40 # иконка слева и стрелочка справа
		self.button.setFixedWidth(self.button.width() + offset)

	def sort_btn_cmd(self, value: bool):
		Dynamic.sort_by_mod_enabled = value
		self.set_sort_button_text()
		self.load_st_grid.emit()

	def set_sort_button_text(self):
		if Dynamic.sort_by_mod_enabled:
			text = Lng.sort_by_mod
		else:
			text = Lng.sort_by_recent
		self.button.setText(text[JsonData.lng_index])


class GridFiltersWidget(TransparentWidget):
	sort_icon_svg = Static.COMMON_ICONS / "filters.svg"
	open_filters_win = pyqtSignal()

	def __init__(self):
		super().__init__()

		self.sort_icon = QIcon(str(self.sort_icon_svg))

		self.h_lay = QHBoxLayout(self)
		self.h_lay.setContentsMargins(0, 0, 0, 0)

		self.button = UPushButton(Lng.filters[JsonData.lng_index])
		self.button.clicked.connect(self.open_filters_win.emit)
		self.button.setIcon(self.sort_icon)
		self.h_lay.addWidget(self.button)


class GridControlsWidget(TransparentWidget):
	# Общий сигнал, который будет срабатывать при изменении сортировки или фильтров
	load_st_grid = pyqtSignal()
	open_filters_win = pyqtSignal()

	def __init__(self):
		super().__init__()

		# Используем вертикальный лэйаут, чтобы расположить их друг под другом
		self.v_lay = QHBoxLayout(self)
		self.v_lay.setContentsMargins(CONTROLS_MARGIN, 0, CONTROLS_MARGIN, 0)
		self.v_lay.setSpacing(10) # Отступ между виджетом сортировки и фильтрами

		# Инициализируем внутренние виджеты
		self.grid_mode_widget = GridModeWidget()
		self.sort_widget = GridSortWidget()
		self.filters_widget = GridFiltersWidget()

		# Добавляем их в лэйаут
		self.v_lay.addWidget(self.grid_mode_widget)
		self.v_lay.addWidget(self.sort_widget)
		self.v_lay.addWidget(self.filters_widget)

		# Перенаправляем (пробрасываем) внутренние сигналы наверх
		self.grid_mode_widget.load_st_grid.connect(self.load_st_grid.emit)
		self.sort_widget.load_st_grid.connect(self.load_st_grid.emit)
		self.filters_widget.open_filters_win.connect(self.open_filters_win.emit)

		self.v_lay.addStretch()


class GridTag(UTagWidget):
	right_svg_path = Static.COMMON_ICONS / "cancel.svg"
	right_svg_size = (12, 12)

	def __init__(self, left_svg_path, text):
		super().__init__(
			qss_style=self.qss_green,
			left_svg_path=str(left_svg_path),
			text=text,
			right_svg_path=str(self.right_svg_path)
		)
		self.right_svg_widget.setFixedSize(*self.right_svg_size)
		self.right_svg_lay.setContentsMargins(0, 1, 0, 0)


class GridDatesTag(GridTag):
	left_svg_path = Static.COMMON_ICONS / "gray_calendar.svg"

	def __init__(self):
		super().__init__(
			text=DatesWidget.readable_date,
			left_svg_path=self.left_svg_path
		)

	def right_svg_cmd(self, *args):
		Dynamic.py_date_start = None
		Dynamic.py_date_end = None
		return super().right_svg_cmd(*args)


class GridWordTag(GridTag):
	left_svg_path = Static.COMMON_ICONS / "tags.svg"

	def __init__(self, text):
		super().__init__(
			text=text,
			left_svg_path=self.left_svg_path
		)

	def right_svg_cmd(self, *args):
		Dynamic.word_tags_list.remove(self.text_widget.text())
		return super().right_svg_cmd(*args)


class GridFavTag(GridTag):
	left_svg_path = Static.COMMON_ICONS / "fav.svg"

	def __init__(self):
		super().__init__(
			text=Lng.favorites[JsonData.lng_index],
			left_svg_path=self.left_svg_path
		)

	def right_svg_cmd(self, *args):
		Dynamic.favs_tag_enabled = False
		return super().right_svg_cmd(*args)


class GridNoSubfoldersTag(GridTag):
	left_svg_path = Static.COMMON_ICONS / "folder_gray.svg"

	def __init__(self):
		super().__init__(
			text=Lng.without_subfolders[JsonData.lng_index],
			left_svg_path=self.left_svg_path
		)

	def right_svg_cmd(self, *args):
		Dynamic.no_subfolders_tag_enabled = False
		return super().right_svg_cmd(*args)


class TagsWidget(TransparentWidget):
	load_st_grid = pyqtSignal()
	open_filters_win = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)

		self.flow_layout = FlowLayout(self, spacing=7)
		self.flow_layout.setContentsMargins(CONTROLS_MARGIN, 0, CONTROLS_MARGIN, 0)
		self._create_tags()

	def _create_tags(self):
		if Dynamic.py_date_start or Dynamic.py_date_end:
			tag = GridDatesTag()
			tag.right_svg_clicked.connect(self.load_st_grid.emit)
			tag.text_clicked.connect(self.open_filters_win.emit)
			self.flow_layout.addWidget(tag)

		if Dynamic.word_tags_list:
			for word in Dynamic.word_tags_list:
				tag = GridWordTag(word)
				tag.right_svg_clicked.connect(self.load_st_grid.emit)
				tag.text_clicked.connect(self.open_filters_win.emit)
				self.flow_layout.addWidget(tag)

		if Dynamic.favs_tag_enabled:
			tag = GridFavTag()
			tag.right_svg_clicked.connect(self.load_st_grid.emit)
			tag.text_clicked.connect(self.open_filters_win.emit)
			self.flow_layout.addWidget(tag)

		if Dynamic.no_subfolders_tag_enabled:
			tag = GridNoSubfoldersTag()
			tag.right_svg_clicked.connect(self.load_st_grid.emit)
			tag.text_clicked.connect(self.open_filters_win.emit)
			self.flow_layout.addWidget(tag)

	def hasHeightForWidth(self):
		return True

	def heightForWidth(self, width):
		return self.flow_layout.heightForWidth(width)

	def sizeHint(self):
		width = self.parentWidget().width() if self.parentWidget() else 500
		return QSize(width, self.heightForWidth(width))


class Grid(UScrollVerticalArea):
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
	open_filters_win = pyqtSignal()

	resize_ms = 10
	thumb_cls = Thumb
	copy_files_path = Static.COMMON_ICONS / "copy_files.svg"

	def __init__(self):
		super().__init__()
		qimage = QImage(str(self.copy_files_path))
		qimage_scaled = Utils.scale_qimage_dpr(qimage, 80)
		self.copy_files_icon = QPixmap.fromImage(qimage_scaled)

		# --- Состояние и данные ---
		self.wid_under_mouse: Thumb | None = None
		self.origin_pos = QPoint()
		self._sel: dict[Thumb, None] = {}      # выделение: ключи в порядке вставки, O(1)
		self.ordered: list[Thumb] = []         # виджеты в порядке отображения, idx = позиция
		self._cols = 1                         # текущее число колонок сетки
		self._layout_cols = -1                 # колонки, с которыми последний раз раскладывали сетку
		self._layout_count = -1                # число виджетов на последней раскладке
		self.cell_to_wid: dict[tuple, Thumb] = {}
		self.url_to_wid: dict[str, Thumb] = {}
		self.files_to_copy = set()

		# --- Дозагрузка ---
		self._loading_more = False             # защита от параллельных запросов
		self._exhausted = False                # БД вернула пустую порцию
		self._fill_retries = 0                 # счётчик повторов проверки, пока геометрия не готова

		# --- Приложения для «Открыть в…» (ищутся в фоне через URunnable) ---
		self._image_apps: dict[str, str] = {}
		self._apps_task = AppsScanner(Static.IMAGE_APPS)
		self._apps_task.sigs.finished_.connect(self._on_apps_found)
		UThreadPool.start(self._apps_task)

		# --- Таймеры ---
		self.resize_timer = QTimer(self)
		self.resize_timer.setSingleShot(True)
		self.resize_timer.timeout.connect(self.rearrange)

		self.date_timer = QTimer(self)
		self.date_timer.setSingleShot(True)

		# таймер окончания перетаскивания слайдера: сглаженный проход один раз
		self._size_timer = QTimer(self)
		self._size_timer.setSingleShot(True)
		self._size_timer.timeout.connect(self._finish_resize)
		self._size_debounce_ms = 200

		# --- Вкладка прокрутки ---
		self.scroll_wid = TransparentFrame()
		self.setWidget(self.scroll_wid)
		self.scroll_layout = QVBoxLayout(self.scroll_wid)
		self.scroll_layout.setContentsMargins(0, 0, 0, 0)
		self.scroll_layout.setSpacing(0)
		self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

		self.up_btn = UpBtn(self.viewport())
		self.up_btn.scroll_to_top.connect(lambda: self.verticalScrollBar().setValue(0))
		self.up_btn.hide()

		self.grid_controls_widget = GridControlsWidget()
		self.grid_controls_widget.open_filters_win.connect(self.open_filters_win.emit)
		self.grid_controls_widget.load_st_grid.connect(self.load_st_grid.emit)
		self.scroll_layout.addWidget(self.grid_controls_widget)
		self.scroll_layout.addSpacing(10)

		has_filters = any((
			Dynamic.py_date_start,
			Dynamic.py_date_end,
			Dynamic.word_tags_list,
			Dynamic.favs_tag_enabled,
			Dynamic.no_subfolders_tag_enabled,
		))

		if has_filters:
			self.scroll_layout.addWidget(USep())
			self.scroll_layout.addSpacing(10)
			self.tags_widget = TagsWidget()
			self.tags_widget.open_filters_win.connect(self.open_filters_win.emit)
			self.tags_widget.load_st_grid.connect(self.load_st_grid.emit)
			self.scroll_layout.addWidget(self.tags_widget)

		self.grid_wid = TransparentFrame()
		self.scroll_layout.addWidget(self.grid_wid)
		self.grid_lay = QGridLayout(self.grid_wid)
		self.grid_lay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

		self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self.viewport())

		self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

	# --- Приложения ---

	def _on_apps_found(self, apps: dict[str, str]):
		# слот вызывается в GUI-потоке (сигнал пришёл из пула через очередь)
		self._image_apps = apps

	# --- Выделение ---

	@property
	def selected_widgets(self) -> list[Thumb]:
		"""Список выделенных виджетов в порядке выделения (для внешнего кода)."""
		return list(self._sel)

	def _add_sel(self, wid: Thumb):
		if wid not in self._sel:
			self._sel[wid] = None
			wid.set_frame()

	def _remove_sel(self, wid: Thumb):
		if wid in self._sel:
			del self._sel[wid]
			wid.set_no_frame()

	def clear_selected_widgets(self):
		"""
		- Убирает стиль выделенных виджетов
		- Очищает выделение
		"""
		for w in self._sel:
			w.set_no_frame()
		self._sel.clear()

	def wid_to_selected_widgets(self, wid: Thumb):
		if isinstance(wid, Thumb):
			self._add_sel(wid)

	def select_by_url(self, path: str):
		if path in self.url_to_wid:
			wid = self.url_to_wid.get(path)
			self.clear_selected_widgets()
			self.wid_to_selected_widgets(wid)

	# --- Геометрия ---

	def get_grid_spacing(self):
		if JsonData.square_thumbs:
			return 1
		else:
			return Static.GRID_SPACINGS[Dynamic.current_pixmap_size_index]

	def get_max_columns(self):
		spacing = self.get_grid_spacing()
		first = next(iter(self.url_to_wid.values()), None)
		if first is None:
			return 1
		self.grid_lay.activate()
		thumb_w = first.width() + spacing
		total_w = self.viewport().width() - spacing * 2
		if thumb_w <= 0 or total_w <= 0:
			return 1
		return max(1, total_w // thumb_w)

	# @Utils.timed("rearrange")
	def rearrange(self):
		spacing = self.get_grid_spacing()
		self.grid_lay.setSpacing(spacing)
		max_col = self.get_max_columns()
		count = len(self.url_to_wid)

		# раскладку переписываем только если поменялись колонки или состав сетки
		if max_col == self._layout_cols and count == self._layout_count:
			self._refresh_visible()
			QTimer.singleShot(0, self._fill_if_needed)
			return

		self.grid_wid.hide()
		self._cols = max_col
		self.ordered = list(self.url_to_wid.values())
		self.cell_to_wid.clear()
		for x, thumb in enumerate(self.ordered):
			row, col = divmod(x, max_col)
			self.cell_to_wid[row, col] = thumb
			thumb.idx, thumb.row, thumb.col = x, row, col
			self.grid_lay.addWidget(thumb, row, col)
		self._layout_cols = max_col
		self._layout_count = count
		self.grid_wid.show()
		self._refresh_visible()
		QTimer.singleShot(0, self._fill_if_needed)

	# @Utils.timed("refresh visible")
	def _refresh_visible(self):
		"""Ставит картинку только миниатюрам из видимого диапазона строк."""
		if not self.ordered or self._cols <= 0:
			return

		first_w = self.ordered[0]
		row_h = first_w.height() + self.grid_lay.verticalSpacing()
		if row_h <= 0:
			return

		# видимая часть вьюпорта в координатах grid_wid
		top = self.verticalScrollBar().value() - self.grid_wid.y()
		bottom = top + self.viewport().height()

		total_rows = (len(self.ordered) + self._cols - 1) // self._cols
		row_from = max(0, top // row_h - 1)              # запас в одну строку сверху
		row_to = min(total_rows - 1, bottom // row_h + 1)  # и снизу

		for row in range(row_from, row_to + 1):
			for col in range(self._cols):
				wid = self.cell_to_wid.get((row, col))
				if wid is not None:
					wid.set_pixmap_with_actual_size()

	# @Utils.timed("resize thumbnails")
	def resize_thumbnails(self):
		# только перезапускаем таймер: сама работа идёт после остановки слайдера
		self._size_timer.start(self._size_debounce_ms)

	# @Utils.timed("finish resize")
	def _finish_resize(self):
		# слайдер остановился: один раз масштабируем и перекладываем сетку
		Thumb.fast_scale = False
		self.thumb_cls.calculate_size()
		for wid in self.url_to_wid.values():
			wid.set_text_and_size()
		self.grid_lay.setSpacing(self.get_grid_spacing())
		self.rearrange()

	def clear_grid(self):
		"""Удаляет все виджеты сетки (при полной перезагрузке)."""
		for w in self.url_to_wid.values():
			self.grid_lay.removeWidget(w)
			w.deleteLater()
		self.url_to_wid.clear()
		self.cell_to_wid.clear()
		self.ordered = []
		self._sel.clear()
		self.wid_under_mouse = None
		self._cols = 1
		self._layout_cols = -1
		self._layout_count = -1

	# --- Дозагрузка ---

	# @Utils.timed("check scroll value")
	def checkScrollValue(self, value: int):
		self.up_btn.setVisible(value > 0)
		self._refresh_visible()
		self._fill_if_needed()

	def _content_bottom(self) -> int:
		"""Нижняя граница сетки в координатах scroll_wid."""
		last = self.ordered[-1]
		return self.grid_wid.y() + last.geometry().bottom()

	def _visible_bottom(self) -> int:
		"""Нижняя граница видимой части в тех же координатах."""
		return self.verticalScrollBar().value() + self.viewport().height()

	# @Utils.timed("fill if needed")
	def _fill_if_needed(self):
		if self._loading_more or self._exhausted or not self.ordered:
			self._fill_retries = 0
			return

		last = self.ordered[-1]

		# геометрия ещё не готова: повторяем проверку, а не решаем по старым данным
		if self.grid_wid.height() <= 0 or last.height() <= 0:
			if self._fill_retries < 20:
				self._fill_retries += 1
				QTimer.singleShot(30, self._fill_if_needed)
			return

		self._fill_retries = 0
		self.scroll_layout.activate()
		self.grid_lay.activate()

		if self._content_bottom() - self._visible_bottom() <= 50:
			self._loading_more = True
			self.load_more_thumbnails()

	# --- Клавиатура ---

	def _navigate(self, key):
		"""Перемещает выделение по линейному индексу."""
		if not self.ordered:
			return
		steps = {
			Qt.Key.Key_Right: 1,
			Qt.Key.Key_Left: -1,
			Qt.Key.Key_Down: self._cols,
			Qt.Key.Key_Up: -self._cols,
		}
		step = steps.get(key)
		if step is None:
			return

		cur = next(reversed(self._sel)).idx if self._sel else 0
		new_idx = min(max(cur + step, 0), len(self.ordered) - 1)
		target = self.ordered[new_idx]

		self.clear_selected_widgets()
		self._add_sel(target)
		self.ensureWidgetVisible(target)
		self.wid_under_mouse = target

	def keyPressEvent(self, event: QKeyEvent | None) -> None:
		def remove_files():
			self.remove_files.emit(
				[i.data_item.rel_path for i in self.selected_widgets]
			)

		def open_info():
			"""Открывает окно информации для выбранных виджетов."""
			if self._sel:
				rel_paths = [self.wid_under_mouse.data_item.rel_path, ]
				self.open_info_win.emit(rel_paths)

		def select_all():
			"""Выделяет все виджеты в сетке."""
			for wid in self.ordered:
				self._add_sel(wid)

		def open_last_selected():
			"""Открывает просмотр последнего выбранного виджета."""
			if self._sel:
				self.open_img_view.emit()

		# --- Основная логика ---
		CTRL = Qt.KeyboardModifier.ControlModifier
		NAVI_KEYS = (
			Qt.Key.Key_Left, Qt.Key.Key_Right,
			Qt.Key.Key_Up, Qt.Key.Key_Down,
		)

		if event.modifiers() == CTRL and event.key() == Qt.Key.Key_Backspace:
			if self._sel:
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
		elif event.key() in NAVI_KEYS:
			self._navigate(event.key())

		super().keyPressEvent(event)

	# --- Мышь ---

	def get_clicked_widget(self, a0) -> None | Thumb:
		# позиция из события, а не из QCursor.pos(): работает и для контекстного меню
		if isinstance(a0, QMouseEvent):
			pos = a0.globalPosition().toPoint()
		else:
			pos = a0.globalPos()
		wid = QApplication.widgetAt(pos)
		if isinstance(wid, (ThumbImgWidget, ThumbFilenameWid)):
			return wid.parent()
		else:
			return None

	def handle_rubber_band_selection(self, rect: QRect, ctrl: bool):
		# один раз переводим прямоугольник резинки в координаты grid_wid
		rect_g = QRect(self.grid_wid.mapFrom(self.viewport(), rect.topLeft()), rect.size())
		hits = [w for w in self.ordered if rect_g.intersects(w.geometry())]

		if not ctrl:
			self.clear_selected_widgets()
		for w in hits:
			if ctrl and w in self._sel:
				self._remove_sel(w)
			else:
				self._add_sel(w)

	def handle_shift_click(self):
		anchor = next(reversed(self._sel))
		target = self.wid_under_mouse
		lo, hi = sorted((anchor.idx, target.idx))
		for w in self.ordered[lo:hi + 1]:
			self._add_sel(w)

	def handle_control_click(self):
		w = self.wid_under_mouse
		if w in self._sel:
			self._remove_sel(w)
		else:
			self._add_sel(w)

	def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
		if a0.button() != Qt.MouseButton.LeftButton:
			return

		if self.rubberBand.isVisible():
			rect = QRect(self.origin_pos, a0.pos()).normalized()
			self.rubberBand.hide()
			self.handle_rubber_band_selection(rect, a0.modifiers() == Qt.KeyboardModifier.ControlModifier)
			return

		self.wid_under_mouse = self.get_clicked_widget(a0)

		if not self.wid_under_mouse:
			self.clear_selected_widgets()
			return

		modifiers = a0.modifiers()
		if modifiers == Qt.KeyboardModifier.ShiftModifier and self._sel:
			self.handle_shift_click()
		elif modifiers == Qt.KeyboardModifier.ControlModifier:
			self.handle_control_click()
		else:
			self.clear_selected_widgets()
			self._add_sel(self.wid_under_mouse)

	def position_up_btn(self):
		vp = self.viewport()

		self.up_btn.move(
			vp.width() - self.up_btn.width() - 20,
			vp.height() - self.up_btn.height() - 20
		)

	def resizeEvent(self, a0: QResizeEvent | None) -> None:
		super().resizeEvent(a0)
		self.resize_timer.stop()
		self.resize_timer.start(self.resize_ms)
		QTimer.singleShot(0, self.position_up_btn)

	def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
		"""Создаёт контекстное меню для пустой области или выбранных виджетов."""
		self.menu_ = UMenu(parent=self)
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
			if not self._sel:
				self._add_sel(clicked)
			elif clicked not in self._sel:
				self.clear_selected_widgets()
				self._add_sel(clicked)

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
				open_menu = UMenu(
					title=f"{Lng.open_in[JsonData.lng_index]}",
					parent=self.menu_
				)
				act = QAction(Lng.open_default[JsonData.lng_index], open_menu)
				act.triggered.connect(
					lambda: self.open_in_app.emit((rel_paths, None))
				)
				open_menu.addAction(act)
				open_menu.addSeparator()

				# список уже найден в фоне; пока сканирование не закончилось, будет только «По умолчанию»
				for app_path, basename in self._image_apps.items():
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

			act = RemoveFiles(self.menu_, len(self._sel))
			act.triggered.connect(
				lambda: self.remove_files.emit(rel_paths)
			)
			self.menu_.addAction(act)

			self.menu_.addSeparator()

		if not clicked_wid:
			menu_empty()
		else:
			menu_widget(clicked_wid)

		self.menu_.show_menu_under_cursor(a0)

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
		except AttributeError as e:
			print("Grid mousemove attr error", e)
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
			if self.wid_under_mouse and self.wid_under_mouse not in self._sel:
				self.clear_selected_widgets()
				self._add_sel(self.wid_under_mouse)

			# собираем пути выбранных изображений
			paths = []
			avaiable_mf_path = Mf.current_mf.get_avaiable_mf_path()
			if avaiable_mf_path:
				Mf.current_mf.set_mf_current_path(avaiable_mf_path)
				paths = [
					Utils.add_mf_path(Mf.current_mf.mf_current_path, wid.data_item.rel_path)
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
		self._load_id = 0              # номер текущего запроса к БД
		self._tasks: dict[int, DbImagesLoader] = {}  # держим ссылки на работающие задачи
		self._empty_lbl: TransparentLabel | None = None
		self.load_db_images_task(reset=True)

	def load_more_thumbnails(self):
		if self._exhausted:
			self._loading_more = False
			return
		Dynamic.loaded_thumbs += Static.THUMBS_LOAD_LIMIT
		self.load_db_images_task(reset=False)

	def load_db_images_task(self, reset: bool = True):
		self._load_id += 1
		lid = self._load_id
		task = DbImagesLoader()
		# лямбда без receiver'а выполняется в потоке GUI, поэтому виджеты создаются безопасно
		task.sigs.finished_.connect(
			lambda items, lid=lid, reset=reset: self._on_loaded(items, lid, reset)
		)
		self._tasks[lid] = task
		UThreadPool.start(task)

	def _on_loaded(self, items: list[DbImagesLoaderItem], load_id: int, reset: bool):
		self._tasks.pop(load_id, None)
		if load_id != self._load_id:
			# результат устарел, сбрасываем флаг, иначе дозагрузка заблокируется
			self._loading_more = False
			return
		if reset:
			self.clear_grid()
			self._exhausted = False
		if not items:
			self._exhausted = True
		self.create_thumbnails(items)

	def clear_grid(self):
		super().clear_grid()
		if self._empty_lbl is not None:
			self._empty_lbl.deleteLater()
			self._empty_lbl = None

	# @Utils.timed("create_thumbnails")
	def create_thumbnails(self, db_images: list[DbImagesLoaderItem]):
		self.thumb_cls = SquareThumb if JsonData.square_thumbs else Thumb
		self.thumb_cls.calculate_size()

		self.grid_wid.setUpdatesEnabled(False)
		try:
			for image_item in db_images:
				# при догрузке уже созданные миниатюры не пересоздаём
				if image_item.rel_img_path in self.url_to_wid:
					continue

				data_item = DataItem(
					base_qimage=image_item.base_qimage,
					resized_qimages=image_item.resized_qimages,
					rel_thumb_path=image_item.rel_thumb_path,
					rel_path=image_item.rel_img_path,
					fav=image_item.fav,
					day_month_year=image_item.day_month_year,
					hour_min_sec=image_item.hour_min_sec,
					filename=os.path.basename(image_item.rel_img_path)
				)
				thumbnail = self.thumb_cls(data_item)
				thumbnail.set_no_frame()
				self.url_to_wid[thumbnail.data_item.rel_path] = thumbnail
		finally:
			self.grid_wid.setUpdatesEnabled(True)

		self._loading_more = False

		if not self.url_to_wid:
			self.grid_wid.hide()
			self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
			self.scroll_layout.addStretch(1)
			self._empty_lbl = TransparentLabel(Lng.no_photo[JsonData.lng_index])
			self.scroll_layout.addWidget(self._empty_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
			self.scroll_layout.addStretch(1)
		else:
			self.rearrange()
		self.finished_.emit()

	def dragEnterEvent(self, a0):
		a0.acceptProposedAction()
		return super().dragEnterEvent(a0)

	def dropEvent(self, a0):

		if not a0.mimeData().hasUrls() or a0.source() is not None:
			return

		elif Dynamic.search_words_list:
			return

		paths: list[str] = [
			i.toLocalFile().rstrip(os.sep)
			for i in a0.mimeData().urls()
			if os.path.isfile(i.toLocalFile())
		]

		if paths:
			self.upload_files.emit(paths)
		return super().dropEvent(a0)