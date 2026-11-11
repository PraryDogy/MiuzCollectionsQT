import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QHBoxLayout

from cfg import Static
from system.database import Dirs
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker
from system.servers import Servers

from ._base_widgets import (ActiveButton, GrayTextLabel, MfPathWidget,
                            QVBoxLayout, TitleTextWidget,
                            TransparentWidget, UGroupBox, UMainWindow,
                            UPushButton)
from .win_servers import ServersWin


def restart_app():
	ProcessWorker.stop_all() 
	os.execl(sys.executable, sys.executable, *sys.argv)
	QApplication.exit(0)


class WinSmb(UMainWindow):
	def __init__(self, mf: Mf):
		super().__init__()
		self.mf = mf
		self.set_close_only()
		self.set_always_on_top()
		self.setWindowTitle(Lng.attention)

		# Делаем отступы аккуратными
		self.central_layout.setContentsMargins(10, 5, 10, 10)
		self.central_layout.setSpacing(10)

		main_wrapper = UGroupBox()
		self.central_layout.addWidget(main_wrapper)
		wrapper_lay = QVBoxLayout(main_wrapper)
		wrapper_lay.setContentsMargins(5, 10, 5, 10)
		wrapper_lay.setSpacing(10)

		title_widget = TitleTextWidget(mf.mf_alias, Static.COLOR_ICONS / "image_folder.svg")
		wrapper_lay.addWidget(title_widget)

		# --- Виджет пути ---
		self.path_widget = MfPathWidget(mf)
		wrapper_lay.addWidget(self.path_widget)

		# --- Кнопки ---
		btns_wid = TransparentWidget()
		self.central_layout.addWidget(btns_wid)
		btns_lay = QHBoxLayout(btns_wid)
		btns_lay.setContentsMargins(0, 0, 0, 0)
		btns_lay.setSpacing(10)

		if Servers.items:

			self.servers_btn = UPushButton(Lng.connections)
			self.servers_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "connections_gray.svg")))
			self.servers_btn.clicked.connect(self.open_servers)
			btns_lay.addWidget(self.servers_btn)

		btns_lay.addStretch()
		
		cancel_btn = UPushButton(Lng.cancel)
		cancel_btn.clicked.connect(self.deleteLater)
		btns_lay.addWidget(cancel_btn)
		
		self.ok_btn = ActiveButton(Lng.apply)
		self.ok_btn.clicked.connect(self.ok_cmd)
		btns_lay.addWidget(self.ok_btn)

		self.setFixedWidth(450)
		self.adjustSize()
		self.setFixedHeight(self.height())

	def open_servers(self):
		self.servers_win = ServersWin()
		self.servers_win.center_to_parent(self)
		self.servers_win.show()

	def ok_cmd(self):
		new_path = self.path_widget.validate_and_show_win()
		if not new_path:
			return

		if new_path == self.mf.mf_path:
			self.deleteLater()
			return

		self.mf.old_mf_path = self.mf.mf_path  # текущий путь становится старым
		self.mf.mf_path = new_path             # новый путь становится текущим
		Mf.write_json_data()
		restart_app()


	def keyPressEvent(self, a0):
		if a0.key() in (Qt.Key.Key_Escape, ):
			self.deleteLater()
		return super().keyPressEvent(a0)

	def deleteLater(self):
		return super().deleteLater()
