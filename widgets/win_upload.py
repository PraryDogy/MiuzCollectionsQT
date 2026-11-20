import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QVBoxLayout

from cfg import Static
from system.items import Mf
from system.lang import Lng

from ._base_widgets import (ActiveButton, ChoosePathWidget, TitleWidget,
                            TransparentWidget, UGroupBox, UMainWindow,
                            UPushButton, UTreeWidget, UTreeWidgetItem)

MIN_WIDTH = 430         # минимальная ширина окна
LIST_HEIGHT = 160       # высота списка файлов, дальше прокрутка


def format_size(size: int) -> str:
	"""Переводит размер в байтах в строку вида '2.4 МБ'."""
	value = float(size)
	for unit in ("Б", "КБ", "МБ"):
		if value < 1024:
			return f"{value:.0f} {unit}" if unit == "Б" else f"{value:.1f} {unit}"
		value /= 1024
	return f"{value:.1f} ГБ"


class ClickablePathWidget(ChoosePathWidget):
	"""Выбор папки: клик открывает диалог, наведение подсвечивает виджет."""
	clicked = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit()
		super().mouseReleaseEvent(event)

	def enterEvent(self, event):
		self.set_hovered(True)
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.set_hovered(False)
		super().leaveEvent(event)


class UploadWin(UMainWindow):
	ok_clicked = pyqtSignal(str)

	def __init__(self, mf: Mf, current_dir: str, files_to_copy: list[str]):
		super().__init__()
		self.setWindowTitle(Lng.file_loading)
		self.set_close_only()
		self.set_always_on_top()

		self.current_dir = (mf.mf_path + current_dir).rstrip(os.sep)

		self.group_box = UGroupBox()
		self.group_layout = QVBoxLayout(self.group_box)
		self.group_layout.setContentsMargins(10, 10, 10, 10)
		self.group_layout.setSpacing(8)
		self.central_layout.addWidget(self.group_box)

		title = TitleWidget(title=Lng.upload_files, descr=Lng.upload_files_description)
		title.description_widget.setWordWrap(False)
		self.group_layout.addWidget(title)

		self.files_widget = self._build_files_list(files_to_copy)
		self.group_layout.addWidget(self.files_widget)

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
		self.ok_button.clicked.connect(lambda *_: self.ok_clicked.emit(self.current_dir))
		self.button_layout.addWidget(self.ok_button)

		self.setMinimumWidth(MIN_WIDTH)
		self.adjustSize()
		self.setFixedHeight(self.height())

	def _build_files_list(self, paths: list[str]) -> UTreeWidget:
		"""Таблица из двух колонок: имя слева, размер справа. Превью не грузятся."""
		widget = UTreeWidget()
		widget.setColumnCount(2)
		widget.setRootIsDecorated(False)
		widget.setIndentation(0)
		widget.setSelectionMode(UTreeWidget.SelectionMode.NoSelection)
		widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
		widget.setFixedHeight(LIST_HEIGHT)

		header = widget.header()
		header.setStretchLastSection(False)
		header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
		header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

		for path in paths:
			try:
				size = os.path.getsize(path)
			except OSError:
				size = 0

			# элемент добавляется в дерево в конструкторе, отдельный addTopLevelItem не нужен
			item = UTreeWidgetItem(widget, [os.path.basename(path), format_size(size)])
			item.setToolTip(0, path)
			item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

		return widget

	def choose_dir(self, *_):
		url = QFileDialog.getExistingDirectory(self, "", self.current_dir)
		if url and url != self.current_dir:
			self.current_dir = url.rstrip(os.sep)
			self.path_widget.set_good(self.current_dir, lng=Lng.chosen_folder)
			self.path_widget.setToolTip(self.current_dir)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		super().keyPressEvent(a0)