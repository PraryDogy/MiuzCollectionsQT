from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtWidgets import QWidget

from cfg import Static
from system.lang import Lng

from ._base_widgets import ConfirmWin, TransparentLabel, WrapLabel


class UploadWin(ConfirmWin):
	WIDTH = 300

	def __init__(self, parent, dest: str):
		super().__init__(parent, Lng.upload_files_description, "blue", "blue")
		self.setFixedWidth(self.WIDTH)
		self.setWindowTitle(Lng.upload_files)
		self.setToolTip(dest)

		self._dest = dest

		self.dest_widget = WrapLabel(dest)
		self.dest_widget.hide()
		self.dest_widget.fit_to_width(self.WIDTH - 40)
		self.dest_widget.set_style("regular", "regular", "regular")
		self.dest_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.text_layout.addWidget(self.dest_widget)
		self.dest_widget.show()

		self.confirm_btn.setText(Lng.upload)
