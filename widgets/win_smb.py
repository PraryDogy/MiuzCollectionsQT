import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QLayout

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker

from ._base_widgets import (ActiveButton, GrayTextLabel, MfPathWidget, SuperConfirmWindow, 
							TitleTextWidget, TransparentWidget, UMainWindow, UPushButton, UGroupBox)
from .win_servers import ServersWin
from system.servers import Servers


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
		
		# --- Виджет пути ---
		self.path_widget = MfPathWidget(mf)
		self.central_layout.addWidget(self.path_widget)

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

		self.setFixedWidth(380)
		self.adjustSize()
		self.setFixedHeight(self.height())

	def open_servers(self):
		self.servers_win = ServersWin()
		self.servers_win.center_to_parent(self)
		self.servers_win.show()

	def ok_cmd(self):

		def ok_clicked():
			self.mf.mf_paths = [mf_path, ]
			Mf.write_json_data()
			restart_app()

		mf_path = self.path_widget.validate_and_show_win()
		if mf_path:
			self.super_win = SuperConfirmWindow(Lng.confirm_mf_path)
			self.super_win.ok_clicked.connect(ok_clicked)
			self.super_win.center_to_parent(self)
			self.super_win.show()

	def keyPressEvent(self, a0):
		if a0.key() in (Qt.Key.Key_Escape, ):
			self.deleteLater()
		return super().keyPressEvent(a0)

	def deleteLater(self):
		return super().deleteLater()
