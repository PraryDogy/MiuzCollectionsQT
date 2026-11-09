import hashlib
import os
import subprocess
import time
import traceback
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QDate, QLocale, QSize, Qt
from PyQt6.QtGui import QColorSpace, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QVBoxLayout

from cfg import JsonData, Static


class Utils:

	@classmethod
	def qimage_from_array(cls, image: np.ndarray) -> QImage | None:
		try:
			image = np.ascontiguousarray(image)
			if image.ndim == 2:
				height, width = image.shape
				qimage = QImage(image.data, width, height, width,
								QImage.Format.Format_Grayscale8).copy()
			elif image.ndim == 3 and image.shape[2] in (3, 4):
				height, width, channels = image.shape
				fmt = (QImage.Format.Format_RGB888 if channels == 3
					else QImage.Format.Format_RGBA8888)
				qimage = QImage(image.data, width, height,
								channels * width, fmt).copy()
			else:
				print(f"qimage_from_array: channels trouble {image.shape}")
				return None

			# Значения уже в sRGB (ImgUtils приводит всё к sRGB), явно это фиксируем
			qimage.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.SRgb))
			return qimage
		except Exception as e:
			print(f"qimage_from_array: {e}")
			return None

	@classmethod
	def scale_qimage_dpr(cls, qimage: QImage, size: int, dpr: int = Static.DPR,
						smooth: bool = True) -> QImage:
		mode = Qt.TransformationMode.SmoothTransformation if smooth \
			else Qt.TransformationMode.FastTransformation
		scaled = qimage.scaled(
			int(size * dpr),
			int(size * dpr),
			Qt.AspectRatioMode.KeepAspectRatio,
			mode
		)
		scaled.setDevicePixelRatio(dpr)
		return scaled

	@classmethod
	def scale_qimage_square(cls, qimage: QImage, size: int, dpr: int = Static.DPR) -> QImage:
		side = int(size * dpr)
		w, h = qimage.width(), qimage.height()
		src = min(w, h)
		x = (w - src) // 2
		y = (h - src) // 2
		square_src = qimage.copy(x, y, src, src)
		scaled = square_src.scaled(
			side,
			side,
			Qt.AspectRatioMode.IgnoreAspectRatio,
			Qt.TransformationMode.SmoothTransformation
		)
		scaled.setDevicePixelRatio(dpr)
		return scaled

	# @classmethod
	# def thumb_scaler(cls):
		# return cls.scale_qimage_square if JsonData.square_thumbs else cls.scale_qimage_dpr
	
	# даже когда сетка квадратная мы не будем обрезать изображения
	@classmethod
	def thumb_scaler(cls):
		return cls.scale_qimage_dpr

	@classmethod
	def pyqt_copy_text(cls, text: str):
		QApplication.clipboard().setText(text)
		return True

	@classmethod
	def pyqt_paste_text(cls) -> str:
		return QApplication.clipboard().text()
		
	@classmethod
	def macos_reveal_files(cls, paths: list[str], scpt = Static.SCRIPTS_REVEAL_FILES):
		subprocess.Popen(["osascript", scpt] + paths)
	
	@classmethod
	def clear_layout(cls, layout: QVBoxLayout | QHBoxLayout | QGridLayout):
		while layout.count():
			item = layout.takeAt(0)
			widget = item.widget()
			if widget is not None:
				widget.setParent(None)
				widget.deleteLater()

	@staticmethod
	def escape_like(text: str) -> str:
		"""Экранирует спецсимволы LIKE, чтобы путь сравнивался буквально."""
		return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

	def timed(label: str):
		def deco(fn):
			@wraps(fn)
			def wrapper(*args, **kwargs):
				t0 = time.perf_counter()
				try:
					return fn(*args, **kwargs)
				finally:
					print(f"[timing] {label}: {(time.perf_counter() - t0) * 1000:.1f} ms")
			return wrapper
		return deco


class ReadableDate:
	def __init__(self, lng_index: int):
		data = {
			0: (QLocale.Language.Russian, QLocale.Country.Russia),
			1: (QLocale.Language.English, QLocale.Country.UnitedStates),
		}
		lng, country = data.get(lng_index)
		self.q_locale = QLocale(lng, country)

	def get_readable_date(self, date: QDate):
		"""
		10 января 1991
		"""
		return self.q_locale.toString(date, "d MMMM yyyy")

	@staticmethod
	def qdate_from_timestamp(timestamp: float) -> QDate:
		# Берём локальную дату, соответствующую timestamp
		dt = datetime.fromtimestamp(timestamp)
		return QDate(dt.year, dt.month, dt.day)

	@staticmethod
	def qdate_from_date(d: date) -> QDate:
		return QDate(d.year, d.month, d.day)