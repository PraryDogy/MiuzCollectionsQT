import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import ProcessWorker

from ._base_widgets import (ActiveButton, GrayTextLabel, MfPathWidget, SuperConfirmWindow, 
							TitleTextLabel, TransparentWidget, UMainWindow, UPushButton)
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
		self.setWindowTitle(Lng.no_connection[JsonData.lng_index])
		
		self.show_titlebar_sep()
		
		self.central_layout.setContentsMargins(10, 10, 10, 10)
		self.central_layout.setSpacing(15)

		# --- Шапка окна (иконка + заголовок + серое описание) ---
		header_wid = TransparentWidget()
		header_lay = QHBoxLayout(header_wid)
		header_lay.setContentsMargins(0, 0, 0, 0)
		header_lay.setSpacing(15)

		icon = QSvgWidget(str(Static.COMMON_ICONS / "yellow_warning.svg"))
		icon.setFixedSize(40, 40)
		# Прижимаем иконку к верхнему краю, чтобы она стояла ровно напротив заголовка
		header_lay.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)

		text_cont = TransparentWidget()
		text_lay = QVBoxLayout(text_cont)
		text_lay.setContentsMargins(0, 0, 0, 0)
		text_lay.setSpacing(2)

		# Жестко прописали заголовок, как ты и просил
		title_str = "Каталог изображений недоступен" if JsonData.lng_index == 0 else "Image catalog is unavailable"
		title_lbl = TitleTextLabel(title_str)
		title_lbl.setWordWrap(True)
		text_lay.addWidget(title_lbl)

		# Формируем описание: "Имя каталога" — Сетевой диск не подключен...
		descr_text = f"\"{mf.mf_alias}\" — {Lng.network_error_text[JsonData.lng_index].lower()}"
		descr_lbl = GrayTextLabel(descr_text)
		descr_lbl.setWordWrap(True)
		text_lay.addWidget(descr_lbl)

		header_lay.addWidget(text_cont)

		self.central_layout.addWidget(header_wid)

		# --- Виджет пути ---
		self.path_widget = MfPathWidget(JsonData.lng_index, mf.mf_current_path)
		self.central_layout.addWidget(self.path_widget)

		# --- Кнопки ---
		btns_wid = TransparentWidget()
		self.central_layout.addWidget(btns_wid)
		btns_lay = QHBoxLayout(btns_wid)
		btns_lay.setContentsMargins(0, 0, 0, 0)
		btns_lay.setSpacing(10)

		# Добавили кнопку "Серверы" слева
		servers_btn_text = "Серверы" if JsonData.lng_index == 0 else "Servers"
		self.servers_btn = UPushButton(servers_btn_text)
		self.servers_btn.setIcon(QIcon(str(Static.COMMON_ICONS / "hdd.svg")))
		self.servers_btn.clicked.connect(self.open_servers)
		btns_lay.addWidget(self.servers_btn)

		btns_lay.addStretch()
		
		cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
		cancel_btn.clicked.connect(self.deleteLater)
		btns_lay.addWidget(cancel_btn)
		
		btn_text = "Применить" if JsonData.lng_index == 0 else "Apply"
		self.ok_btn = ActiveButton(btn_text)
		self.ok_btn.clicked.connect(self.ok_cmd)
		btns_lay.addWidget(self.ok_btn)

		# Чуть-чуть расширили окно, чтобы комфортно влезли 3 кнопки
		# self.setFixedWidth(420)
		self.adjustSize()
		# self.setFixedHeight(self.height())

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
