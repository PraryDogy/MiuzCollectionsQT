import hashlib
import json
import os
import struct
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from multiprocessing import shared_memory
from pathlib import Path

import numpy as np
from PyQt6.QtCore import QDate, QLocale, QObject, pyqtSignal
from PyQt6.QtGui import QImage

from cfg import Static

from .image_reader import ImageReader


class _ProbeSignals(QObject):
	done = pyqtSignal(str, bool)  # путь, доступен ли


class RootProbe:
	"""Проверка доступности корня каталога по запросу, без фонового опроса.

	- Проверка запускается только из check(), то есть когда что-то нужно знать.
	- Результат кэшируется на TTL секунд.
	- На один путь не больше одной проверки в работе: зависший диск не порождает новых потоков.
	- GUI не ждёт диск: результат приходит сигналом signals.done.
	"""

	TTL = 10.0
	signals = _ProbeSignals()
	_lock = threading.Lock()
	_result: dict[str, tuple[bool, float]] = {}
	_busy: set[str] = set()

	@classmethod
	def check(cls, path: str) -> bool | None:
		"""Возвращает последний известный результат (None, если его ещё нет).
		Если результат устарел, запускает проверку; ответ придёт в signals.done."""
		now = time.monotonic()
		with cls._lock:
			cached = cls._result.get(path)
			stale = cached is None or now - cached[1] >= cls.TTL
			if stale and path not in cls._busy:
				cls._busy.add(path)
				threading.Thread(target=cls._probe, args=(path,), daemon=True).start()
			return cached[0] if cached else None

	@classmethod
	def _probe(cls, path: str) -> None:
		ok = os.path.isdir(path)  # может зависнуть: это делает только один поток на путь
		with cls._lock:
			cls._result[path] = (ok, time.monotonic())
			cls._busy.discard(path)
		cls.signals.done.emit(path, ok)  # в GUI-поток уйдёт через очередь Qt


@dataclass(slots=True)
class DataItem:
	base_qimage: QImage
	resized_qimages: list[QImage]
	rel_thumb_path: str
	rel_path: str
	abs_path: str
	fav: bool
	day_month_year: str
	hour_min_sec: str
	filename: str
	ext: str


class Filters:
	items = []

	@classmethod
	def validate_json(cls):
		try:
			with open(Static.FILTERS_JSON, "r", encoding="utf-8") as file:
				data: list[str] = json.load(file)
		except Exception as e:
			print("Filters, error reading file", e)
			return False

		if not isinstance(data, list):
			print("Filters: json data не является списком")
			return False

		if len(data) == 0:
			print("Filters: json data список пуст")
			return False

		filters = []
		for i in data:
			if isinstance(i, str):
				filters.append(i)
		if not filters:
			print("Filters, нет string фильтров")
			return False

		return filters

	@classmethod
	def json_to_app(cls, data: list[str]):
		cls.items.clear()
		cls.items = data

	@classmethod
	def write_json_data(cls):
		with open(Static.FILTERS_JSON, "w", encoding="utf-8") as f:
			json.dump(cls.items, f, indent=4, ensure_ascii=False)


class Strings:
	mf_alias = "mf_alias"
	mf_paths = "mf_paths"
	mf_stop_list = "mf_stop_list"
	mf_current_path = "mf_current_path"


class Mf:
	current_mf: "Mf" = None
	items: list["Mf"] = []
	__slots__ = [
		Strings.mf_alias,
		Strings.mf_paths,
		Strings.mf_stop_list,
		Strings.mf_current_path,
	]

	REQUIRED_KEYS = (Strings.mf_alias, Strings.mf_paths, Strings.mf_stop_list)

	def __init__(self, mf_alias, mf_paths, mf_stop_list, mf_current_path=None):
		super().__init__()
		self.mf_alias: str = mf_alias
		self.mf_paths: list[str] = mf_paths
		self.mf_stop_list: list[str] = mf_stop_list
		self.mf_current_path: str | None = mf_current_path

	@property
	def mf_path(self):
		return self.mf_paths[0]

	@mf_path.setter
	def mf_path(self, value: str):
		self.mf_paths[0] = value

	@property
	def old_mf_path(self):
		return self.mf_paths[1] if len(self.mf_paths) > 1 else None

	@old_mf_path.setter
	def old_mf_path(self, value: str | None):
		if value is None:
			del self.mf_paths[1:]
		elif len(self.mf_paths) > 1:
			self.mf_paths[1] = value
		else:
			self.mf_paths.append(value)

	@classmethod
	def json_to_app(cls, data: list[dict]):
		cls.items.clear()
		for d in data:
			cls.items.append(Mf(**d))

	def create_abs_path(self, rel_path: str) -> str:
		return os.path.join(self.mf_path, rel_path.lstrip(os.sep))

	def create_rel_path(self, abs_path: str) -> str:
		rel = os.path.relpath(abs_path, self.mf_path)
		if rel == os.curdir:
			return os.sep
		return os.sep + rel

	def create_abs_thumb_path(self, rel_img_path: str) -> str:
		clean_rel_path = rel_img_path.strip(os.sep)
		encoded = clean_rel_path.encode('utf-8')
		filename = hashlib.md5(encoded).hexdigest() + ".jpg"
		folder_name = f"{self.mf_alias}-{filename[:2]}"
		new_folder = Static.HASHDIR / folder_name
		new_folder.mkdir(parents=True, exist_ok=True)
		return str(new_folder / filename)

	@classmethod
	def get_rel_thumb_path(cls, abs_thumb_path: str):
		p_base = Path(str(Static.APP_DATA_DIR).strip(os.sep))
		p_abs = Path(abs_thumb_path.strip(os.sep))
		if p_abs.is_relative_to(p_base):
			return os.sep + str(p_abs.relative_to(p_base))

	@classmethod
	def get_abs_thumb_path(cls, rel_thumb_path: str):
		rel_thumb_path = Path(rel_thumb_path.strip(os.sep))
		return Static.APP_DATA_DIR / rel_thumb_path

	def is_root_alive(self) -> bool:
		"""Синхронная проверка. Только для фоновых процессов: сканер, воркеры."""
		return os.path.isdir(self.mf_path)

	def is_root_alive_cached(self) -> bool:
		"""Для GUI-потока: не ждёт диск, результат приходит через RootProbe.signals."""
		return RootProbe.check(self.mf_path) is True

	def get_data(self):
		return {i: getattr(self, i) for i in self.__slots__}

	def repair_ignore_list(self):
		self.mf_stop_list = [i for i in self.mf_stop_list if i]

	@classmethod
	def write_json_data(cls):
		with open(Static.MF_JSON, "w", encoding="utf-8") as file:
			data = []
			for i in cls.items:
				i.repair_ignore_list()
				data.append(i.get_data())
			json.dump(data, file, ensure_ascii=False, indent=4)

	# --- Валидация ---

	@staticmethod
	def _check_item(raw) -> tuple[dict | None, str | None]:
		"""Проверяет один элемент. Возвращает (очищенный словарь, None) или (None, причина)."""
		if not isinstance(raw, dict):
			return None, "элемент не является объектом"

		missing = [k for k in Mf.REQUIRED_KEYS if k not in raw]
		if missing:
			return None, f"нет обязательных ключей: {missing}"

		alias = raw[Strings.mf_alias]
		paths = raw[Strings.mf_paths]
		stops = raw[Strings.mf_stop_list]
		current = raw.get(Strings.mf_current_path)

		if not isinstance(alias, str) or not alias.strip():
			return None, "mf_alias должен быть непустой строкой"

		if not isinstance(paths, list) or not paths:
			return None, "mf_paths должен быть непустым списком"
		if not all(isinstance(p, str) and p.strip() for p in paths):
			return None, "mf_paths содержит не строки или пустые пути"

		if not isinstance(stops, list):
			return None, "mf_stop_list должен быть списком"
		if not all(isinstance(s, str) for s in stops):
			return None, "mf_stop_list содержит не строки"

		if current is not None and not isinstance(current, str):
			return None, "mf_current_path должен быть строкой или null"

		cleaned = {
			Strings.mf_alias: alias,
			Strings.mf_paths: paths,
			Strings.mf_stop_list: stops,
			Strings.mf_current_path: current,
		}
		return cleaned, None

	@classmethod
	def validate_json(cls) -> list[dict] | None:
		"""
		Читает mf.json и возвращает список валидных словарей для Mf(**d).
		Невалидные элементы пропускаются с причиной в консоли.
		Возвращает None, если файл не читается или валидных элементов нет.
		"""
		try:
			with open(Static.MF_JSON, "r", encoding="utf-8") as file:
				data = json.load(file)
		except (OSError, json.JSONDecodeError) as e:
			print("Mf: не удалось прочитать файл:", e)
			return None

		if not isinstance(data, list):
			print("Mf: корень JSON должен быть списком")
			return None

		valid: list[dict] = []
		seen_aliases: set[str] = set()
		rejected = 0

		for index, raw in enumerate(data):
			cleaned, error = cls._check_item(raw)

			# уникальность alias без учёта регистра, как в UI (_get_error)
			if error is None:
				key = cleaned[Strings.mf_alias].lower()
				if key in seen_aliases:
					error = f"дубликат mf_alias: {cleaned[Strings.mf_alias]!r}"
				else:
					seen_aliases.add(key)

			if error is not None:
				rejected += 1
				print(f"Mf: элемент #{index} пропущен: {error}")
				continue

			valid.append(cleaned)

		if rejected:
			print(f"Mf: пропущено элементов: {rejected}, валидных: {len(valid)}")

		if not valid:
			print("Mf: нет ни одного валидного архива")
			return None

		return valid


class Servers:
	items = []

	@classmethod
	def validate_json(cls):
		try:
			with open(Static.SERVERS_JSON, "r", encoding="utf-8") as file:
				data: list[list[str]] = json.load(file)
		except Exception as e:
			print("Servers, error reading file", e)
			return False

		if not isinstance(data, list):
			print("Servers: json data не является списком")
			return False

		if len(data) == 0:
			print("Servers: json data список пуст")
			return False

		servers = []
		for server_data in data:
			if isinstance(server_data, list):
				if (x for x in server_data if isinstance(x, str)):
					servers.append(server_data)
		if not servers:
			return False

		return servers

	@classmethod
	def json_to_app(cls, data: list[list[str]]):
		cls.items.clear()
		cls.items = data

	@classmethod
	def write_json_data(cls):
		with open(Static.SERVERS_JSON, "w", encoding="utf-8") as file:
			json.dump(cls.items, file, indent=4, ensure_ascii=False)


class ReadableDateItem:
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


class ImageArrayItem:
	def __init__(self, image_path: Path | str):
		super().__init__()
		self.image_path = str(image_path)
		self.image_array: np.ndarray
		self.shm: shared_memory
		self.shm_name: str
		self.shape: tuple[int, ...]
		self.dtype: str

	def load(self):
		self.image_array = ImageReader.read_img(self.image_path)

	def load_shared_memory(self):
		self.shm = shared_memory.SharedMemory(create=True, size=self.image_array.nbytes)
		buffer = np.ndarray(self.image_array.shape, dtype=self.image_array.dtype, buffer=self.shm.buf)
		buffer[:] = self.image_array

		self.shm_name = self.shm.name
		self.shape = self.image_array.shape
		self.dtype = self.image_array.dtype.str

	def is_grayscale(self) -> bool:
		return len(self.image_array.shape) < 3 or self.image_array.shape[2] == 1

	def get_img_res(self):

		def read():
			if self.image_array is not None and len(self.image_array.shape) > 1:
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

	def resize(self, size: int) -> np.ndarray | None:
		import cv2
		if self.image_array is None:
			self.image_array = self.get_broken_image()

		try:
			h, w = self.image_array.shape[:2]
			if h == 0 or w == 0:
				raise ValueError("пустое изображение")

			scale = size / max(h, w)
			new_w = max(1, int(round(w * scale)))
			new_h = max(1, int(round(h * scale)))

			interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LANCZOS4
			self.image_array = cv2.resize(self.image_array, (new_w, new_h), interpolation=interpolation)

		except Exception as e:
			print(f"resize error: {e}")
			self.image_array = self.get_broken_image()

		return self.image_array

	def is_grayscale(self) -> bool:
		return len(self.image_array.shape) < 3 or self.image_array.shape[2] == 1