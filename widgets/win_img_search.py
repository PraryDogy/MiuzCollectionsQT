import os
from multiprocessing import shared_memory

import numpy as np
from PyQt6.QtCore import QStandardPaths, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QStackedWidget,
                             QVBoxLayout)

from cfg import Dynamic, Static
from system.image_reader import ImageReader
from system.items import ImageArrayItem, Mf
from system.lang import Lng
from system.multiprocess import ProcessWorker, ImageArrayItemLoader
from system.runnable import BlurImgBgTask, ImageSearcher, UThreadPool

from ._base_widgets import (ActiveButton, TitleWidget,
                            TransparentFrame, TransparentLabel,
                            TransparentWidget, UGroupBox, UMainWindow, UMenu,
                            UPushButton, USlider)

DROP_WIDGET_SIZE = (350, 300)


class ProgressWin(UMainWindow):
	stop_img_search = pyqtSignal()

	def __init__(self):
		super().__init__()

		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.image_search)
		self.show_titlebar_sep()

		self.stop_icon = QIcon(str(Static.GRAY_ICONS / "square.svg"))

		self.text_container = TransparentWidget()
		self.central_layout.addWidget(self.text_container)
		self.h_lay = QHBoxLayout(self.text_container)
		self.h_lay.setContentsMargins(0, 0, 0, 0)
		self.h_lay.setSpacing(10)

		self.svg_icon = QSvgWidget(str(Static.COLOR_ICONS / "clock.svg"))
		self.svg_icon.setFixedSize(40, 40)
		self.h_lay.addWidget(self.svg_icon, alignment=Qt.AlignmentFlag.AlignVCenter)

		self.labels_container = TransparentWidget()
		self.labels_layout = QVBoxLayout(self.labels_container)
		self.labels_layout.setContentsMargins(0, 0, 0, 0)
		self.labels_layout.setSpacing(3)
		self.h_lay.addWidget(self.labels_container)

		self.labels_layout.addStretch()

		self.please_wait_label = TransparentLabel(Lng.please_wait)
		self.please_wait_label.set_style("regular", "regular", "bold")
		self.labels_layout.addWidget(self.please_wait_label)

		self.text_label = TransparentLabel("")
		self.text_label.set_style("gray", "regular", "regular")
		self.labels_layout.addWidget(self.text_label)

		self.labels_layout.addStretch()

		self.cancel_btn = UPushButton(Lng.cancel)
		# self.cancel_btn.setIcon(self.stop_icon)
		self.cancel_btn.clicked.connect(self.stop_img_search.emit)
		self.central_layout.addWidget(self.cancel_btn)

		max_ = 99999
		self.set_text(max_, max_)
		self.text_label.adjustSize()
		self.text_label.setFixedWidth(self.text_label.width())

		self.adjustSize()
		self.setFixedSize(self.width(), self.height())

	def set_text(self, current_count, total_count):
		if current_count > total_count:
			current_count = total_count

		if total_count == 0:
			text = Lng.preparing
		else:
			text = (
				f"{Lng.indexing} "
				f"{current_count} "
				f"{Lng.from_} "
				f"{total_count}"
			)

		self.text_label.setText(text)

	def progress_stop_cmd(self):
		# пользователь отменил поиск: останавливаем и возвращаем окно поиска
		self.stop_img_search()
		self.show_main_window()

	def show_main_window(self):
		if not self.isVisible():
			self.show()
			self.raise_()
			self.activateWindow()

	def closeEvent(self, a0):
		a0.ignore()


class SliderWidget(TransparentWidget):
	def __init__(self):
		super().__init__()

		base_value = 30
		self.current_value = base_value

		self.h_layout = QHBoxLayout(self)
		self.h_layout.setContentsMargins(0, 0, 0, 0)
		self.h_layout.setSpacing(10)

		self.slider = USlider()
		self.slider.setOrientation(
			Qt.Orientation.Horizontal
		)
		self.slider.setMinimum(0)
		self.slider.setMaximum(100)
		self.slider.setValue(base_value)

		self.h_layout.addWidget(self.slider)

		self.value_label = TransparentLabel(
			f"{base_value}%"
		)
		self.h_layout.addWidget(self.value_label)

		self.slider.clicked.connect(
			self.slider_clicked_cmd
		)

	def slider_clicked_cmd(self, value: int):
		self.value_label.setText(f"{value}%")
		self.current_value = value


class ImageDropFrame(TransparentFrame):
	"""Общая логика приёма изображения: перетаскивание, клик и контекстное меню.

	Подсвечивает зону (свойство active), если файл подходит,
	и отклоняет всё остальное.
	"""
	image_dropped = pyqtSignal(str)
	reset_requested = pyqtSignal()
	# в контекстном меню показывать пункт «Сброс» (включается в наследниках)
	show_reset = False
	# папка последнего выбранного файла, общая для всех зон
	_last_dir: str = ""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setAcceptDrops(True)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

	def _set_active(self, value: bool):
		self.setProperty("active", value)
		self.style().unpolish(self)
		self.style().polish(self)

	@staticmethod
	def _path_from_mime(mime) -> str | None:
		if not mime.hasUrls():
			return None
		path = mime.urls()[0].toLocalFile().rstrip(os.sep)
		return path if path.endswith(ImageReader.ext_all) else None

	def dragEnterEvent(self, a0):
		if self._path_from_mime(a0.mimeData()):
			a0.acceptProposedAction()
			self._set_active(True)
		else:
			a0.ignore()

	def dragLeaveEvent(self, a0):
		self._set_active(False)

	def dropEvent(self, a0):
		self._set_active(False)
		path = self._path_from_mime(a0.mimeData())
		if path is None:
			a0.ignore()
			return
		a0.acceptProposedAction()
		self.image_dropped.emit(path)

	def mouseReleaseEvent(self, a0):
		if a0.button() == Qt.MouseButton.LeftButton:
			self._open_file_dialog()
		super().mouseReleaseEvent(a0)

	def contextMenuEvent(self, a0):
		menu = UMenu(parent=self)

		choose = QAction(Lng.choose_another_image, menu)
		choose.triggered.connect(lambda: self._open_file_dialog())
		menu.addAction(choose)

		if self.show_reset:
			menu.addSeparator()
			reset = QAction(Lng.reset, menu)
			reset.triggered.connect(lambda: self.reset_requested.emit())
			menu.addAction(reset)

		menu.show_menu_under_cursor(a0)

	def _open_file_dialog(self):
		if not ImageDropFrame._last_dir:
			ImageDropFrame._last_dir = QStandardPaths.writableLocation(
				QStandardPaths.StandardLocation.DownloadLocation
			)

		file_filter = "Images (" + " ".join(f"*{ext}" for ext in ImageReader.ext_all) + ")"
		path, _ = QFileDialog.getOpenFileName(self, "", ImageDropFrame._last_dir, file_filter)
		if not path:
			return

		ImageDropFrame._last_dir = os.path.dirname(path)
		if path.endswith(ImageReader.ext_all):
			self.image_dropped.emit(path)


class WinImgSearchDropWidget(ImageDropFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setFixedSize(*DROP_WIDGET_SIZE)

		self.v_layout = QVBoxLayout(self)
		self.v_layout.setContentsMargins(10, 10, 10, 10)
		self.v_layout.setSpacing(0)
		self.v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.svg_widget = QSvgWidget(str(Static.COLOR_ICONS / "image.svg"))
		self.svg_widget.setFixedSize(50, 50)
		self.v_layout.addWidget(
			self.svg_widget,
			alignment=Qt.AlignmentFlag.AlignCenter,
		)

		self.v_layout.addSpacing(5)

		self.first_row_label = TransparentLabel("")
		self.first_row_label.set_style("gray", "regular", "regular")
		self.first_row_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.v_layout.addWidget(
			self.first_row_label,
			alignment=Qt.AlignmentFlag.AlignCenter,
		)

		self.second_row_label = TransparentLabel("")
		self.second_row_label.set_style("gray", "regular", "regular")
		self.second_row_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.v_layout.addWidget(
			self.second_row_label,
			alignment=Qt.AlignmentFlag.AlignCenter,
		)

		self.show_default()

	def show_loading(self, file_name: str):
		self.first_row_label.setText(Lng.loading)
		self.second_row_label.setText(file_name)
		self.second_row_label.set_elide(True, ignore_width=False)
		self.svg_widget.load(str(Static.COLOR_ICONS / "loading.svg"))

	def show_default(self):
		self.first_row_label.setText(f"{Lng.catalog}: \"{Mf.current_mf.mf_alias}\"",)
		self.second_row_label.setText(Lng.image_search_drop)
		self.second_row_label.set_elide(False)
		self.svg_widget.load(str(Static.COLOR_ICONS / "image.svg"))


class WinImgSearchPreviewWidget(ImageDropFrame):
	pixmap_finished = pyqtSignal()
	show_reset = True

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setFixedSize(*DROP_WIDGET_SIZE)

		# номер текущей загрузки: результаты старых задач игнорируются
		self._generation = 0
		self.pixmap = QPixmap()
		self.image_label = TransparentLabel(Lng.loading)
		self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		layout.addWidget(self.image_label)

	def set_pixmap(self, img_array: np.ndarray):
		generation = self._generation

		def finished(qimage: QImage):
			# пришёл результат для изображения, которое уже заменили: игнорируем
			if generation != self._generation:
				return
			self.pixmap = QPixmap.fromImage(qimage)
			self.image_label.setPixmap(self.pixmap)
			self.pixmap_finished.emit()

		self.qimage_task = BlurImgBgTask(
			img=img_array,
			size=DROP_WIDGET_SIZE,
			radius=8.0
		)
		self.qimage_task.sigs.finished_.connect(finished)
		UThreadPool.start(self.qimage_task)

	def clear(self):
		self._generation += 1
		self.pixmap = QPixmap()
		self.image_label.clear()


class ControlsWidget(TransparentWidget):
	reset_btn_clicked = pyqtSignal()
	slider_moved = pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.v_layout = QVBoxLayout(self)
		self.v_layout.setContentsMargins(5, 5, 5, 5)
		self.v_layout.setSpacing(5)

		title = TitleWidget(Lng.accuracy, Lng.accuracy_descr)
		self.v_layout.addWidget(title)

		self.slider_widget = SliderWidget()
		self.v_layout.addWidget(self.slider_widget)


class WinImgSearch(UMainWindow):
	reload_thumbnails = pyqtSignal()
	closed = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.search_window)

		self.img_array = None
		self.img_search_task = None
		self.read_img_task = None
		self.shm = None
		self.progress_win = None
		self.read_img_poll_ms = 300
		self.magnifier_icon = QIcon(str(Static.GRAY_ICONS / "magnifier.svg"))

		self.found_image_timer = QTimer(self)
		self.found_image_timer.setSingleShot(True)
		self.found_image_timer.timeout.connect(self.reload_thumbnails.emit)
		self.poll_progress_win_timer = QTimer(self)
		self.poll_progress_win_timer.setSingleShot(True)
		self.poll_progress_win_timer.timeout.connect(self.poll_progress_win)
		self.read_img_timer = QTimer(self)
		self.read_img_timer.setSingleShot(True)
		self.read_img_timer.timeout.connect(self.poll_read_img)

		# --- Основной контент внутри UGroupBox ---
		self.content_box = UGroupBox()
		self.content_layout = QVBoxLayout(self.content_box)
		self.content_layout.setContentsMargins(5, 5, 5, 5)
		self.content_layout.setSpacing(10)

		header_widget = TransparentWidget()
		header_layout = QVBoxLayout(header_widget)
		header_layout.setContentsMargins(0, 0, 0, 0)
		header_layout.setSpacing(5)

		self.title_widget = TitleWidget(Lng.image_search, Lng.image_search_descr)
		self.title_widget.set_margins(5, 0, 5, 0)
		header_layout.addWidget(self.title_widget)

		self.content_layout.addWidget(header_widget)

		self.image_stack = QStackedWidget()
		self.drop_widget = WinImgSearchDropWidget()
		self.preview_widget = WinImgSearchPreviewWidget()
		self.preview_widget.pixmap_finished.connect(self.set_close_button_text)
		self.image_stack.addWidget(self.drop_widget)
		self.image_stack.addWidget(self.preview_widget)
		self.image_stack.setCurrentIndex(0)
		self.content_layout.addWidget(self.image_stack, alignment=Qt.AlignmentFlag.AlignCenter)
		# бросок принимают обе зоны: пустая и превью
		self.drop_widget.image_dropped.connect(self.image_dropped)
		self.preview_widget.image_dropped.connect(self.image_dropped)
		self.preview_widget.reset_requested.connect(self.reset_img_search)

		self.controls_widget = ControlsWidget()
		self.content_layout.addWidget(self.controls_widget)

		self.central_layout.addWidget(self.content_box)

		# --- Кнопки под группой ---
		btn_layout = QHBoxLayout()
		self.central_layout.addLayout(btn_layout)
		btn_layout.setContentsMargins(0, 0, 0, 0)
		btn_layout.setSpacing(5)

		reset_btn = UPushButton(Lng.reset)
		reset_btn.clicked.connect(self.reset_img_search)
		btn_layout.addWidget(reset_btn)

		btn_layout.addStretch()

		self.close_button = UPushButton("")
		self.set_close_button_width()
		self.set_close_button_text()
		self.close_button.clicked.connect(self.request_close)
		btn_layout.addWidget(self.close_button)

		self.start_btn = ActiveButton(Lng.find_matches)
		self.start_btn.setIcon(self.magnifier_icon)
		self.start_btn.clicked.connect(self.search_cmd)
		btn_layout.addWidget(self.start_btn)

		self.set_close_button_width()

		self.adjustSize()
		self.setFixedSize(self.width(), self.height())

	def search_cmd(self):
		# нет изображения: просто закрываем окно
		if self.img_array is None:
			self.request_close()
			return

		# есть изображение: запускаем поиск и прячем основное окно на время прогресса
		self.start_img_search()
		self.hide()

	def set_close_button_width(self):
		max_word = max((Lng.close, Lng.hide), key=len)
		self.close_button.setText(max_word)
		self.close_button.adjustSize()
		self.close_button.setFixedWidth(self.close_button.width())

	def set_close_button_text(self):
		if self.preview_widget.pixmap.isNull():
			self.close_button.setText(Lng.close)
		else:
			self.close_button.setText(Lng.hide)

	def image_dropped(self, path: str):
		# новое изображение: старое убираем сразу, показываем загрузку в зоне drop
		self.preview_widget.clear()
		self.drop_widget.show_loading(os.path.basename(path))
		self.image_stack.setCurrentIndex(0)
		self.set_close_button_text()
		self.start_read_img_task(path)

	def reset_img_search(self):
		self.stop_timers_and_tasks()
		self.cleanup_shm()
		self.img_array = None
		self.preview_widget.clear()
		self.image_stack.setCurrentIndex(0)
		self.drop_widget.show_default()
		Dynamic.img_search_thumb_paths.clear()
		self.reload_thumbnails.emit()
		self.set_close_button_text()

	def start_img_search(self):
		if self.img_array is None:
			return
		self.stop_img_search()
		self.img_search_task = ImageSearcher(src_img=self.img_array, similarity_value=self.controls_widget.slider_widget.current_value, mf=Mf.current_mf)
		self.img_search_task.sigs.finished_.connect(self.img_search_finished)
		self.img_search_task.sigs.found_image.connect(self.found_image_cmd)
		Dynamic.img_search_thumb_paths.clear()
		UThreadPool.start(self.img_search_task)
		self.open_progress_win()
		self.poll_progress_win()

	def stop_img_search(self):
		self.poll_progress_win_timer.stop()
		if self.img_search_task is not None:
			try:
				self.img_search_task.stop_task()
			except Exception:
				pass
			self.img_search_task = None
		self.close_progress_win()

	def img_search_finished(self):
		if not Dynamic.img_search_thumb_paths:
			self.found_image_cmd("999999999999")
		self.poll_progress_win_timer.stop()
		if self.progress_win is not None:
			try:
				QTimer.singleShot(1000, self.progress_win.deleteLater)
			except RuntimeError:
				pass
			self.progress_win = None

	def show_main_window(self):
		# возвращаем окно поиска после прогресса; не трогаем, если оно уже закрыто
		if not self.isVisible():
			self.show()
			self.raise_()
			self.activateWindow()

	def open_progress_win(self):
		self.close_progress_win()
		pixmap = self.preview_widget.pixmap
		self.progress_win = ProgressWin()
		self.progress_win.center_to_parent(self)
		self.progress_win.stop_img_search.connect(self.progress_stop_cmd)
		self.progress_win.show()

	def progress_stop_cmd(self):
		# пользователь нажал «Стоп» в окне прогресса: останавливаем поиск и возвращаем окно
		self.stop_img_search()
		self.show_main_window()

	def close_progress_win(self):
		if self.progress_win is not None:
			try:
				self.progress_win.deleteLater()
			except RuntimeError:
				pass
			self.progress_win = None

	def poll_progress_win(self):
		self.poll_progress_win_timer.stop()
		if self.progress_win is None or self.img_search_task is None:
			return
		try:
			self.progress_win.set_text(self.img_search_task.current_count, self.img_search_task.total_count)
			self.poll_progress_win_timer.start(500)
		except RuntimeError:
			self.poll_progress_win_timer.stop()

	def start_read_img_task(self, url: str, ms=300):
		self.cleanup_shm()
		self.read_img_timer.stop()
		if self.read_img_task is not None:
			try:
				self.read_img_task.terminate_join()
			except Exception:
				pass
			self.read_img_task = None
		self.img_array = None
		self.read_img_poll_ms = ms
		self.read_img_task = ProcessWorker(target=ImageArrayItemLoader.start, args=(url, None))
		self.read_img_task.start()
		self.read_img_timer.start(ms)

	def poll_read_img(self):
		self.read_img_timer.stop()
		if self.read_img_task is None:
			return

		# сначала проверяем, жив ли процесс, и только потом очередь:
		# так результат, который процесс положил перед выходом, не потеряется
		is_alive = self.read_img_task.is_alive()

		if not self.read_img_task.process_queue.empty():
			item: ImageArrayItem = self.read_img_task.process_queue.get()
			try:
				self.shm = shared_memory.SharedMemory(name=item.shm_name)
				self.img_array = np.ndarray(item.shape, dtype=np.dtype(item.dtype), buffer=self.shm.buf)
				self.image_stack.setCurrentIndex(1)
				self.drop_widget.show_default()
				self.preview_widget.set_pixmap(self.img_array)

				if item.is_grayscale():
					self.cleanup_shm()
					self.img_array = None
					QTimer.singleShot(1500, self.reset_img_search)

				if not is_alive:
					self.read_img_task.terminate_join()
					self.read_img_task = None
			except Exception:
				self.read_img_failed()
		elif is_alive:
			self.read_img_timer.start(self.read_img_poll_ms)
		else:
			self.read_img_failed()

	def read_img_failed(self):
		self.cleanup_shm()
		self.img_array = None
		if self.read_img_task is not None:
			try:
				self.read_img_task.terminate_join()
			except Exception:
				pass
			self.read_img_task = None

		self.preview_widget.clear()
		self.image_stack.setCurrentIndex(0)
		self.drop_widget.show_default()
		self.set_close_button_text()

	def found_image_cmd(self, rel_path: str):
		Dynamic.img_search_thumb_paths.add(rel_path)
		self.found_image_timer.stop()
		self.found_image_timer.start(500)

	def cleanup_shm(self):
		if self.shm is not None:
			try:
				self.shm.close()
			except Exception:
				pass
			try:
				self.shm.unlink()
			except Exception:
				pass
			self.shm = None

	def stop_timers_and_tasks(self):
		self.found_image_timer.stop()
		self.poll_progress_win_timer.stop()
		self.read_img_timer.stop()
		self.stop_img_search()
		if self.read_img_task is not None:
			try:
				self.read_img_task.terminate_join()
			except Exception:
				pass
			self.read_img_task = None

	def request_close(self):
		self.stop_timers_and_tasks()
		self.closed.emit()

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Escape:
			self.request_close()
			return
		super().keyPressEvent(event)

	def closeEvent(self, event):
		event.ignore()
		self.request_close()