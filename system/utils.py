import os
import struct
import subprocess
import time
from functools import wraps
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
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

	@classmethod
	def get_f_size(cls, bytes_size: int, round_value: int = 2) -> str:
		def format_size(size: float) -> str:
			if round_value == 0:
				return str(int(round(size)))
			return str(round(size, round_value))

		if bytes_size < 1024:
			return f"{bytes_size} байт"
		elif bytes_size < pow(1024, 2):
			return f"{format_size(bytes_size / 1024)} КБ"
		elif bytes_size < pow(1024, 3):
			return f"{format_size(bytes_size / pow(1024, 2))} МБ"
		elif bytes_size < pow(1024, 4):
			return f"{format_size(bytes_size / pow(1024, 3))} ГБ"
		elif bytes_size < pow(1024, 5):
			return f"{format_size(bytes_size / pow(1024, 4))} ТБ"

	@classmethod
	def load_thumbnail(cls, thumb_path: str | Path) -> np.ndarray | None:
		thumb_path = str(thumb_path)
		try:
			if not os.path.exists(thumb_path):
				print(f"load_thumbnail: файл не существует {thumb_path}")
				return None

			img = cv2.imread(thumb_path, cv2.IMREAD_UNCHANGED)
			if img is None:
				return None

			if img.ndim == 2:  # grayscale, конвертация не нужна
				return img

			if img.shape[2] == 4:  # BGRA -> RGBA
				return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)

			return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # BGR -> RGB

		except Exception as e:
			print(f"load_thumbnail: ошибка чтения миниатюры: {e}")
			return None

	@classmethod
	def write_thumbnail(cls, image_array: np.ndarray, thumbnail_path: Path | str) -> bool:
		thumbnail_path = str(thumbnail_path)
		if str(Static.APP_DATA_DIR) not in thumbnail_path:
			raise Exception ("неправильный путь к thumbnail", thumbnail_path)
		try:
			if image_array.ndim == 2:  # grayscale, конвертация не нужна
				img = image_array
			elif image_array.shape[2] == 3:  # RGB -> BGR для cv2
				img = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
			elif image_array.shape[2] == 4:  # RGBA -> BGRA для cv2
				img = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGRA)
			else:
				print(f"write_thumbnail: неподдерживаемое число каналов {image_array.shape}")
				return False

			return bool(cv2.imwrite(thumbnail_path, img))

		except Exception as e:
			print(f"write_thumbnail: ошибка записи миниатюры на диск: {e}")
			return False

	@classmethod
	def get_broken_thumbnail(cls):
		path = Static.JPEG_ICONS / "broken_thumbnail.jpg"
		with Image.open(path) as img:
			return np.array(img.convert("RGB"))

	@classmethod
	def _get_broken_image(cls):
		path = Static.JPEG_ICONS / "broken_image.jpg"
		with Image.open(path) as img:
			return np.array(img.convert("RGB"))
