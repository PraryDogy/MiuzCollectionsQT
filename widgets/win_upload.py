from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget

from system.lang import Lng
from cfg import Static
from ._base_widgets import ActiveButton, UPushButton, UMainWindow, WrapLabel, TransparentLabel


class UploadWin(UMainWindow):
	WIDTH = 280
	ok_clicked = pyqtSignal()

	def __init__(self, parent, dest):
		super().__init__(parent)
		self.setWindowTitle(Lng.upload_files)
		self.central_layout.setSpacing(0)

		self.svg_widget = QSvgWidget(str(Static.COLOR_ICONS / "info.svg"))
		self.svg_widget.setFixedSize(70, 70)
		self.central_layout.addWidget(self.svg_widget)

		self.descr = TransparentLabel(Lng.upload_files_description)
		self.descr.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.central_layout.addWidget(self.descr)

		self.dest_widget = WrapLabel(self, dest)
		self.dest_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.dest_widget.set_style("regular", "regular", "bold")
		self.central_layout.addWidget(self.dest_widget)

		self.ok_btn = ActiveButton(Lng.upload)
		self.ok_btn.clicked.connect(self.ok_clicked.emit)
		self.central_layout.addWidget(self.ok_btn)

		self.cancel_btn = UPushButton(Lng.cancel)
		self.cancel_btn.clicked.connect(self.deleteLater)
		self.central_layout.addWidget(self.cancel_btn)

		self.fix_window_height()

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)