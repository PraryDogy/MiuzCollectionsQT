import os
import traceback
from dataclasses import dataclass, replace
from datetime import datetime
from multiprocessing import Queue
from time import sleep
from typing import Literal

import sqlalchemy

from cfg import Static
from system.database import Dbase, Dirs, Thumbs
from system.items import Mf
from system.multiprocess import BaseProcessWorker
from system.shared_utils import ImgUtils
from system.utils import Utils


# Порог совпадения при смене пути и размер выборки для проверки каталога
MATCH_THRESHOLD = 80
SAMPLE_SIZE = 500

# mod = StopList.MOD (0): стоп-папка
# mod = PENDING_MOD (-1): папка найдена, но её изображения ещё не проверены.
# Такая папка всегда считается изменённой, пока скан не дойдёт до неё.
PENDING_MOD = -1


class Tools:
	@staticmethod
	def log(text: str) -> None:
		from cfg import Static as _Static
		filepath = _Static.APP_DATA_DIR / "log.txt"
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		log_entry = f"[{timestamp}] {text}\n"
		with open(filepath, "a", encoding="utf-8") as f:
			f.write(log_entry)


# ==========================================
# Сообщения из дочернего процесса в GUI.
# Дочерний процесс не использует Lng: текст строит GUI-поток.
# ==========================================

@dataclass(slots=True)
class ScanProgress:
	"""
	Ход сканирования.
	- kind: "search_dirs" — поиск папок,
	        "indexing" — создание миниатюр (current из total),
	        "no_connection" — нет доступа к хранилищу.
	- dir_path: папка, в которой сейчас обрабатывается изображение (только для indexing)
	"""
	kind: Literal["search_dirs", "indexing", "no_connection"]
	mf_alias: str
	current: int = 0
	total: int = 0
	dir_path: str = ""


@dataclass(slots=True)
class DirsReady:
	"""Папки Mf записаны в Dirs (пока с PENDING_MOD). Можно строить левое меню."""
	mf_alias: str


@dataclass(slots=True)
class PathMismatch:
	"""Новый корень не совпал с сохранённым каталогом. Сканирование прервано."""
	mf_alias: str
	match_percent: int


@dataclass(slots=True)
class PathCheckPassed:
	"""Новый корень совпал с сохранённым каталогом. GUI может сбросить old_mf_path."""
	mf_alias: str
	match_percent: int


class ScanIncomplete(Exception):
	"""Сбор данных прерван: корень недоступен, результат неполный и не должен использоваться."""


class ScanerWorker(BaseProcessWorker):
	def __init__(self, target: callable, args: tuple):
		self.process_queue = Queue()
		super().__init__(target, (*args, self.process_queue))


@dataclass(slots=True)
class DirItem:
	"""
	Параметры:
	- rel_path: относительный путь к подкаталогу относительно корня Mf (`mf_path`).
	  Пример:
		- корень = /User/Downloads/parent/folder
		- подкаталог = /User/Downloads/parent/folder/subfolder
		- rel_path = /subfolder
	- mod: дата модификации каталога (os.stat.st_mtime),
	  StopList.MOD для стоп-папки или PENDING_MOD для непроверенной папки
	"""
	abs_path: str
	rel_path: str
	mod: int


@dataclass(slots=True)
class ImgItem:
	"""
	Параметры:
	- abs_img_path: полный путь до изображения
	- size: размер изображения в байтах
	- mod: os.stat.st_mtime
	- rel_thumb_path: путь до миниатюры /hashdir/thumb.jpg
	"""
	abs_img_path: str
	size: int
	mod: int
	rel_thumb_path: str = ""


class StopList:
	"""
	Стоп-лист по относительным путям. Папка из стоп-листа и всё её поддерево
	считаются стоп-папками: изображения в них не сканируются, структура сохраняется.
	"""

	# mod для стоп-папок в Dirs. Реальный mtime никогда не равен 0.
	MOD = 0

	def __init__(self, stop_list: list[str]):
		self.roots = {
			os.sep + s.strip(os.sep)
			for s in stop_list
			if s.strip(os.sep)
		}

	def contains(self, rel_path: str) -> bool:
		rel = os.sep + rel_path.strip(os.sep)
		for root in self.roots:
			if rel == root or rel.startswith(root + os.sep):
				return True
		return False


@dataclass(slots=True)
class ForcedScanerItem:
	mf: Mf
	dirs_to_scan: list[str]


@dataclass(slots=True)
class BaseScanerItem:
	mf: Mf
	engine: sqlalchemy.Engine
	process_queue: Queue
	total_count: int
	current_count: int
	scaner_type: Literal["forced", "base"]


@dataclass(slots=True)
class DirsDiff:
	removed: list[DirItem]        # удалены с диска
	added: list[DirItem]          # новые на диске
	changed: list[DirItem]        # mod отличается (включая PENDING_MOD)
	stopped: list[DirItem]        # стоп-папки на диске, mod = StopList.MOD
	newly_stopped: list[DirItem]  # стали стоп-папкой только что


def diff_dirs(finder: list[DirItem], db: list[DirItem]) -> DirsDiff:
	"""Сравнивает папки с диска и из БД по относительному пути."""
	db_map = {d.rel_path: d for d in db}
	finder_map = {d.rel_path: d for d in finder}

	removed = [d for p, d in db_map.items() if p not in finder_map]

	added, changed, stopped, newly_stopped = [], [], [], []
	for p, f in finder_map.items():
		old = db_map.get(p)
		if f.mod == StopList.MOD:
			stopped.append(f)
			if old is not None and old.mod != StopList.MOD:
				newly_stopped.append(f)
			continue
		if old is None:
			added.append(f)
		elif old.mod != f.mod:
			changed.append(f)

	return DirsDiff(removed, added, changed, stopped, newly_stopped)


class CatalogIdentity:
	"""
	Проверка, тот ли это каталог, что был сохранён в БД.
	Берётся случайная выборка изображений из БД, их относительные пути
	проверяются на новом корне, и сравниваются размеры файлов.
	"""

	@staticmethod
	def sample_db_images(engine: sqlalchemy.Engine, mf_alias: str) -> list[tuple[str, int]]:
		stmt = (
			sqlalchemy.select(Thumbs.rel_img_path, Thumbs.size)
			.where(Thumbs.mf_alias == mf_alias)
			.order_by(sqlalchemy.func.random())
			.limit(SAMPLE_SIZE)
		)
		with engine.connect() as conn:
			return [(rel, size) for rel, size in conn.execute(stmt)]

	@staticmethod
	def match_percent(mf: Mf, sample: list[tuple[str, int]]) -> int:
		if not sample:
			return 100  # в БД нет изображений, сравнивать не с чем
		matched = 0
		for rel_path, size in sample:
			try:
				st = os.stat(mf.create_abs_path(rel_path))
			except OSError:
				continue
			if int(st.st_size) == size:
				matched += 1
		return matched * 100 // len(sample)


class ScanerParent:
	def __init__(self, scaner_item: BaseScanerItem):
		super().__init__()
		self.scaner_item = scaner_item


class DirsChangeWatcher(ScanerParent):
	"""Быстрая проверка: есть ли вообще изменения. Нужна только как оптимизация."""

	def __init__(self, scaner_item: BaseScanerItem):
		super().__init__(scaner_item)

	def is_changed(self) -> tuple[bool, list[DirItem]]:
		db_dirs = BaseScaner.load_db_dirs(self.scaner_item)
		mf = self.scaner_item.mf
		stop = StopList(mf.mf_stop_list)
		base_path = mf.mf_path.strip(os.sep)

		is_changed_flag = False

		for item in db_dirs:
			abs_dir_path = os.path.join(os.sep, base_path, item.rel_path.strip(os.sep))
			if not os.path.exists(abs_dir_path):
				is_changed_flag = True
				break

			if stop.contains(item.rel_path):
				# стоп-папка: mtime не отслеживаем, но если в БД ещё не стоит MOD,
				# нужно её перезаписать
				if item.mod != StopList.MOD:
					is_changed_flag = True
					break
				continue

			try:
				stat = os.stat(abs_dir_path)
			except Exception as e:
				print("DirsChangeWatcher error", abs_dir_path, e)
				continue

			# PENDING_MOD (-1) всегда меньше mtime, поэтому папка считается изменённой
			if item.mod == StopList.MOD or int(stat.st_mtime) > item.mod:
				is_changed_flag = True
				break

		if not db_dirs:
			is_changed_flag = True
		return (is_changed_flag, db_dirs)


class DirsLoader(ScanerParent):

	def __init__(self, scaner_item: BaseScanerItem):
		super().__init__(scaner_item)

	def get_finder_dirs(self) -> list[DirItem]:
		"""
		Собирает список директорий:
		- стоп-папка записывается в список с mod = StopList.MOD, внутрь не заходим
		- её подпапки и изображения не попадают в список вообще
		- если недоступен сам корень, поднимает ScanIncomplete
		"""
		scaner = self.scaner_item
		root = scaner.mf.mf_path

		scaner.process_queue.put(ScanProgress("search_dirs", scaner.mf.mf_alias))

		stop = StopList(scaner.mf.mf_stop_list)
		dirs: list[DirItem] = []
		stack = [root]

		while stack:
			path = stack.pop()
			try:
				scandir_iterator = os.scandir(path)
			except OSError:
				# ошибка на корне = диск пропал, список неполный
				if path == root:
					raise ScanIncomplete(root)
				print(traceback.format_exc())
				continue

			with scandir_iterator:
				for entry in scandir_iterator:
					try:
						if not entry.is_dir():
							continue
					except OSError:
						print(traceback.format_exc())
						continue

					rel_path = scaner.mf.create_rel_path(entry.path)

					if stop.contains(rel_path):
						dirs.append(DirItem(entry.path, rel_path, StopList.MOD))
						continue

					stack.append(entry.path)
					mod = int(entry.stat().st_mtime)
					dirs.append(DirItem(entry.path, rel_path, mod))

		try:
			stats = os.stat(root)
		except OSError:
			raise ScanIncomplete(root)
		dirs.append(DirItem(root, os.sep, int(stats.st_mtime)))

		return dirs


class DirsDbUpdater(ScanerParent):
	def __init__(self, scaner_item: BaseScanerItem, dirs_to_scan: list[DirItem]):
		super().__init__(scaner_item)
		self.dirs_to_scan = dirs_to_scan

	def upsert_records(self):
		"""
		Записывает папки в Dirs одной транзакцией.
		Проверка корня стоит до DELETE, поэтому при отказе откатываются оба шага.
		"""
		scaner = self.scaner_item
		if not scaner.mf.is_root_alive():
			print("root lost, skip Dirs update", scaner.mf.mf_alias)
			return

		with scaner.engine.begin() as conn:
			rel_paths = [dir_item.rel_path for dir_item in self.dirs_to_scan]
			del_stmt = (
				sqlalchemy.delete(Dirs.table)
				.where(Dirs.rel_dir_path.in_(rel_paths))
				.where(Dirs.mf_alias == scaner.mf.mf_alias)
			)
			conn.execute(del_stmt)

			values_list = [
				{
					Dirs.rel_dir_path.name: dir_item.rel_path,
					Dirs.mod.name: dir_item.mod,
					Dirs.mf_alias.name: scaner.mf.mf_alias
				}
				for dir_item in self.dirs_to_scan
			]
			if values_list:
				conn.execute(sqlalchemy.insert(Dirs.table), values_list)


class ImgLoader(ScanerParent):

	def __init__(self, scaner_item: BaseScanerItem, dirs_to_scan: list[DirItem]):
		super().__init__(scaner_item)
		self.dirs_to_scan = dirs_to_scan

	def get_finder_images(self) -> list[ImgItem]:
		"""
		Собирает список `ImgItem` из указанных директорий.
		Если недоступен корень, поднимает ScanIncomplete.
		Ошибка отдельной папки при живом корне пропускается.
		"""
		root = self.scaner_item.mf.mf_path
		finder_images: list[ImgItem] = []

		for dir_item in self.dirs_to_scan:
			try:
				scandir_iterator = os.scandir(dir_item.abs_path)
			except OSError:
				if not os.path.isdir(root):
					raise ScanIncomplete(root)
				print(traceback.format_exc())
				continue

			with scandir_iterator:
				for entry in scandir_iterator:
					if not entry.path.endswith(ImgUtils.ext_all):
						continue
					try:
						stat = entry.stat()
					except OSError:
						print(traceback.format_exc())
						continue

					size = int(stat.st_size)
					mod = int(stat.st_mtime)
					finder_images.append(ImgItem(entry.path, size, mod))

		return finder_images

	def get_db_images(self) -> list[ImgItem]:
		"""
		Возвращает записи об изображениях из БД для изменённых папок.
		Один запрос на весь Mf, дальше фильтрация по родительской папке.
		"""
		scaner = self.scaner_item
		wanted_dirs = {dir_item.rel_path for dir_item in self.dirs_to_scan}

		stmt = (
			sqlalchemy.select(
				Thumbs.rel_thumb_path,
				Thumbs.rel_img_path,
				Thumbs.size,
				Thumbs.mod,
			)
			.where(Thumbs.mf_alias == scaner.mf.mf_alias)
		)

		db_images: list[ImgItem] = []
		with scaner.engine.connect() as conn:
			for rel_thumb_path, rel_path, size, mod in conn.execute(stmt):
				folder = os.path.dirname(rel_path)
				if folder not in wanted_dirs:
					continue
				abs_img_path = scaner.mf.create_abs_path(rel_path)
				db_images.append(
					ImgItem(abs_img_path, size, mod, rel_thumb_path)
				)

		return db_images


class ImgComparator(ScanerParent):

	def __init__(self, scaner_item: BaseScanerItem, finder_images: list[ImgItem], db_images: list[ImgItem]):
		super().__init__(scaner_item)
		self.finder_images = finder_images
		self.db_images = db_images

	def start(self):
		"""
		Собирает списки `ImgItem`:
		- изображения, которых больше нет в Finder но есть в БД
		- изображения, которых нет в БД, но есть в Finder
		"""
		finder_dict = {
			(i.abs_img_path, i.size, i.mod): i
			for i in self.finder_images
		}
		db_dict = {
			(i.abs_img_path, i.size, i.mod): i
			for i in self.db_images
		}

		removed_images = [
			img_item
			for data, img_item in db_dict.items()
			if data not in finder_dict
		]
		new_images = [
			img_item
			for data, img_item in finder_dict.items()
			if data not in db_dict
		]

		return removed_images, new_images


class ThumbsUpdater(ScanerParent):

	def __init__(self, scaner_item: BaseScanerItem, removed_images: list[ImgItem], new_images: list[ImgItem]):
		super().__init__(scaner_item)
		self.removed_images = removed_images
		self.new_images = new_images

	def _progress(self, img_item: ImgItem) -> ScanProgress:
		scaner = self.scaner_item
		return ScanProgress(
			kind="indexing",
			mf_alias=scaner.mf.mf_alias,
			current=scaner.current_count,
			total=scaner.total_count,
			dir_path=os.path.dirname(img_item.abs_img_path),
		)

	def del_thumbs(self):
		"""
		Удаляет миниатюры и записи из БД пакетами по 10.
		Перед каждым пакетом проверяет доступность корня и прерывается, если он пропал.
		"""
		scaner = self.scaner_item

		def _del_records(good_chunk: list[ImgItem]):
			with scaner.engine.begin() as conn:
				rel_thumb_paths = [i.rel_thumb_path for i in good_chunk]
				if not rel_thumb_paths:
					return
				stmt = (
					sqlalchemy.delete(Thumbs.table)
					.where(Thumbs.rel_thumb_path.in_(rel_thumb_paths))
					.where(Thumbs.mf_alias == scaner.mf.mf_alias)
				)
				conn.execute(stmt)

		def _remove_thumb(img_item: ImgItem) -> bool:
			scaner.current_count += 1
			scaner.process_queue.put(self._progress(img_item))
			abs_thumb_path = Mf.get_abs_thumb_path(img_item.rel_thumb_path)
			try:
				os.remove(abs_thumb_path)
			except FileNotFoundError:
				return True
			except Exception:
				print(traceback.format_exc())
				return False
			try:
				os.rmdir(os.path.dirname(abs_thumb_path))
			except OSError:
				pass
			return True

		step = 10
		for i in range(0, len(self.removed_images), step):
			if not scaner.mf.is_root_alive():
				print("root lost, stop thumbs deletion", scaner.mf.mf_alias)
				return
			good_chunk: list[ImgItem] = []
			for img_item in self.removed_images[i:i + step]:
				if _remove_thumb(img_item):
					good_chunk.append(img_item)
			if good_chunk:
				_del_records(good_chunk)

	def add_thumbs(self):
		"""
		Создаёт миниатюры и записи в БД пакетами по 10.
		Перед каждым пакетом проверяет доступность корня.
		"""
		scaner = self.scaner_item

		def _upsert_records(good_chunk: list[ImgItem]):
			with scaner.engine.begin() as conn:
				rel_thumb_paths = [i.rel_thumb_path for i in good_chunk]
				if not rel_thumb_paths:
					return
				stmt = (
					sqlalchemy.delete(Thumbs.table)
					.where(Thumbs.rel_thumb_path.in_(rel_thumb_paths))
					.where(Thumbs.mf_alias == scaner.mf.mf_alias)
				)
				conn.execute(stmt)

				values_list = []
				for img_item in good_chunk:
					rel_img_path = scaner.mf.create_rel_path(img_item.abs_img_path)
					abs_thumb_path = scaner.mf.create_abs_thumb_path(rel_img_path)
					rel_thumb_path = Mf.get_rel_thumb_path(abs_thumb_path)
					root = os.path.dirname(rel_img_path)
					values_list.append({
						Thumbs.rel_img_path.name: rel_img_path,
						Thumbs.rel_thumb_path.name: rel_thumb_path,
						Thumbs.size.name: img_item.size,
						Thumbs.birth.name: 0,
						Thumbs.mod.name: img_item.mod,
						Thumbs.root.name: root,
						Thumbs.coll.name: "none",
						Thumbs.fav.name: 0,
						Thumbs.mf_alias.name: scaner.mf.mf_alias
					})
				stmt = sqlalchemy.insert(Thumbs.table).values(values_list)
				conn.execute(stmt)

		def _create_thumb(img_item: ImgItem) -> bool:
			scaner.current_count += 1
			scaner.process_queue.put(self._progress(img_item))
			img = ImgUtils.read_img(img_item.abs_img_path)
			img = ImgUtils.fit_to_thumb(img, Static.THUMB_MAX_SIZE)
			rel_img_path = scaner.mf.create_rel_path(img_item.abs_img_path)
			thumb_path = scaner.mf.create_abs_thumb_path(rel_img_path)
			return bool(ImgUtils.write_thumb(thumb_path, img))

		step = 10
		for i in range(0, len(self.new_images), step):
			if not scaner.mf.is_root_alive():
				print("root lost, stop thumbs creation", scaner.mf.mf_alias)
				return
			good_chunk: list[ImgItem] = []
			for img_item in self.new_images[i:i + step]:
				if _create_thumb(img_item):
					good_chunk.append(img_item)
			if good_chunk:
				_upsert_records(good_chunk)


class DirImagesUpdater(ScanerParent):
	def __init__(self, scaner_item: BaseScanerItem, dirs_to_scan: list[DirItem]):
		super().__init__(scaner_item)
		self.dirs_to_scan = dirs_to_scan

	def start(self):
		"""
		Сравнивает изображения выбранных папок с БД и применяет изменения.
		Если корень пропал во время сбора, ничего не меняет.
		В конце записывает реальные mod папок вместо PENDING_MOD.
		"""
		scaner = self.scaner_item

		try:
			finder_images = ImgLoader(scaner, self.dirs_to_scan).get_finder_images()
		except ScanIncomplete:
			print("scan incomplete, root lost", scaner.mf.mf_alias)
			return

		db_images = ImgLoader(scaner, self.dirs_to_scan).get_db_images()

		# диск мог пропасть во время сбора: неполный finder_images нельзя сравнивать
		if not scaner.mf.is_root_alive():
			print("root lost before compare, skip", scaner.mf.mf_alias)
			return

		img_comparator = ImgComparator(scaner, finder_images, db_images)
		removed_images, new_images = img_comparator.start()

		scaner.total_count = len(removed_images) + len(new_images)

		ThumbsUpdater(scaner, removed_images, new_images).del_thumbs()
		ThumbsUpdater(scaner, removed_images, new_images).add_thumbs()

		if scaner.mf.is_root_alive():
			DirsDbUpdater(scaner, self.dirs_to_scan).upsert_records()


class RemovedDirsCleaner(ScanerParent):

	def __init__(self, scaner_item: BaseScanerItem, removed_dirs: list[DirItem]):
		super().__init__(scaner_item)
		self.removed_dirs = removed_dirs

	def remove_thumbs(self):
		"""
		Удаляет миниатюры папок из hashdir и записи Thumbs пакетами по 10.
		Перед каждым пакетом проверяет доступность корня.
		"""
		scaner = self.scaner_item
		step = 10

		def _get_thumbs(conn: sqlalchemy.Connection, dir_item: DirItem):
			prefix = Utils.escape_like(dir_item.rel_path)
			one_slash = f"{prefix}/%"
			stmt = (
				sqlalchemy.select(Thumbs.rel_thumb_path)
				.where(Thumbs.rel_img_path.ilike(one_slash, escape="\\"))
				.where(Thumbs.mf_alias == scaner.mf.mf_alias)
			)
			return conn.execute(stmt).scalars().all()

		def _remove_file(rel_thumb_path: str):
			abs_thumb_path = Mf.get_abs_thumb_path(rel_thumb_path)
			try:
				os.remove(abs_thumb_path)
			except FileNotFoundError:
				pass
			except Exception:
				print(traceback.format_exc())
			try:
				os.rmdir(os.path.dirname(abs_thumb_path))
			except OSError:
				pass

		with scaner.engine.begin() as conn:
			for dir_item in self.removed_dirs:
				thumbs_to_remove = _get_thumbs(conn, dir_item)
				for i in range(0, len(thumbs_to_remove), step):
					if not scaner.mf.is_root_alive():
						print("root lost, stop removing thumbs", scaner.mf.mf_alias)
						return
					chunk = thumbs_to_remove[i:i + step]
					for rel_thumb_path in chunk:
						_remove_file(rel_thumb_path)
					conn.execute(
						sqlalchemy.delete(Thumbs.table)
						.where(Thumbs.rel_thumb_path.in_(chunk))
						.where(Thumbs.mf_alias == scaner.mf.mf_alias)
					)

	def remove_dirs(self):
		"""Удаляет записи папок из Dirs."""
		scaner = self.scaner_item
		if not scaner.mf.is_root_alive():
			print("root lost, skip Dirs removal", scaner.mf.mf_alias)
			return

		with scaner.engine.begin() as conn:
			for dir_item in self.removed_dirs:
				stmt = (
					sqlalchemy.delete(Dirs.table)
					.where(Dirs.rel_dir_path == dir_item.rel_path)
					.where(Dirs.mf_alias == scaner.mf.mf_alias)
				)
				conn.execute(stmt)


class BaseScaner:
	@staticmethod
	def start(mf_list: list[Mf], force_full: bool, queue: Queue):
		engine = Dbase.create_engine()
		# нельзя обращаться сразу к Mf так как это мультипроцесс
		for mf in mf_list:
			scaner_item = BaseScanerItem(
				mf=mf,
				engine=engine,
				process_queue=queue,
				total_count=0,
				current_count=0,
				scaner_type="base"
			)
			if mf.is_root_alive():
				try:
					print("scaner started", mf.mf_alias)
					BaseScaner.single_mf_scan(scaner_item, force_full)
					print("scaner finished", mf.mf_alias)
				except Exception:
					print(traceback.format_exc())
					continue
			else:
				scaner_item.process_queue.put(
					ScanProgress("no_connection", mf.mf_alias)
				)
				print("no connection", mf.mf_alias)
				sleep(3)
		engine.dispose()

	@staticmethod
	def load_db_dirs(scaner_item: BaseScanerItem) -> list[DirItem]:
		"""Читает записи папок из Dirs для текущего Mf."""
		mf = scaner_item.mf
		q = (
			sqlalchemy.select(Dirs.rel_dir_path, Dirs.mod)
			.where(Dirs.mf_alias == mf.mf_alias)
		)
		db_dirs: list[DirItem] = []
		with scaner_item.engine.connect() as conn:
			for rel_path, mod in conn.execute(q):
				db_dirs.append(DirItem(
					abs_path=os.path.join(os.sep, mf.mf_path.strip(os.sep), rel_path.strip(os.sep)),
					rel_path=rel_path,
					mod=mod,
				))
		return db_dirs

	@staticmethod
	def single_mf_scan(scaner_item: BaseScanerItem, force_full: bool = False):
		mf = scaner_item.mf

		# Смена корня: проверяем, тот ли это каталог, до любых изменений в БД
		if mf.old_mf_path is not None:
			sample = CatalogIdentity.sample_db_images(scaner_item.engine, mf.mf_alias)
			percent = CatalogIdentity.match_percent(mf, sample)
			if percent < MATCH_THRESHOLD:
				scaner_item.process_queue.put(PathMismatch(mf.mf_alias, percent))
				print("path mismatch", mf.mf_alias, percent)
				return  # БД не трогаем, сканирование этого каталога прервано
			scaner_item.process_queue.put(PathCheckPassed(mf.mf_alias, percent))

		if force_full:
			# полный пересказ: все папки помечаются как изменённые
			db_dirs = BaseScaner.load_db_dirs(scaner_item)
			db_dirs = [replace(d, mod=PENDING_MOD) for d in db_dirs]
		else:
			watcher = DirsChangeWatcher(scaner_item)
			is_changed, db_dirs = watcher.is_changed()
			if not is_changed:
				print(mf.mf_alias, "not changed")
				return

		try:
			finder_dirs = DirsLoader(scaner_item).get_finder_dirs()
		except ScanIncomplete:
			print("scan incomplete, root lost", mf.mf_alias)
			return
		if not finder_dirs:
			return

		# корень мог пропасть во время обхода: неполный список не сравниваем
		if not mf.is_root_alive():
			print("root lost after dirs scan, skip", mf.mf_alias)
			return

		diff = diff_dirs(finder_dirs, db_dirs)

		# удаление: пропавшие папки и папки, ставшие стоп-папками
		to_clean = diff.removed + diff.newly_stopped
		if to_clean and mf.is_root_alive():
			BaseScaner.log_removed_dirs(scaner_item, finder_dirs, to_clean)
			cleaner = RemovedDirsCleaner(scaner_item, to_clean)
			cleaner.remove_thumbs()
			cleaner.remove_dirs()

		# стоп-папки: только запись mod = StopList.MOD в Dirs, изображения не трогаем
		if diff.stopped and mf.is_root_alive():
			DirsDbUpdater(scaner_item, diff.stopped).upsert_records()

		# добавленные и изменённые: сначала папки в БД с PENDING_MOD, затем картинки
		to_scan = diff.added + diff.changed
		if to_scan and mf.is_root_alive():
			pending = [replace(d, mod=PENDING_MOD) for d in to_scan]
			DirsDbUpdater(scaner_item, pending).upsert_records()
			scaner_item.process_queue.put(DirsReady(mf.mf_alias))

			# DirImagesUpdater запишет реальные mod, когда пройдёт сравнение
			DirImagesUpdater(scaner_item, to_scan).start()

	@staticmethod
	def log_removed_dirs(
		scaner_item: BaseScanerItem,
		finder_dirs: list[DirItem],
		removed_dirs: list[DirItem]
	):
		finder_lines = [f"{i.abs_path}, {i.rel_path}" for i in finder_dirs]
		removed_lines = [f"{i.abs_path}, {i.rel_path}" for i in removed_dirs]
		now_line = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
		sep = "==========="
		lines = [
			sep,
			now_line,
			f"Mf: {scaner_item.mf.mf_alias}, {scaner_item.mf.mf_path}",
			"Удаление директорий:",
			f"finder dirs: {len(finder_lines)}",
			f"removed dirs: {len(removed_lines)}",
			"",
			"Список finder dirs (абсолютный путь, относительный путь)",
			*finder_lines,
			"",
			"Список removed dirs (абсолютный путь, относительный путь)",
			*removed_lines,
			sep,
			"\n\n"
		]
		Tools.log("\n".join(lines))


class ForcedScaner:

	@staticmethod
	def start(item: ForcedScanerItem, queue: Queue):
		print("single dir scaner started, mf:", item.mf.mf_alias)
		ForcedScaner.single_mf_scan(
			mf=item.mf,
			dirs_to_scan=item.dirs_to_scan,
			queue=queue,
		)
		print("single dir scaner finished, mf:", item.mf.mf_alias)

	@staticmethod
	def single_mf_scan(mf: Mf, dirs_to_scan: list[str], queue: Queue):
		"""
		Сканирует заданные директории в пределах Mf на предмет новых или
		удаленных изображений. Стоп-папки и их поддерево пропускаются.
		"""
		engine = Dbase.create_engine()
		scaner_item = BaseScanerItem(
			mf=mf,
			engine=engine,
			process_queue=queue,
			total_count=0,
			current_count=0,
			scaner_type="forced"
		)
		if not mf.is_root_alive():
			engine.dispose()
			return

		stop = StopList(mf.mf_stop_list)
		dir_items: list[DirItem] = []
		for abs_path in dirs_to_scan:
			rel_path = mf.create_rel_path(abs_path)
			if stop.contains(rel_path):
				continue
			try:
				mod = int(os.stat(abs_path).st_mtime)
			except OSError:
				print(traceback.format_exc())
				continue
			item = DirItem(abs_path=abs_path, rel_path=rel_path, mod=mod)
			if item not in dir_items:
				dir_items.append(item)

		if dir_items:
			DirImagesUpdater(scaner_item, dir_items).start()
		engine.dispose()