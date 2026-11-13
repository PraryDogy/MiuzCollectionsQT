import subprocess
import time
from functools import wraps

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColorSpace, QImage
from PyQt6.QtWidgets import QApplication

from cfg import Static


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
