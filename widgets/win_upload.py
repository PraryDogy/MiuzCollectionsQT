from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtWidgets import QWidget

from cfg import Static
from system.lang import Lng

from ._base_widgets import ConfirmWindow, TransparentLabel


class UploadWin(ConfirmWindow):
	# WIDTH = 320

	def __init__(self, dest: str):
		super().__init__(
			text=Lng.upload_files_description,
			confirm_btn="blue",
			icon="blue"
		)
		self.setWindowTitle(Lng.upload_files)

		self._dest = dest

		descr = self.description_label
		idx = self.central_layout.indexOf(descr) + 1

		self.dest_widget = TransparentLabel(dest)
		self.dest_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.dest_widget.set_style("regular", "small", "regular")
		self.dest_widget.setWordWrap(True)
		self.dest_widget.set_selectable(True)
		self.central_layout.insertWidget(idx, self.dest_widget)

		self.confirm_btn.setText(Lng.upload)
		self.fit_label(self.dest_widget)