import os
from datetime import datetime
from queue import Empty

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPixmap
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QSpacerItem, QVBoxLayout

from cfg import JsonData, Static
from system.items import DataItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import OneFileInfo, OneFileInfoItem, ProcessWorker
from system.shared_utils import SharedUtils
from system.utils import Utils

from ._base_widgets import (ActiveButton, GrayTextLabel, TransparentLabel,
                            TransparentWidget, UGroupBox, UMainWindow,
                            UPushButton)
from system.tasks import BlurImgBgTask, UThreadPool


MAX_SIZE = 250


class WinInfoSelectableLabel(TransparentLabel):
	def __init__(self, text: str):
		super().__init__(text)
		self.set_selectable(True)

	def contextMenuEvent(self, ev):
		if not self.selectedText():
			self.setSelection(0, len(self.text()))
		super().contextMenuEvent(ev)


class WinInfo(UMainWindow):
	POLL_MS = 100

	def __init__(self, data_item: DataItem):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.info)

		self.labels: dict[str, WinInfoSelectableLabel] = {}
		self.data_item = data_item
		self.abs_path = Utils.add_mf_path(
			mf_path=Mf.current_mf.mf_paths[0],
			rel_path=self.data_item.rel_path
		)

		self.central_layout.setContentsMargins(10, 0, 10, 10)
		self.central_layout.setSpacing(10)

		self.build_img_wid()
		self.create_qimage()
		self._build_info()
		self._build_buttons()
		self._load_info()

		self.setMinimumWidth(400)

		# Высоту берём из раскладки, ширину не трогаем: sizeHint() по ширине
		# у elided-лейблов завышен и тянет окно к длине пути
		self.centralWidget().layout().activate()
		height = self.centralWidget().sizeHint().height()
		self.resize(400, height)
		self.setFixedHeight(height)

	def build_img_wid(self):
		self.img_wid = TransparentLabel("")
		self.img_wid.setFixedSize(MAX_SIZE, MAX_SIZE)
		# Добавление в раскладку выполняется в _build_info, внутри группы

	def create_qimage(self):

		def fin(qimage):
			qpixmap = QPixmap.fromImage(qimage)
			self.img_wid.setPixmap(qpixmap)

		size = (MAX_SIZE, MAX_SIZE)
		self.qimage_task = BlurImgBgTask(self.data_item.base_qimage, size)
		self.qimage_task.sigs.finished_.connect(fin)
		UThreadPool.start(self.qimage_task)


	def _build_info(self):
		wid = UGroupBox()
		self.central_layout.addWidget(wid)

		outer_lay = QVBoxLayout(wid)
		outer_lay.setContentsMargins(10, 10, 10, 10)
		outer_lay.setSpacing(10)

		outer_lay.addWidget(self.img_wid, alignment=Qt.AlignmentFlag.AlignCenter)

		self.grid_lay = QGridLayout()
		self.grid_lay.setSpacing(5)
		self.grid_lay.setContentsMargins(0, 0, 0, 0)
		outer_lay.addLayout(self.grid_lay)

		rows = [
			("name", Lng.file_name, os.path.basename(self.abs_path)),
			("type", Lng.type_, Lng.calculating),
			("size", Lng.file_size, Lng.calculating),
			("location", Lng.location, self.abs_path),
			("changed", Lng.changed, Lng.calculating),
			("resol", Lng.resol, Lng.calculating),
		]

		l_fl = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop

		for row, (key, caption, value) in enumerate(rows):
			left_lbl = GrayTextLabel(caption + ":")
			right_lbl = WinInfoSelectableLabel(value)
			for i in left_lbl, right_lbl:
				i.set_font_size(11)

			right_lbl.set_elide(True, ignore_width=False)

			self.grid_lay.addWidget(left_lbl, row, 0, alignment=l_fl)
			self.grid_lay.addItem(QSpacerItem(15, 0), row, 1)
			self.grid_lay.addWidget(right_lbl, row, 2)
			self.labels[key] = right_lbl

		# Правая колонка забирает всё оставшееся место окна
		self.grid_lay.setColumnStretch(2, 1)

	def _build_buttons(self):
		widget = TransparentWidget()
		self.central_layout.addWidget(widget)

		layout = QHBoxLayout(widget)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(5)
		layout.addStretch()

		copy_btn = UPushButton(Lng.copy_filepath)
		copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.path))
		layout.addWidget(copy_btn)

		close_btn = ActiveButton(Lng.close)
		close_btn.clicked.connect(self.close)
		layout.addWidget(close_btn)

	def _load_info(self):
		self.workers: dict[str, ProcessWorker] = {
			"info": ProcessWorker(target=OneFileInfo.start, args=(self.abs_path,)),
			"res": ProcessWorker(target=OneFileInfo.start_res, args=(self.abs_path,)),
		}
		self.task_timer = QTimer(self)
		self.task_timer.setSingleShot(True)
		self.task_timer.timeout.connect(self.poll)

		for worker in self.workers.values():
			worker.start()
		self.task_timer.start(self.POLL_MS)

	def poll(self):
		for key in list(self.workers):
			worker = self.workers[key]

			# Флаг снимаем до чтения очереди: результат, положенный перед выходом
			# процесса, гарантированно будет прочитан в этом же проходе
			alive = worker.is_alive()

			try:
				value = worker.process_queue.get_nowait()
				if key == "info":
					self.apply_info(value)
				else:
					self.apply_res(value)
			except Empty:
				pass

			if not alive:
				worker.terminate_join()
				del self.workers[key]

		if self.workers:
			self.task_timer.start(self.POLL_MS)

	def apply_info(self, info_item: OneFileInfoItem | None):
		if info_item is None:
			for key in ("type", "size", "changed"):
				self.labels[key].setText("—")
			return

		self.labels["type"].setText(f"{Lng.image} {info_item.ext}")
		self.labels["size"].setText(SharedUtils.get_f_size(info_item.size_bytes))
		self.labels["changed"].setText(self.format_mod(info_item.mtime))

	def apply_res(self, res: str | None):
		self.labels["resol"].setText(res or "—")

	@staticmethod
	def format_mod(mtime: float) -> str:
		# Lng доступен только в главном потоке, поэтому форматируем здесь
		dt = datetime.fromtimestamp(mtime)
		month = Lng.months_gen[str(dt.month)]
		return f"{dt.day} {month} {dt.year} {dt:%H:%M:%S}"

	def keyPressEvent(self, ev: QKeyEvent):
		if ev.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
			self.close()
			return
		super().keyPressEvent(ev)

	def closeEvent(self, ev):
		self.task_timer.stop()
		for worker in self.workers.values():
			worker.terminate_join()
		self.workers.clear()
		super().closeEvent(ev)
