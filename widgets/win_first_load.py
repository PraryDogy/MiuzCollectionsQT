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

from ._base_widgets import (ConfirmWin, HoverGroupBox, TitleWidget,
                            TransparentWidget, UMenu, UPushButton)
from .win_settings import NewMfWin

LNG_INDEX = 0


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


class MiuzGroup(HoverGroupBox):
	remove_mf_clicked = pyqtSignal()

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
			"MIUZ Diamonds",
			"Загрузить настройки для MIUZ Diamonds",
			Static.COLOR_ICONS / "miuz.svg"
		)
		content_lay.addWidget(title_widget)

		# правая часть: кнопка запуска, по центру по вертикали
		self.start_btn = QSvgWidget(str(Static.GRAY_ICONS / "arrow_right.svg"))
		self.start_btn.setFixedSize(15, 15)

		main_lay.addWidget(content, 1)
		main_lay.addWidget(self.start_btn, 0, Qt.AlignmentFlag.AlignVCenter)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
			self.remove_mf_clicked.emit()
		super().mouseReleaseEvent(event)



class FirstLoadWin(NewMfWin):
	def __init__(self, mf_path = None):
		super().__init__(mf_path)
		rus_icon = QIcon(str(Static.COLOR_ICONS / "rus_flag.svg"))
		eng_icon = QIcon(str(Static.COLOR_ICONS / "eng_flag.svg"))

		if LNG_INDEX == 0:
			icon = rus_icon
		else:
			icon = eng_icon

		lng_menu = UMenu()

		rus = QAction(Lng.lng_menu_rus, lng_menu)
		rus.setIcon(rus_icon)
		rus.setIconVisibleInMenu(True)
		lng_menu.addAction(rus)

		eng = QAction(Lng.lng_menu_eng, lng_menu)
		eng.setIcon(eng_icon)
		eng.setIconVisibleInMenu(True)
		lng_menu.addAction(eng)

		lng_wrapper = TransparentWidget()
		lng_layout = QHBoxLayout(lng_wrapper)
		lng_layout.setContentsMargins(0, 5, 11, 0)
		lng_layout.setSpacing(0)

		lng_layout.addStretch()

		lng_button = UPushButton("")
		lng_button.setMenu(lng_menu)
		lng_button.setIcon(icon)
		lng_button.setIconSize(QSize(18, 18))
		lng_button.adjustSize()
		lng_button.setFixedWidth(lng_button.width() + 10)
		lng_layout.addWidget(lng_button)

		self.title_bar.set_custom_widget(lng_wrapper)
		self.set_titlebar_height(lng_button.height() + 8)

		if os.path.exists(Static.MIUZ_ZIP):
			idx = self.group_lay.indexOf(self.mf_path_widget) + 1

			self.miuz_wid = MiuzGroup()
			self.miuz_wid.clicked.connect(self.copy_zip_cmd)
			self.group_lay.insertWidget(idx, self.miuz_wid)

			self.setFixedHeight(self.height() + self.miuz_wid.sizeHint().height())

	def copy_zip_cmd(self):

		def fin():
			JsonData.lng_index = Lng.CURRENT_LNG_INDEX
			JsonData.write_json_data()
			restart_app()

		self.copy_task = ZipTask()
		self.copy_task.sigs.finished.connect(fin)
		self.hide()
		UThreadPool.start(self.copy_task)

	def save_cmd(self):

		def save_fin(mf_alias: str, mf_path: str):
			mf = Mf(
				mf_alias=mf_alias,
				mf_paths=[mf_path, ],
				mf_stop_list=[]
			)
			Mf.items.clear()
			Mf.items.append(mf)
			Mf.write_json_data()
			JsonData.lng_index = LNG_INDEX
			JsonData.write_json_data()
			restart_app()

		mf_alias = self.mf_alias_widget.validate_and_show_win()
		mf_path = self.path_widget.validate_and_show_win()
		if mf_alias and mf_path:
			self.confirm = ConfirmWin(self.window(), Lng.save_text_long, "blue", "yellow")
			self.confirm.ok_clicked.connect(lambda: save_fin(mf_alias, mf_path))
