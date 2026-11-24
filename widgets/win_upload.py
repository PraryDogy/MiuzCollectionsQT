from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtWidgets import QWidget

from cfg import Static
from system.lang import Lng

from ._base_widgets import ConfirmWin, TransparentLabel


class UploadWin(ConfirmWin):
	# WIDTH = 320

	def __init__(self, dest: str):
		super().__init__(Lng.upload_files_description, "blue", "blue")
		self.setWindowTitle(Lng.upload_files)

		self._dest = dest

		descr = self.description_label
		idx = self.central_layout.indexOf(descr) + 1

		self.dest_widget = TransparentLabel(dest)
		self.add_text_label(self.dest_widget)
		self.dest_widget.set_style("regular", "small", "regular")
		self.dest_widget.set_selectable(True)

		self.confirm_btn.setText(Lng.upload)