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
							TitleTextLabel, TransparentWidget, UMainWindow, UPushButton, USep)
from .win_servers import ServersWin
from system.servers import Servers


def restart_app():
	ProcessWorker.stop_all() 
	os.execl(sys.executable, sys.executable, *sys.argv)
	QApplication.exit(0)


class WinSmb(UMainWindow):
	yellow_warning_path = Static.COMMON_ICONS / "yellow_warning.svg"
	yellow_waring_size = (24, 24)
	connect_svg_path = Static.COMMON_ICONS / "connect.svg"

	def __init__(self, mf: Mf):
		super().__init__()
		self.mf = mf

		self.set_close_only()
		self.set_always_on_top()
		self.setWindowTitle(Lng.attention[JsonData.lng_index])
		
		self.show_titlebar_sep()
		
		# Задаем фиксированную ширину
		self.setFixedWidth(440)
		
		# Делаем отступы аккуратными
		self.central_layout.setContentsMargins(15, 10, 15, 15)
		self.central_layout.setSpacing(5)

		# --- Шапка окна (иконка + заголовок) ---
		header_wid = TransparentWidget()
		header_lay = QHBoxLayout(header_wid)
		header_lay.setContentsMargins(0, 0, 0, 0)
		header_lay.setSpacing(10)

		icon = QSvgWidget()
		icon.load(str(self.yellow_warning_path))
		icon.setFixedSize(*self.yellow_waring_size)
		header_lay.addWidget(icon)

		title_lbl = TitleTextLabel(Lng.catalog_unavaiable[JsonData.lng_index])
		header_lay.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
		
		header_lay.addStretch()
		self.central_layout.addWidget(header_wid)

		# --- Разделитель ---
		# self.central_layout.addWidget(USep())

		descr_lbl = GrayTextLabel(Lng.network_error_text[JsonData.lng_index])
		descr_lbl.setWordWrap(True)
		self.central_layout.addWidget(descr_lbl)

		self.central_layout.addSpacing(5)

		# --- Виджет пути ---
		self.path_widget = MfPathWidget(JsonData.lng_index, mf.mf_current_path)
		self.central_layout.addWidget(self.path_widget)

		self.central_layout.addSpacing(5)

		# --- Кнопки ---
		btns_wid = TransparentWidget()
		self.central_layout.addWidget(btns_wid)
		btns_lay = QHBoxLayout(btns_wid)
		btns_lay.setContentsMargins(0, 0, 0, 0)
		btns_lay.setSpacing(10)

		if Servers.items:

			self.servers_btn = UPushButton(Lng.servers[JsonData.lng_index])
			self.servers_btn.setIcon(QIcon(str(self.connect_svg_path)))
			self.servers_btn.clicked.connect(self.open_servers)
			btns_lay.addWidget(self.servers_btn)

		btns_lay.addStretch()
		
		cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
		cancel_btn.clicked.connect(self.deleteLater)
		btns_lay.addWidget(cancel_btn)
		
		self.ok_btn = ActiveButton(Lng.apply[JsonData.lng_index])
		self.ok_btn.clicked.connect(self.ok_cmd)
		btns_lay.addWidget(self.ok_btn)

		self.adjustSize()
		self.setFixedHeight(self.height())

	def open_servers(self):
		self.servers_win = ServersWin()
		self.servers_win.center_to_parent(self)
		self.servers_win.show()

	def ok_cmd(self):

		def ok_clicked():
			self.mf.mf_paths = [mf_path, ]
			self.mf.mf_current_path = mf_path
			Mf.write_json_data()
			restart_app()

		mf_path = self.path_widget.validate()
		if mf_path:
			self.super_win = SuperConfirmWindow(Lng.confirm_mf_path[JsonData.lng_index])
			self.super_win.ok_clicked.connect(ok_clicked)
			self.super_win.center_to_parent(self)
			self.super_win.show()

	def keyPressEvent(self, a0):
		if a0.key() in (Qt.Key.Key_Escape, ):
			self.deleteLater()
		return super().keyPressEvent(a0)

	def deleteLater(self):
		return super().deleteLater()
