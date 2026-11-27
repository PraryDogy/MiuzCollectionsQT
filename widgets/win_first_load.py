import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

from PyQt6.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy, QVBoxLayout

from cfg import JsonData, Static
from system.items import Mf
from system.lang import Lng
from system.runnable import URunnable, UThreadPool

from ._base_widgets import (ConfirmWin, LightHoverGroupBox, TitleWidget,
                            TransparentWidget, UMenu, UPushButton, TransparentLabel)
from .win_settings import NewMfWin
import json  # добавь в импорты

def restart_app():
	os.execl(sys.executable, sys.executable, *sys.argv)
	QApplication.exit(0)


class ZipTask(URunnable):

	class Sigs(QObject):
		error = pyqtSignal()
		finished = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.sigs = self.Sigs()

	def task(self):
		shutil.rmtree(Static.APP_DATA_DIR, ignore_errors=True)
		try:
			Static.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
			dest = Path(shutil.copy(Static.MIUZ_ZIP, Static.APP_DATA_DIR))
			with ZipFile(dest, "r") as zip_ref:
				zip_ref.extractall(Static.APP_DATA_DIR)
			dest.unlink(missing_ok=True)
		except Exception as e:
			print(f"ZipTask critical error: {e}")
			self.sigs.error.emit()
			return
		self.sigs.finished.emit()


class MiuzGroup(LightHoverGroupBox):
	clicked = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

		# внешний горизонтальный layout: контент слева, кнопка справа
		main_lay = QHBoxLayout(self)
		main_lay.setContentsMargins(10, 5, 10, 5)
		main_lay.setSpacing(10)

		# левая часть: заголовок и описание
		content = TransparentWidget()
		content_lay = QVBoxLayout(content)
		content_lay.setContentsMargins(0, 0, 0, 0)
		content_lay.setSpacing(7)

		title_widget = TitleWidget(
			title="MIUZ Diamonds",
			descr=Lng.miuz_diamonds_descr,
			title_svg=Static.COLOR_ICONS / "miuz.svg",
			sep=False
		)
		title_widget.v_lay.setSpacing(5)
		content_lay.addWidget(title_widget)

		# правая часть: кнопка запуска, по центру по вертикали
		self.start_btn = QSvgWidget(str(Static.GRAY_ICONS / "arrow_right.svg"))
		self.start_btn.setFixedSize(15, 15)

		main_lay.addWidget(content, 1)
		main_lay.addWidget(self.start_btn, 0, Qt.AlignmentFlag.AlignVCenter)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
			self.clicked.emit()
		super().mouseReleaseEvent(event)



class FirstLoadWin(NewMfWin):
	TEMP_FILE = Static.APP_DATA_DIR / "temp_new_mf.json"

	def __init__(self, mf_path = None):
		# читаем временные данные до построения виджетов, чтобы передать путь в базовый класс
		saved = self._read_temp()
		super().__init__(saved.get("mf_path") or mf_path)

		self.setWindowTitle(Static.APP_NAME)

		if saved.get("mf_alias"):
			self.mf_alias_widget.line_edit.setText(saved["mf_alias"])
			self.has_unsaved = True
		
		self.rus_icon = QIcon(str(Static.COLOR_ICONS / "rus_flag.svg"))
		self.eng_icon = QIcon(str(Static.COLOR_ICONS / "eng_flag.svg"))

		if Lng.CURRENT_LNG_INDEX == 0:
			icon = self.rus_icon
		else:
			icon = self.eng_icon

		self.lng_menu = UMenu()

		self.rus_action = QAction(Lng.lng_menu_rus, self.lng_menu)
		self.rus_action.setIcon(self.rus_icon)
		self.rus_action.setIconVisibleInMenu(True)
		self.rus_action.triggered.connect(lambda e: self.change_lang_cmd(0))
		self.lng_menu.addAction(self.rus_action)

		self.eng_action = QAction(Lng.lng_menu_eng, self.lng_menu)
		self.eng_action.setIcon(self.eng_icon)
		self.eng_action.setIconVisibleInMenu(True)
		self.eng_action.triggered.connect(lambda e: self.change_lang_cmd(1))
		self.lng_menu.addAction(self.eng_action)

		self.lng_button = UPushButton("")
		self.lng_button.setMenu(self.lng_menu)
		self.lng_button.setIcon(icon)
		self.lng_button.setIconSize(QSize(18, 18))
		self.lng_button.adjustSize()
		self.lng_button.setFixedWidth(self.lng_button.width() + 10)
		self.main_title_lay.addWidget(self.lng_button)

		if os.path.exists(Static.MIUZ_ZIP):
			idx = self.group_lay.indexOf(self.mf_path_widget) + 1

			self.miuz_wid = MiuzGroup()
			self.miuz_wid.clicked.connect(self.copy_zip_cmd)
			self.group_lay.insertWidget(idx, self.miuz_wid)

		self.setFixedWidth(500)
		self.set_fixed_height_wraps()
		self.setFixedHeight(self.height() + 5) # поправка на кнопку языка в заголовке

	@classmethod
	def _read_temp(cls) -> dict:
		try:
			data = json.loads(cls.TEMP_FILE.read_text(encoding="utf-8"))
		except (OSError, ValueError):
			data = {}
		# файл одноразовый: после чтения удаляем, чтобы старые данные не вернулись
		cls.TEMP_FILE.unlink(missing_ok=True)
		return data if isinstance(data, dict) else {}

	def temp_save(self):
		path = self.mf_path_widget.draft_mf_path
		data = {
			"mf_alias": self.mf_alias_widget.line_edit.text(),
			"mf_path": str(path) if path else None,
		}
		try:
			self.TEMP_FILE.parent.mkdir(parents=True, exist_ok=True)
			self.TEMP_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
		except OSError as e:
			print(f"temp_save: не удалось сохранить черновик: {e}")

	def change_lang_cmd(self, index: int):
		self.temp_save()  # сохраняем черновик до перезапуска
		JsonData.lng_index = index
		JsonData.write_json_data()
		restart_app()

	def copy_zip_cmd(self):

		def fin():
			JsonData.lng_index = Lng.CURRENT_LNG_INDEX
			JsonData.write_json_data()
			restart_app()

		self.copy_task = ZipTask()
		self.copy_task.sigs.finished.connect(fin)
		self.hide()
		UThreadPool.init()
		UThreadPool.start(self.copy_task)

	def after_save(self):
		restart_app()
		return super().after_save()

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			a0.ignore()
		elif a0.key() == Qt.Key.Key_Q and a0.modifiers() & Qt.KeyboardModifier.ControlModifier:
			os._exit(1)
