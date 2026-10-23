import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.utils import Utils

from ._base_widgets import (ActiveButton, GrayTextLabel, TitleTextLabel,
                            TransparentLabel, TransparentWidget, UGroupBox,
                            UMainWindow, UPushButton, USep)


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
	copy = Static.COMMON_ICONS / "copy.svg"
	magnifier = Static.COMMON_ICONS / "magnifier.svg"
	svg_path = Static.COMMON_ICONS / "folder_solid.svg"
	green_checkmark = Static.COMMON_ICONS / "green_checkmark.svg"
	svg_size = (20, 20)

	def __init__(self, current_dir: str):
		super().__init__()
		self.current_dir = current_dir
		self.copy_path_btn_locked = False

		self.main_layout = QVBoxLayout(self)
		self.main_layout.setContentsMargins(10, 10, 10, 10)
		self.main_layout.setSpacing(5)

		self.title_label = TitleTextLabel(Lng.dest_folder[JsonData.lng_index], str(self.svg_path))
		self.main_layout.addWidget(self.title_label)

		# с обычным spacing виджет под сепаратором будет как бы дальше
		# из-за высоты кнопки, поэтому заголовок над сепаратором
		# ощущается ближе к сепаратору, для этого мы добавляем смещение
		self.main_layout.addSpacing(3)
		self.main_layout.addWidget(USep())

		self.path_row = TransparentWidget()
		self.path_row_layout = QHBoxLayout(self.path_row)
		self.path_row_layout.setContentsMargins(0, 0, 0, 0)
		self.path_row_layout.setSpacing(10)
		self.main_layout.addWidget(self.path_row)

		self.path_label = GrayTextLabel(self.current_dir)
		self.path_label.set_elide(True)
		self.path_row_layout.addWidget(self.path_label, 1)

		self.copy_path_button = UPushButton("")
		self.copy_path_button.setIcon(QIcon(str(self.copy)))
		self.copy_path_button.clicked.connect(self.copy_path)
		self.path_row_layout.addWidget(self.copy_path_button)

		# Кнопка вне GroupBox
		self.change_btn = UPushButton(Lng.choose_folder[JsonData.lng_index])
		self.change_btn.setIcon(QIcon(str(self.magnifier)))
		self.change_btn.clicked.connect(self.change_dir)
		self.main_layout.addWidget(self.change_btn)

	def copy_path(self):

		def unlock():
			self.copy_path_btn_locked = False
			self.copy_path_button.setIcon(QIcon(str(self.copy)))

		if self.copy_path_btn_locked:
			return
		Utils.pyqt_copy_text(self.current_dir)
		self.copy_path_button.setIcon(QIcon(str(self.green_checkmark)))
		self.copy_path_btn_locked = True
		QTimer.singleShot(1000, unlock)

	def change_dir(self):
		self.file_dialog = QFileDialog()
		self.file_dialog.setDirectory(self.current_dir)
		url = self.file_dialog.getExistingDirectory()
		if url and url != self.current_dir:
			url = url.rstrip(os.sep)
			self.current_dir = url
			self.path_label.setText(self.current_dir)
			self.dir_changed.emit(self.current_dir)
			self.copy_path_button.current_text = self.current_dir


class UploadWin(UMainWindow):
	ok_clicked = pyqtSignal(str)

	def __init__(self, mf: Mf, current_dir: str, files_to_copy: list[str]):
		super().__init__()
		self.setWindowTitle(Lng.file_loading[JsonData.lng_index])
		self.setFixedWidth(450)
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

	def dir_changed_cmd(self, path: str):
		self.current_dir = path

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)