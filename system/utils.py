import io
import os
import struct
import subprocess
import tempfile
import time
from functools import wraps
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
import rawpy
import tifffile
from PIL import Image, ImageCms, ImageOps
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColorSpace, QImage
from PyQt6.QtWidgets import QApplication

from cfg import Static

pillow_heif.register_heif_opener()
Image.MAX_IMAGE_PIXELS = None

ICC_TIFF_TAG = 34675          # InterColorProfile
TIFF_ORIENTATION_TAG = 274    # Orientation

_TIFF_ORIENT = {
	2: Image.Transpose.FLIP_LEFT_RIGHT,
	3: Image.Transpose.ROTATE_180,
	4: Image.Transpose.FLIP_TOP_BOTTOM,
	5: Image.Transpose.TRANSPOSE,
	6: Image.Transpose.ROTATE_270,
	7: Image.Transpose.TRANSVERSE,
	8: Image.Transpose.ROTATE_90,
}


class ImageReader:

	ext_jpeg = (
		".jpg", ".JPG",
		".jpeg", ".JPEG",
		".jpe", ".JPE",
		".jfif", ".JFIF",
		".bmp", ".BMP",
		".dib", ".DIB",
		".webp", ".WEBP",
		".ppm", ".PPM",
		".pgm", ".PGM",
		".pbm", ".PBM",
		".pnm", ".PNM",
		".ico", ".ICO",
		".heic", ".HEIC",
		".heif", ".HEIF",
	)

	ext_tiff = (
		".tif", ".TIF",
		".tiff", ".TIFF",
	)

	ext_psd = (
		".psd", ".PSD",
		".psb", ".PSB",
	)

	ext_png = (
		".png", ".PNG",
	)

	ext_gif = (
		".gif", ".GIF",
	)

	ext_raw = (
		".nef", ".NEF",
		".cr2", ".CR2",
		".cr3", ".CR3",
		".arw", ".ARW",
		".raf", ".RAF",
		".dng", ".DNG",
		".rw2", ".RW2",
		".orf", ".ORF",
		".srw", ".SRW",
		".pef", ".PEF",
		".rwl", ".RWL",
		".mos", ".MOS",
		".kdc", ".KDC",
		".mrw", ".MRW",
		".x3f", ".X3F",
	)

	ext_video = (
		".avi", ".AVI",
		".mp4", ".MP4",
		".mov", ".MOV",
		".mkv", ".MKV",
		".wmv", ".WMV",
		".flv", ".FLV",
		".webm", ".WEBM",
	)

	ext_icns = (
		".icns", ".ICNS",
	)

	ext_svg = (
		".svg", ".SVG",
	)

	ext_all = (
		*ext_jpeg,
		*ext_tiff,
		*ext_psd,
		*ext_png,
		*ext_gif,
		*ext_raw,
		*ext_video,
		*ext_icns,
		*ext_svg,
	)

	@staticmethod
	def _sniff(path: str) -> str | None:
		"""Определяет формат по сигнатуре файла, а не по расширению."""
		try:
			with open(path, "rb") as f:
				head = f.read(4)
		except OSError:
			return None
		if head == b"8BPS":                      # PSD и PSB
			return "psd"
		if head in (b"II*\x00", b"MM\x00*"):     # TIFF (little/big endian)
			return "tiff"
		return None

	@staticmethod
	def _flatten(img: Image.Image) -> Image.Image:
		"""Прозрачность кладём на белый фон, остальные режимы не трогаем."""
		if img.mode == "P":
			img = img.convert("RGBA" if "transparency" in img.info else "RGB")
		if img.mode in ("RGBA", "LA"):
			img = img.convert("RGBA")
			bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
			return Image.alpha_composite(bg, img).convert("RGB")
		return img

	@classmethod
	def _to_srgb_array(cls, img: Image.Image, icc: bytes | None) -> np.ndarray:
		"""Приводит изображение к sRGB uint8 RGB по встроенному ICC-профилю."""
		img = cls._flatten(img)
		if icc and img.mode in ("RGB", "CMYK"):
			try:
				src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
				dst = ImageCms.createProfile("sRGB")
				img = ImageCms.profileToProfile(img, src, dst, outputMode="RGB")
			except Exception as e:
				print("icc transform error", e)
				img = img.convert("RGB")
		else:
			img = img.convert("RGB")
		return np.asarray(img, dtype=np.uint8)

	@classmethod
	def _read_gif(cls, src):
		with Image.open(src) as img:
			img.seek(0)
			return cls._to_srgb_array(img, img.info.get("icc_profile"))

	@classmethod
	def _read_pil(cls, path: str):
		"""JPEG, PNG, WebP, BMP, HEIC, ICNS и другие форматы, которые читает Pillow."""
		try:
			with Image.open(path) as img:
				icc = img.info.get("icc_profile")  # читаем до exif_transpose
				img = ImageOps.exif_transpose(img)
				return cls._to_srgb_array(img, icc)
		except Exception as e:
			print("read pil error", e)
			return None

	@classmethod
	def _read_jpg(cls, path: str):
		return cls._read_pil(path)

	@classmethod
	def _read_png(cls, path: str):
		return cls._read_pil(path)

	@classmethod
	def _read_icns(cls, path: str):
		return cls._read_pil(path)

	@classmethod
	def _read_tiff(cls, path: str):
		try:
			with tifffile.TiffFile(path) as tf:
				page = tf.pages[0]
				# CMYK и палитровые TIFF читает Pillow, tifffile их не разбирает
				if page.photometric in (tifffile.PHOTOMETRIC.SEPARATED,
				                        tifffile.PHOTOMETRIC.PALETTE):
					return cls._read_pil(path)

				icc_tag = page.tags.get(ICC_TIFF_TAG)
				icc = icc_tag.value if icc_tag else None
				orient_tag = page.tags.get(TIFF_ORIENTATION_TAG)
				orientation = orient_tag.value if orient_tag else 1
				arr = page.asarray()
		except Exception as e:
			print("read tiff, tifffile error", path, e)
			return cls._read_pil(path)

		# Планарная раскладка (C, H, W) -> (H, W, C)
		if arr.ndim == 3 and arr.shape[0] in (3, 4) and arr.shape[-1] > 4:
			arr = np.moveaxis(arr, 0, -1)
		# Одноканальный (H, W, 1) -> (H, W)
		if arr.ndim == 3 and arr.shape[-1] == 1:
			arr = arr[..., 0]

		# Приведение к uint8 с правильной шкалой
		if arr.dtype == np.uint8:
			pass
		elif arr.dtype == np.uint16:
			arr = np.round(arr.astype(np.float32) * (255.0 / 65535.0)).astype(np.uint8)
		else:
			arr = arr.astype(np.float32)
			if arr.size and float(arr.max()) <= 1.0:
				arr *= 255.0
			arr = np.clip(np.round(arr), 0, 255).astype(np.uint8)

		# Лишние каналы: оставляем RGB или RGBA, LA сводим к L
		if arr.ndim == 3:
			if arr.shape[-1] == 2:
				arr = arr[..., 0]
			elif arr.shape[-1] > 4:
				arr = arr[..., :3]

		img = Image.fromarray(np.ascontiguousarray(arr))

		if orientation in _TIFF_ORIENT:
			img = img.transpose(_TIFF_ORIENT[orientation])

		return cls._to_srgb_array(img, icc)

	@classmethod
	def _read_quicklook(cls, path: str, size: int = 5000, timeout: int = 120):
		# Создаем уникальную временную папку для конкретного вызова
		with tempfile.TemporaryDirectory() as tmp_dir_name:
			tmp_dir = Path(tmp_dir_name)
			try:
				subprocess.run(
					["qlmanage", "-t", "-s", str(size), "-o", str(tmp_dir), path],
					check=True,
					stdout=subprocess.DEVNULL,
					stderr=subprocess.DEVNULL,
					timeout=timeout,
				)
			except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
				return None

			# Ищем файл только в нашей изолированной папке
			generated_files = list(tmp_dir.glob("*.png"))
			if not generated_files:
				return None

			with Image.open(generated_files[0]) as img:
				arr = np.array(img.convert("RGB"))

			# Файл удалится вместе с временной папкой при выходе из блока
			return arr

	@classmethod
	def _read_svg(cls, path: str):
		return None

	@classmethod
	def _read_raw(cls, path: str):
		try:
			# https://github.com/letmaik/rawpy
			with rawpy.imread(path) as raw:
				thumb = raw.extract_thumb()

			if thumb.format == rawpy.ThumbFormat.JPEG:
				img = Image.open(io.BytesIO(thumb.data))
			elif thumb.format == rawpy.ThumbFormat.BITMAP:
				img = Image.fromarray(thumb.data)
			else:
				return None

			icc = img.info.get("icc_profile")
			img = ImageOps.exif_transpose(img)  # поворот по EXIF эскиза
			return cls._to_srgb_array(img, icc)
		except Exception as e:
			print("read raw error", e)
			return None

	@classmethod
	def _read_movie(cls, path: str, time_sec=1):
		try:
			cap = cv2.VideoCapture(path)
			cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
			success, frame = cap.read()
			cap.release()
			if success:
				return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			return None
		except Exception as e:
			print("read movie error", e)
			return None

	@classmethod
	def read_img(cls, path: str) -> np.ndarray | None:
		ext = os.path.splitext(path)[1].lower()

		# RAW проверяем первым: CR2, NEF, DNG и др. основаны на TIFF
		if ext in cls.ext_raw:
			return cls._read_raw(path)
		if ext in cls.ext_video:
			return cls._read_movie(path)
		if ext in cls.ext_gif:
			return cls._read_gif(path)
		if ext in cls.ext_svg:
			return cls._read_svg(path)

		# PSD и PSB через QuickLook, как и раньше
		if ext in cls.ext_psd or cls._sniff(path) == "psd":
			return cls._read_quicklook(path)

		# Сигнатура важнее расширения: .jpg, который на деле TIFF, читается правильно
		if cls._sniff(path) == "tiff" or ext in cls.ext_tiff:
			return cls._read_tiff(path)

		if ext in cls.ext_icns or ext in cls.ext_png or ext in cls.ext_jpeg:
			return cls._read_pil(path)

		return None


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
	def get_broken_image(cls):
		path = Static.JPEG_ICONS / "broken_image.jpg"
		with Image.open(path) as img:
			return np.array(img.convert("RGB"))
