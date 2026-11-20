import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static
from system.items import Mf
from system.lang import Lng
from system.runnable import URunnable, UThreadPool

from ._base_widgets import (ConfirmWindow, MfAliasWidget, MfPathWidget,
                            RowArrowWidget, SaveRowArrowWidget, UGroupBox,
                            UMainWindow, UMenu, UPushButton)
from .win_settings import NewMfWin


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



class FirstLoadWin(NewMfWin):
	pass

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
			JsonData.lng_index = Lng.CURRENT_LNG_INDEX
			JsonData.write_json_data()
			restart_app()

		mf_alias = self.mf_alias_widget.validate_and_show_win()
		mf_path = self.path_widget.validate_and_show_win()
		if mf_alias and mf_path:
			self.save_win = ConfirmWindow(Lng.save_text_long)
			self.save_win.ok_clicked.connect(
				lambda: save_fin(mf_alias, mf_path)
			)
			self.save_win.center_to_parent(self.window())
			self.save_win.show()
