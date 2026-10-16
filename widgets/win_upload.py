import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.utils import Utils

from ._base_widgets import (ActiveButton, GrayTextLabel, SvgIconButton,
                            TitleTextLabel, TransparentLabel,
                            TransparentWidget, UGroupBox, UMainWindow,
                            UPushButton, UTagWidget)


class CopyPathButton(SvgIconButton):
	svg_path = Static.COMMON_ICONS / "copy.svg"
	green_mark = Static.COMMON_ICONS / "green_checkmark.svg"
	CLICK_COOLDOWN = 500  # мс

	def __init__(self, current_dir: str):
		super().__init__(self.svg_path, (33, 33), (20, 20))
		self.current_dir = current_dir
		self._click_locked = False

		self._cooldown_timer = QTimer(self)
		self._cooldown_timer.setSingleShot(True)
		self._cooldown_timer.setInterval(self.CLICK_COOLDOWN)
		self._cooldown_timer.timeout.connect(self._unlock_click)

	def _unlock_click(self):
		self._click_locked = False

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			if not self._click_locked:
				self._click_locked = True
				self._cooldown_timer.start()
				Utils.pyqt_copy_text(self.current_dir)
		super().mouseReleaseEvent(event)


class TitleWidget(UGroupBox):
	svg_path = Static.COMMON_ICONS / "upload_file.svg"
	svg_size = (45, 45)

	def __init__(self, files_count: int):
		super().__init__()

		self.h_layout = QHBoxLayout(self)
		self.h_layout.setContentsMargins(10, 10, 10, 10)
		self.h_layout.setSpacing(10)

		self.svg_widget = QSvgWidget()
		self.svg_widget.load(str(self.svg_path))
		self.svg_widget.setFixedSize(*self.svg_size)
		self.h_layout.addWidget(self.svg_widget)

		self.text_container = TransparentWidget()
		self.h_layout.addWidget(self.text_container)
		self.text_layout = QVBoxLayout(self.text_container)
		self.text_layout.setContentsMargins(0, 0, 0, 0)
		self.text_layout.setSpacing(5)

		self.title_label = TitleTextLabel(self.get_plural_text(files_count))
		self.text_layout.addWidget(self.title_label)

		self.description_label = GrayTextLabel(Lng.upload_files_description[JsonData.lng_index])
		self.text_layout.addWidget(self.description_label)

	def get_plural_text(self, count):
		# 1. Определяем, какой кортеж использовать на основе правил русского языка
		if count % 10 == 1 and count % 100 != 11:
			chosen_tuple = Lng.chosen_x_files   # ... 1 файл
		elif 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
			chosen_tuple = Lng.chosen_xx_files  # ... 2-4 файла
		else:
			chosen_tuple = Lng.chosen_xxx_files # ... 5-20 файлов

		# 2. Берем строку под нужный язык и сразу подставляем число
		return chosen_tuple[JsonData.lng_index].format(files_count=count)


class DestinyFolderWidget(UGroupBox):
	dir_changed = pyqtSignal(str)
	copy_path_clicked = pyqtSignal()

	svg_path = Static.COMMON_ICONS / "folder_solid.svg"
	svg_size = (20, 20)

	def __init__(self, current_dir: str):
		super().__init__()
		self.current_dir = current_dir

		self.main_layout = QVBoxLayout(self)
		self.main_layout.setContentsMargins(10, 10, 10, 10)
		self.main_layout.setSpacing(10)

		self.title_container = TransparentWidget()
		self.main_layout.addWidget(self.title_container)
		self.title_layout = QHBoxLayout(self.title_container)
		self.title_layout.setContentsMargins(0, 0, 0, 0)
		self.title_layout.setSpacing(10)

		self.title_svg = QSvgWidget()
		self.title_svg.load(str(self.svg_path))
		self.title_svg.setFixedSize(*self.svg_size)
		self.title_layout.addWidget(self.title_svg)

		self.title_label = TransparentLabel(Lng.dest_folder[JsonData.lng_index])
		self.title_layout.addWidget(self.title_label)

		self.path_row = TransparentWidget()
		self.path_row_layout = QHBoxLayout(self.path_row)
		self.path_row_layout.setContentsMargins(0, 0, 0, 0)
		self.path_row_layout.setSpacing(10)

		self.main_layout.addWidget(self.path_row)

		# GroupBox с путём
		self.path_container = UGroupBox()
		self.path_row_layout.addWidget(self.path_container, 1)

		self.path_layout = QHBoxLayout(self.path_container)
		self.path_layout.setContentsMargins(10, 2, 10, 2)
		self.path_layout.setSpacing(10)

		self.path_svg = QSvgWidget()
		self.path_svg.load(str(self.svg_path))
		self.path_svg.setFixedSize(*self.svg_size)
		# self.path_layout.addWidget(self.path_svg)

		self.path_label = TransparentLabel(self.current_dir)
		self.path_label.set_elide(True)
		self.path_layout.addWidget(self.path_label, 1)

		self.copy_path_button = CopyPathButton(self.current_dir)
		self.copy_path_button.clicked_.connect(self.copy_path_clicked.emit)
		self.path_layout.addWidget(self.copy_path_button)

		# Кнопка вне GroupBox
		self.change_btn = UPushButton(Lng.change[JsonData.lng_index])
		self.change_btn.clicked.connect(self.change_dir)
		self.path_row_layout.addWidget(self.change_btn)

	def change_dir(self):
		self.file_dialog = QFileDialog()
		self.file_dialog.setDirectory(self.current_dir)
		url = self.file_dialog.getExistingDirectory()
		if url and url != self.current_dir:
			url = url.rstrip()
			self.current_dir = url
			self.path_label.setText(self.current_dir)
			self.dir_changed.emit(self.current_dir)
			self.copy_path_button.current_dir = self.current_dir


class NotiWidget(UTagWidget):
	svg_path = Static.COMMON_ICONS / "checkmark.svg"

	def __init__(self):
		super().__init__(
			Lng.text_copied[JsonData.lng_index],
			self.qss_green,
			str(self.svg_path),
			None
		)
		self.adjustSize()


class UploadWin(UMainWindow):
	ok_clicked = pyqtSignal(str)

	def __init__(self, mf: Mf, current_dir: str, files_to_copy: list[str]):
		super().__init__()
		self.setWindowTitle(Lng.file_loading[JsonData.lng_index])
		self.setFixedWidth(500)
		self.set_close_only()
		self.set_always_on_top()

		self.current_dir = (mf.mf_paths[0] + current_dir).rstrip(os.sep)

		self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
		self.central_layout.setContentsMargins(10, 5, 10, 10)
		self.central_layout.setSpacing(10)

		self.title_widget = TitleWidget(len(files_to_copy))
		self.central_layout.addWidget(self.title_widget)

		self.destiny_widget = DestinyFolderWidget(self.current_dir)
		self.destiny_widget.dir_changed.connect(self.dir_changed_cmd)
		self.destiny_widget.copy_path_clicked.connect(self.copy_path_clicked_cmd)
		self.central_layout.addWidget(self.destiny_widget)

		self.button_widget = TransparentWidget()
		self.central_layout.addWidget(self.button_widget)
		self.button_layout = QHBoxLayout(self.button_widget)
		self.button_layout.setContentsMargins(0, 0, 0, 0)
		self.button_layout.setSpacing(10)

		self.button_layout.addStretch()

		self.cancel_button = UPushButton(Lng.cancel[JsonData.lng_index])
		self.cancel_button.clicked.connect(self.deleteLater)
		self.button_layout.addWidget(self.cancel_button)

		self.ok_button = ActiveButton(Lng.upload[JsonData.lng_index])
		self.ok_button.clicked.connect(
			lambda e: self.ok_clicked.emit(self.current_dir)
		)
		self.button_layout.addWidget(self.ok_button)

		self.adjustSize()
		self.setFixedHeight(self.height())

		self.noti_widgeet = NotiWidget()
		self.noti_widgeet.setParent(self)
		y = 5
		x = (self.width() - self.noti_widgeet.width()) // 2
		self.noti_widgeet.move(x, y)
		self.noti_widgeet.setVisible(False)

	def copy_path_clicked_cmd(self):
		if not self.noti_widgeet.isVisible():
			self.noti_widgeet.setVisible(True)
			QTimer.singleShot(1000, self.show_noti_widget)

	def show_noti_widget(self):
		try:
			self.noti_widgeet.setVisible(False)
		except RuntimeError:
			# значит окно было удалено раньше чем сработал таймер
			pass

	def dir_changed_cmd(self, path: str):
		self.current_dir = path

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)