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
                            UPushButton, USep)
from .grid import GridStandart, SquareThumb




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

		self.title_widget = TitleWidget(
			title=Lng.upload_files,
			descr=Lng.upload_files_description
		)
		self.title_widget.description_widget.setWordWrap(False)
		content_lay.addWidget(self.title_widget)

		content_lay.addSpacing(5)

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

		self.destiny_widget = DestinyFolderWidget(self.current_dir, files_to_copy)
		self.destiny_widget.dir_changed.connect(self.dir_changed_cmd)
		self.central_layout.addWidget(self.destiny_widget)

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