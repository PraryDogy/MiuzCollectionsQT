from system.lang import Lng

from ._base_widgets import ConfirmWindow, TransparentLabel


class UploadWin(ConfirmWindow):
	def __init__(self, dest: str):
		txt = Lng.upload_files_description[:-1] + ":"
		super().__init__(txt)

		descr = self.description_label
		# self.adjust_window_size_single_line(descr, descr.text())

		idx = self.icon_text_layout.indexOf(descr)
		idx = idx + 1

		self.dest_widget = TransparentLabel(dest)
		self.dest_widget.set_style("regular", "regular", "bold")
		self.dest_widget.setWordWrap(True)
		self.dest_widget.set_selectable(True)
		self.icon_text_layout.insertWidget(idx, self.dest_widget)
		self.adjust_window_size(self.dest_widget, dest)
