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

	def __init__(self, mf: Mf):
		super().__init__()
		self.mf = mf
		self._user_control = False   # пользователь выбрал путь (обзор или drop)
		self._dialog_open = False    # диалог обзора открыт прямо сейчас
		self._closing = False

		self.set_close_only()
		self.set_always_on_top()
		self.setWindowTitle(Lng.attention)

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
		RootProbe.signals.done.connect(self._on_root_done)

		self.setFixedWidth(450)
		self.adjustSize()
		self.setFixedHeight(self.height())

		self._poll = QTimer(self)
		self._poll.setInterval(1500)
		self._poll.timeout.connect(self._tick)
		self._poll.start()

	# ---------- сигналы ----------

	def _tick(self):
		# запрашиваем состояние; если проверка уже идёт, RootProbe её не дублирует
		if RootProbe.check(self.mf.mf_path) is True:
			self._on_root_done(self.mf.mf_path, True)

	def _on_user_busy(self, busy: bool):
		self._dialog_open = busy

	def _on_user_changed(self):
		# changed эмитится только из update_path: после обзора или drop
		self._user_control = True

	def _on_root_done(self, path: str, ok: bool):
		if not ok or path != self.mf.mf_path:
			return
		# выбор пользователя важнее автоматического закрытия
		if self._user_control or self._dialog_open:
			return
		self._finish(restart=True)

	# ---------- закрытие ----------

	def _finish(self, restart: bool):
		if self._closing:
			return
		self._closing = True
		self._poll.stop()
		self._disconnect_root_done()
		if restart:
			self.restart_scaner.emit()
		self.deleteLater()

	def _disconnect_root_done(self):
		try:
			RootProbe.signals.done.disconnect(self._on_root_done)
		except (TypeError, RuntimeError):
			pass  # уже отключено

	def closeEvent(self, a0):
		self._disconnect_root_done()
		super().closeEvent(a0)

	def deleteLater(self):
		self._disconnect_root_done()
		super().deleteLater()

	# ---------- действия ----------

	def open_servers(self):
		self.servers_win = ServersWin()
		self.servers_win.center_to_parent(self)
		self.servers_win.show()

	def ok_cmd(self):
		new_path = self.path_widget.validate_and_show_win()
		if not new_path:
			return  # путь не выбран или не существует: сканировать нечего

		if new_path != self.mf.mf_path:
			self.mf.old_mf_path = self.mf.mf_path  # текущий путь становится старым
			self.mf.mf_path = new_path             # новый путь становится текущим
			Mf.write_json_data()

		# скан запускается в любом случае, полный проход только при смене пути
		self._finish(restart=True)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self._finish(restart=False)
			return
		super().keyPressEvent(a0)