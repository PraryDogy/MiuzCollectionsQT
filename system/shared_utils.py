import io
import os
import struct
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
import pillow_heif
import rawpy
import tifffile
from PIL import Image, ImageCms, ImageOps

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

	@classmethod
	def _get_broken_image(cls):
		path = Static.JPEG_ICONS / "broken_image.jpg"

		if not path.exists():
			raise Exception(f"Img Utils {path} not exists")

		with Image.open(path) as img:
			return np.array(img.convert("RGB"))

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
			return cls._get_broken_image()

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
				# Возвращаем "пустую" картинку при ошибке или таймауте
				return np.zeros((100, 100, 3), dtype=np.uint8)

			# Ищем файл только в нашей изолированной папке
			generated_files = list(tmp_dir.glob("*.png"))
			if not generated_files:
				return cls._get_broken_image()

			with Image.open(generated_files[0]) as img:
				arr = np.array(img.convert("RGB"))

			# Файл удалится вместе с временной папкой при выходе из блока
			return arr

	@classmethod
	def _read_svg(cls, path: str):
		return cls._get_broken_image()

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
				return cls._get_broken_image()

			icc = img.info.get("icc_profile")
			img = ImageOps.exif_transpose(img)  # поворот по EXIF эскиза
			return cls._to_srgb_array(img, icc)
		except Exception as e:
			print("read raw error", e)
			return cls._get_broken_image()

	@classmethod
	def _read_movie(cls, path: str, time_sec=1):
		try:
			cap = cv2.VideoCapture(path)
			cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
			success, frame = cap.read()
			cap.release()
			if success:
				return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			return cls._get_broken_image()
		except Exception as e:
			print("read movie error", e)
			return cls._get_broken_image()

	@classmethod
	def read_img(cls, path: str):
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

		return cls._get_broken_image()

	@classmethod
	def get_psd_size(cls, path):
		with open(path, "rb") as f:
			header = f.read(26)

		if header[:4] != b"8BPS":
			raise ValueError("Не PSD")

		height, width = struct.unpack(">II", header[14:22])
		return width, height

	# перенес
	@classmethod
	def resize(cls, image: np.ndarray, size: int) -> np.ndarray:
		try:
			if image is None:
				return cls.resize(cls._get_broken_image(), size)
			h, w = image.shape[:2]
			if w > h:  # Горизонтальное изображение
				new_w = size
				new_h = int(h * (size / w))
			elif h > w:  # Вертикальное изображение
				new_h = size
				new_w = int(w * (size / h))
			else:  # Квадратное изображение
				new_w, new_h = size, size
			return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
		except Exception as e:
			print("fit image error", e)
			return cls.resize(cls._get_broken_image(), size)

	# перенес
	@classmethod
	def get_img_res(cls, path: str):

		def read(path: str):
			img_ = ImageReader.read_img(path)
			if img_ is not None and len(img_.shape) > 1:
				h, w = img_.shape[0], img_.shape[1]
				return f"{w}x{h}"
			return None

		def psd_read(path: str):
			try:
				w, h = ImageReader.get_psd_size(path)
				return f"{w}x{h}"
			except Exception as e:
				print("multiprocess > ImgRes psd error", e)
				return None

		if path.endswith(ImageReader.ext_psd):
			return psd_read(path)
		return read(path)

	@classmethod
	def fit_to_thumb(cls, image: np.ndarray, size: int) -> np.ndarray:
		try:
			h, w = image.shape[:2]
			if h == 0 or w == 0:
				print("fit_to_thumb: пустое изображение")
				return cls.fit_to_thumb(cls._get_broken_image(), size)

			scale = size / max(h, w)
			new_w = max(1, int(w * scale))
			new_h = max(1, int(h * scale))

			return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

		except Exception as e:
			print(f"fit_to_thumb: ошибка масштабирования: {e}")
			return cls.fit_to_thumb(cls._get_broken_image(), size)

	@classmethod
	def write_thumb(cls, thumb_path: str, thumb: np.ndarray):
		try:
			if len(thumb.shape) == 2:  # grayscale
				img = thumb
			elif thumb.shape[2] == 3:  # RGB -> BGR для cv2
				img = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
			elif thumb.shape[2] == 4:  # RGBA -> BGRA для cv2
				img = cv2.cvtColor(thumb, cv2.COLOR_RGBA2BGRA)
			else:
				print(f"write_thumb: неподдерживаемое число каналов {thumb.shape}")
				return False
			cv2.imwrite(thumb_path, img)
			return True
		except Exception as e:
			print(f"write_thumb: ошибка записи thumb на диск: {e}")
			return False

	@classmethod
	def read_thumb(cls, thumb_path: str) -> np.ndarray | None:
		try:
			if not os.path.exists(thumb_path):
				print(f"read_thumb: файл не существует {thumb_path}")
				return None
			img = cv2.imread(thumb_path, cv2.IMREAD_UNCHANGED)
			if img is None:
				return None
			if img.ndim == 2:
				return img
			if img.shape[2] == 4:
				return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
			return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		except Exception as e:
			print(f"read_thumb: ошибка чтения thumb: {e}")
			return None

	# перенес
	@staticmethod
	def is_grayscale(img: np.ndarray) -> bool:
		return len(img.shape) < 3 or img.shape[2] == 1


class MyImage:
	def __init__(self, image_path: Path):
		super().__init__()
		self.image_path = image_path
		self.image_array: np.ndarray = None

	def load(self):
		self.image_array = ImageReader.read_img(str(self.image_path))

	def is_grayscale(self) -> bool:
		return len(self.image_array.shape) < 3 or self.image_array.shape[2] == 1

	def get_img_res(self):

		def read():
			if len(self.image_array.shape) > 1:
				h, w = self.image_array.shape[0], self.image_array.shape[1]
				return f"{w}x{h}"
			return None

		def psd_read():
			try:
				w, h = self.get_psd_size()
				return f"{w}x{h}"
			except Exception as e:
				print("multiprocess > ImgRes psd error", e)
				return None

		if self.image_path.endswith(ImageReader.ext_psd):
			return psd_read()
		return read()

	def get_psd_size(self):
		with open(self.image_path, "rb") as f:
			header = f.read(26)

		if header[:4] != b"8BPS":
			raise ValueError("Не PSD")

		height, width = struct.unpack(">II", header[14:22])
		return width, height

	def resize(self, size: int) -> np.ndarray:
		try:
			if self.image_array is None:
				return self.resize(self._get_broken_image(), size)
			h, w = self.image_array.shape[:2]
			if w > h:  # Горизонтальное изображение
				new_w = size
				new_h = int(h * (size / w))
			elif h > w:  # Вертикальное изображение
				new_h = size
				new_w = int(w * (size / h))
			else:  # Квадратное изображение
				new_w, new_h = size, size
			return cv2.resize(self.image_array, (new_w, new_h), interpolation=cv2.INTER_AREA)
		except Exception as e:
			print("fit image error", e)
			return self.image_array.resize(self._get_broken_image(), size)

		
	def _get_broken_image(self):
		path = Static.JPEG_ICONS / "broken_image.jpg"

		if not path.exists():
			raise Exception(f"Img Utils {path} not exists")

		with Image.open(path) as img:
			return np.array(img.convert("RGB"))