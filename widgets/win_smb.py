from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout

from cfg import Static
from system.items import Mf, RootProbe, Servers
from system.lang import Lng

from ._base_widgets import (ActiveButton, MfPathWidget, QVBoxLayout,
                            TitleTextWidget, TransparentWidget, UGroupBox,
                            UMainWindow, UPushButton)
from .win_servers import ServersWin


class WinSmb(UMainWindow):
	restart_scaner = pyqtSignal()
	CHECK_MS = 1500

	def __init__(self, mf: Mf):
		super().__init__()
		self.mf = mf
		self._user_control = False  # пользователь выбрал путь (обзор или drop)
		self._dialog_open = False   # диалог обзора открыт прямо сейчас
		self._closing = False

		self.set_close_only()
		self.set_always_on_top()
		self.setWindowTitle(Lng.attention)

		main_wrapper = UGroupBox()
		self.central_layout.addWidget(main_wrapper)
		wrapper_lay = QVBoxLayout(main_wrapper)
		wrapper_lay.setContentsMargins(5, 10, 5, 10)
		wrapper_lay.setSpacing(10)

		wrapper_lay.addWidget(TitleTextWidget(mf.mf_alias, Static.COLOR_ICONS / "image_folder.svg"))

		self.path_widget = MfPathWidget(mf)
		wrapper_lay.addWidget(self.path_widget)

		btns_wid = TransparentWidget()
		self.central_layout.addWidget(btns_wid)
		btns_lay = QHBoxLayout(btns_wid)
		btns_lay.setContentsMargins(0, 0, 0, 0)
		btns_lay.setSpacing(5)

		if Servers.items:
			self.servers_btn = UPushButton(Lng.connections)
			self.servers_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "connections.svg")))
			self.servers_btn.clicked.connect(self.open_servers)
			btns_lay.addWidget(self.servers_btn)

		btns_lay.addStretch()

		cancel_btn = UPushButton(Lng.cancel)
		cancel_btn.clicked.connect(lambda: self._finish(restart=False))
		btns_lay.addWidget(cancel_btn)

		self.ok_btn = ActiveButton(Lng.apply)
		self.ok_btn.clicked.connect(self.ok_cmd)
		btns_lay.addWidget(self.ok_btn)

		self.path_widget.user_busy.connect(self._on_user_busy)
		self.path_widget.changed.connect(self._on_user_changed)

		self._timer = QTimer(self)
		self._timer.timeout.connect(self._tick)
		self._timer.start(self.CHECK_MS)

		self.setFixedWidth(450)
		self.adjustSize()
		self.setFixedHeight(self.height())

	def _on_user_busy(self, busy: bool):
		self._dialog_open = busy

	def _on_user_changed(self):
		# changed эмитится только из update_path: после обзора или drop
		self._user_control = True

	def _tick(self):
		# каталог вернулся сам, и пользователь ничего не выбирал: закрываем
		if self._user_control or self._dialog_open:
			return
		if RootProbe.is_available(self.mf.mf_path):
			self._finish(restart=True)

	def _finish(self, restart: bool):
		if self._closing:
			return
		self._closing = True
		self._timer.stop()
		if restart:
			self.restart_scaner.emit()
		self.deleteLater()

	def closeEvent(self, a0):
		self._finish(restart=False)
		super().closeEvent(a0)

	def open_servers(self):
		self.servers_win = ServersWin()
		self.servers_win.center_to_parent(self)
		self.servers_win.show()

	def ok_cmd(self):
		new_path = self.path_widget.validate_and_show_win()
		if not new_path:
			return

		if new_path != self.mf.mf_path:
			self.mf.old_mf_path = self.mf.mf_path
			self.mf.mf_path = new_path
			Mf.write_json_data()

		self._finish(restart=True)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self._finish(restart=False)
			return
		super().keyPressEvent(a0)