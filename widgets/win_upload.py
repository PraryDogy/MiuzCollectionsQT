import os
from collections import deque
from queue import Empty

import numpy as np
from PyQt6.QtCore import QEvent, QSize, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QAbstractItemView, QFileDialog, QGridLayout,
                             QHBoxLayout, QLabel, QListView, QScrollArea,
                             QSizePolicy, QVBoxLayout)

from cfg import JsonData, Static
from system.items import Mf
from system.lang import Lng
from system.multiprocess import ImageArrayItemLoader, ProcessWorker
from system.runnable import BlurImgBgTask, ImgArrayQImage
from system.utils import Utils

from ._base_widgets import (ActiveButton, ChoosePathWidget, HoverGroupBox,
                            TitleTextWidget, TitleWidget, TransparentLabel,
                            TransparentWidget, UGroupBox, TransparentFrame,
                            UScrollVerticalArea, UMainWindow, UPushButton, USep)
from .grid import GridStandart, SquareThumb


THUMB_SIZE = 100        # размер, который отдаёт загрузчик и занимает квадрат в строке
ICON_SIZE = THUMB_SIZE  # квадрат миниатюры в строке списка
ROW_PADDING = 8         # отступы строки по высоте
THUMB_RADIUS = 8        # скругление углов миниатюры


LOAD_SIZE = 200      # размер, который отдаёт загрузчик
CELL = 100           # размер миниатюры в сетке
SPACING = 10         # расстояние между ячейками
RADIUS = 8           # скругление углов миниатюры


class ImageCell(TransparentWidget):
	"""Миниатюра 100×100 и имя файла под ней."""

	def __init__(self, path: str):
		super().__init__()
		self.setFixedWidth(CELL)

		lay = QVBoxLayout(self)
		lay.setContentsMargins(0, 0, 0, 0)
		lay.setSpacing(4)

		self.pic_label = QLabel()
		self.pic_label.setFixedSize(CELL, CELL)
		self.pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		lay.addWidget(self.pic_label)

		self.name_label = TransparentLabel(os.path.basename(path))
		self.name_label.set_style("gray", "small", "regular")
		self.name_label.set_elide(True)
		self.name_label.setFixedWidth(CELL)
		self.name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
		self.name_label.setToolTip(path)
		lay.addWidget(self.name_label)

	def set_pixmap(self, pixmap: QPixmap | None):
		if pixmap is None or pixmap.isNull():
			self.pic_label.setText("✕")
			return
		self.pic_label.setPixmap(pixmap)


class ImageGridWidget(UScrollVerticalArea):
	"""Сетка миниатюр 100×100. Число колонок зависит от ширины окна.

	Цепочка для каждого файла:
	ImageArrayItemLoader (подпроцесс) -> ImgArrayQImage (пул) -> BlurImgBgTask (пул) -> QPixmap (GUI).
	"""

	def __init__(self, paths: list[str], max_workers: int | None = None):
		super().__init__()
		self.paths = paths
		self.max_workers = max_workers or min(4, os.cpu_count() or 2)
		self._pending = deque(range(len(paths)))
		self._active: dict[int, ProcessWorker] = {}   # загрузка массива
		self._tasks: dict[int, object] = {}           # задачи в пуле потоков
		self._cells: list[ImageCell] = [ImageCell(p) for p in paths]
		self._cols = 0
		self._pool = QThreadPool.globalInstance()

		self.setWidgetResizable(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

		self.container = TransparentFrame()
		self.grid = QGridLayout(self.container)
		self.grid.setContentsMargins(10, 10, 10, 10)
		self.grid.setSpacing(SPACING)
		self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
		self.setWidget(self.container)

		self._relayout()

		self._timer = QTimer(self)
		self._timer.timeout.connect(self._poll)
		self._timer.start(50)
		self._start_next()

	# --- раскладка ---

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self._relayout()

	def _relayout(self):
		"""Пересчитывает число колонок по ширине и перекладывает ячейки."""
		step = CELL + SPACING
		cols = max(1, (self.viewport().width() - 20 + SPACING) // step)
		if cols == self._cols:
			return
		self._cols = cols

		for cell in self._cells:
			self.grid.removeWidget(cell)
		for i, cell in enumerate(self._cells):
			self.grid.addWidget(cell, i // cols, i % cols)

	# --- этап 1: массив в подпроцессе ---

	def _start_next(self):
		while self._pending and len(self._active) < self.max_workers:
			idx = self._pending.popleft()
			worker = ProcessWorker(
				target=ImageArrayItemLoader.start,
				args=(self.paths[idx], LOAD_SIZE),
			)
			worker.start()
			self._active[idx] = worker

	def _poll(self):
		for idx in list(self._active):
			worker = self._active[idx]
			try:
				item = worker.process_queue.get_nowait()
			except Empty:
				if worker.is_alive():
					continue
				try:
					item = worker.process_queue.get(timeout=0.5)
				except Empty:
					item = None

			worker.terminate_join()
			del self._active[idx]

			if item is not None:
				self._run_qimage_task(idx, item.image_array)
			else:
				self._cells[idx].set_pixmap(None)

		self._start_next()

		if not self._active and not self._pending and not self._tasks:
			self._timer.stop()

	# --- этап 2: массив -> QImage в пуле потоков ---

	def _run_qimage_task(self, idx: int, array):
		task = ImgArrayQImage(array)
		task.sigs.finished_.connect(lambda qimage, i=idx: self._on_qimage(i, qimage))
		self._tasks[idx] = task
		self._pool.start(task)

	# --- этап 3: фон и композиция в пуле потоков ---

	def _on_qimage(self, idx: int, qimage):
		self._tasks.pop(idx, None)
		if qimage is None or qimage.isNull():
			self._cells[idx].set_pixmap(None)
			return
		task = BlurImgBgTask(qimage, size=(CELL, CELL), radius=RADIUS)
		task.sigs.finished_.connect(lambda final, i=idx: self._on_final(i, final))
		self._tasks[idx] = task
		self._pool.start(task)

	# --- готовая миниатюра (GUI-поток) ---

	def _on_final(self, idx: int, qimage):
		self._tasks.pop(idx, None)
		if qimage is None or qimage.isNull():
			self._cells[idx].set_pixmap(None)
			return
		self._cells[idx].set_pixmap(QPixmap.fromImage(qimage))

	def stop(self):
		"""Останавливает загрузку. Вызвать в closeEvent окна."""
		self._pending.clear()
		self._timer.stop()
		for worker in self._active.values():
			worker.terminate_join()
		self._active.clear()
		self._tasks.clear()


class ClickablePathWidget(ChoosePathWidget):
	"""Выбор папки: клик открывает диалог, наведение подсвечивает виджет."""
	clicked = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit()
		super().mouseReleaseEvent(event)

	def enterEvent(self, event):
		self.set_hovered(True)
		return super().enterEvent(event)


class UploadWin(UMainWindow):
	ok_clicked = pyqtSignal(str)

	def __init__(self, mf: Mf, current_dir: str, files_to_copy: list[str]):
		super().__init__()
		self.setWindowTitle(Lng.file_loading)
		self.setFixedWidth(430)
		self.set_close_only()
		self.set_always_on_top()

		self.current_dir = (mf.mf_path + current_dir).rstrip(os.sep)

		self.group_box = UGroupBox()
		self.group_layout = QVBoxLayout(self.group_box)
		self.group_layout.setContentsMargins(10, 10, 10, 10)
		self.group_layout.setSpacing(8)
		self.central_layout.addWidget(self.group_box)

		self.title_widget = TitleWidget(
			title=Lng.upload_files,
			descr=Lng.upload_files_description
		)
		self.title_widget.description_widget.setWordWrap(False)
		self.group_layout.addWidget(self.title_widget)

		self.list_widget = ImageGridWidget(files_to_copy)  # абсолютные пути к файлам
		self.group_layout.addWidget(self.list_widget)

		self.path_widget = ClickablePathWidget()
		self.path_widget.set_good(self.current_dir, lng=Lng.chosen_folder)
		self.path_widget.setToolTip(self.current_dir)
		self.path_widget.clicked.connect(self.choose_dir)
		self.group_layout.addWidget(self.path_widget)

		self.button_widget = TransparentWidget()
		self.central_layout.addWidget(self.button_widget)
		self.button_layout = QHBoxLayout(self.button_widget)
		self.button_layout.setContentsMargins(0, 0, 0, 0)
		self.button_layout.setSpacing(5)

		find_catalog_btn = UPushButton(Lng.choose_folder)
		find_catalog_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "magnifier.svg")))
		find_catalog_btn.clicked.connect(self.choose_dir)
		self.button_layout.addWidget(find_catalog_btn)

		self.button_layout.addStretch()

		self.cancel_button = UPushButton(Lng.cancel)
		self.cancel_button.clicked.connect(self.deleteLater)
		self.button_layout.addWidget(self.cancel_button)

		self.ok_button = ActiveButton(Lng.upload)
		self.ok_button.clicked.connect(
			lambda e: self.ok_clicked.emit(self.current_dir)
		)
		self.button_layout.addWidget(self.ok_button)

		self.adjustSize()
		self.setFixedHeight(self.height())

	def choose_dir(self, *_):
		url = QFileDialog.getExistingDirectory(self, "", self.current_dir)
		if url and url != self.current_dir:
			self.current_dir = url.rstrip(os.sep)
			self.path_widget.set_good(self.current_dir, lng=Lng.chosen_folder)
			self.path_widget.setToolTip(self.current_dir)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)

	def dragEnterEvent(self, a0):
		return super().dragEnterEvent(a0)

	def  dragLeaveEvent(self, a0):
		return super().dragLeaveEvent(a0)