from system.lang import Lng
from PyQt6.QtCore import Qt
from ._base_widgets import ConfirmWindow, TransparentLabel


class UploadWin(ConfirmWindow):
	# WIDTH = 320

	def __init__(self, dest: str):
		super().__init__(Lng.upload_files_description)

		descr = self.description_label

		idx = self.central_layout.indexOf(descr)
		idx = idx + 1

		self.dest_widget = TransparentLabel(dest)
		self.dest_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.dest_widget.set_style("regular", "small", "regular")
		self.dest_widget.setWordWrap(True)
		self.dest_widget.set_elide(True)
		self.dest_widget.set_selectable(True)

		self.central_layout.insertWidget(idx, self.dest_widget)
		# self.central_layout.insertSpacing(idx + 1, 5)
		# self.fit_label(self.description_label)
