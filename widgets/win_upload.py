import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QSizePolicy, QVBoxLayout

from cfg import JsonData, Static
from system.items import Mf
from system.lang import Lng
from system.utils import Utils

from ._base_widgets import (ActiveButton, ChoosePathWidget, HoverGroupBox,
                            TitleTextWidget, TitleWidget, TransparentLabel,
                            TransparentWidget, UGroupBox, UMainWindow,
                            UPushButton, USep, UListWidget, UListWidgetItem)
from .grid import GridStandart, SquareThumb

import os
from collections import deque
from queue import Empty

import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from system.multiprocess import ImageArrayItemLoader, ProcessWorker

from ._base_widgets import TransparentLabel


import os
from collections import deque
from queue import Empty

import numpy as np
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QListView

from system.multiprocess import ImageArrayItemLoader, ProcessWorker


THUMB_SIZE = 200
ICON_SIZE = 64          # размер миниатюры в строке списка


def array_to_pixmap(arr: np.ndarray) -> QPixmap:
	"""Переводит numpy-массив изображения в QPixmap."""
	arr = np.ascontiguousarray(arr, dtype=np.uint8)
	h, w = arr.shape[:2]
	if arr.ndim == 2:
		fmt = QImage.Format.Format_Grayscale8
	elif arr.shape[2] == 4:
		fmt = QImage.Format.Format_RGBA8888
	else:
		fmt = QImage.Format.Format_RGB888
	# copy() отвязывает QImage от буфера, который живёт только в этой функции
	image = QImage(arr.tobytes(), w, h, arr.strides[0], fmt).copy()
	return QPixmap.fromImage(image)


class ImageListWidget(UListWidget):
	"""Список файлов: миниатюра слева, имя справа. Миниатюры грузятся в подпроцессах."""

	def __init__(self, paths: list[str], max_workers: int | None = None):
		super().__init__()
		self.paths = paths
		self.max_workers = max_workers or min(4, os.cpu_count() or 2)
		self._pending = deque()
		self._active: dict[int, ProcessWorker] = {}
		self._items: list[UListWidgetItem] = []

		self.setViewMode(QListView.ViewMode.ListMode)
		self.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
		self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
		self.setSpacing(2)
		self.setWordWrap(False)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

		for idx, path in enumerate(paths):
			item = UListWidgetItem(self, os.path.basename(path))
			item.setToolTip(path)
			item.setSizeHint(QSize(0, ICON_SIZE + 8))
			self.addItem(item)
			self._items.append(item)
			self._pending.append(idx)

		self._timer = QTimer(self)
		self._timer.timeout.connect(self._poll)
		self._timer.start(50)
		self._start_next()

	def _start_next(self):
		while self._pending and len(self._active) < self.max_workers:
			idx = self._pending.popleft()
			worker = ProcessWorker(
				target=ImageArrayItemLoader.start,
				args=(self.paths[idx], THUMB_SIZE),
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
				try:
					pixmap = array_to_pixmap(item.image_array)
					self._items[idx].setIcon(QIcon(pixmap))
				except Exception:
					pass

		self._start_next()

		if not self._active and not self._pending:
			self._timer.stop()

	def stop(self):
		"""Останавливает загрузку. Вызвать в closeEvent окна."""
		self._pending.clear()
		self._timer.stop()
		for worker in self._active.values():
			worker.terminate_join()
		self._active.clear()


class DestinyFolderWidget(HoverGroupBox):
	dir_changed = pyqtSignal(str)

	def __init__(self, current_dir: str, files_to_copy):
		super().__init__()
		self.current_dir = current_dir
		self.copy_path_btn_locked = False

		self.setCursor(Qt.CursorShape.PointingHandCursor)

		# внешний горизонтальный layout: контент слева, стрелка справа
		main_lay = QHBoxLayout(self)
		main_lay.setContentsMargins(10, 5, 10, 5)
		main_lay.setSpacing(10)

		# левая часть: заголовок, путь и описание
		content = TransparentWidget()
		content_lay = QVBoxLayout(content)
		content_lay.setContentsMargins(0, 0, 0, 0)
		content_lay.setSpacing(5)

		self.path_status = ChoosePathWidget()
		content_lay.addWidget(self.path_status)
		self.path_status.set_good(self.current_dir, lng=Lng.chosen_folder)
		self.setToolTip(self.current_dir)

		# правая часть: стрелка по центру по вертикали
		self.change_dir_svg = QSvgWidget(str(Static.GRAY_ICONS / "arrow_right.svg"))
		self.change_dir_svg.setFixedSize(15, 15)

		main_lay.addWidget(content)
		main_lay.addWidget(self.change_dir_svg)

	def change_dir(self):
		self.file_dialog = QFileDialog()
		self.file_dialog.setDirectory(self.current_dir)
		url = self.file_dialog.getExistingDirectory()
		if url and url != self.current_dir:
			url = url.rstrip(os.sep)
			self.current_dir = url
			self.dir_changed.emit(self.current_dir)
			self.path_status.set_good(self.current_dir, lng=Lng.chosen_folder)
			self.setToolTip(self.current_dir)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.change_dir()
		return super().mouseReleaseEvent(event)

	def enterEvent(self, a0):
		super().enterEvent(a0)
		self.path_status.set_hovered(True)

	def leaveEvent(self, a0):
		super().leaveEvent(a0)
		self.path_status.set_hovered(False)



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
			sep=False
		)
		self.group_layout.addWidget(self.title_widget)

		self.list_widget = ImageListWidget(files_to_copy)  # абсолютные пути к файлам
		self.group_layout.addWidget(self.list_widget)

		self.destiny_widget = DestinyFolderWidget(self.current_dir, files_to_copy)
		self.destiny_widget.dir_changed.connect(self.dir_changed_cmd)
		self.group_layout.addWidget(self.destiny_widget)

		self.button_widget = TransparentWidget()
		self.central_layout.addWidget(self.button_widget)
		self.button_layout = QHBoxLayout(self.button_widget)
		self.button_layout.setContentsMargins(0, 0, 0, 0)
		self.button_layout.setSpacing(5)

		find_catalog_btn = UPushButton(Lng.choose_folder)
		find_catalog_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "magnifier.svg")))
		find_catalog_btn.clicked.connect(self.destiny_widget.change_dir)
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

	def dir_changed_cmd(self, path: str):
		self.current_dir = path

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)