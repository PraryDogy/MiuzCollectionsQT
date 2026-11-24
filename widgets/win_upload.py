from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtWidgets import QWidget

from cfg import Static
from system.lang import Lng

from ._base_widgets import ConfirmWin, TransparentLabel, WrapLabel


class UploadWin(ConfirmWin):
	WIDTH = 300

	def __init__(self, dest: str):
		super().__init__(Lng.upload_files_description, "blue", "blue")
		self.setWindowTitle(Lng.upload_files)

		self._dest = dest

		self.dest_widget = WrapLabel(dest)
		self.dest_widget.set_style("regular", "regular", "regular")
		self.dest_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.text_layout.addWidget(self.dest_widget)

		self.confirm_btn.setText(Lng.upload)
