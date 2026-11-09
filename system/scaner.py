import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Queue
from time import sleep
from typing import Literal

import sqlalchemy

from cfg import Static
from system.database import Dbase, Dirs, Thumbs
from system.main_folder import Mf
from system.multiprocess import BaseProcessWorker
from system.shared_utils import ImgUtils
from system.utils import Utils


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
	"""
	kind: Literal["search_dirs", "indexing", "no_connection"]
	mf_alias: str
	current: int = 0
	total: int = 0


class ScanerWorker(BaseProcessWorker):
	def __init__(self, target: callable, args: tuple):
		self.process_queue = Queue()
		super().__init__(target, (*args, self.process_queue))


@dataclass(slots=True)
class DirItem:
	"""
	Параметры:
	- rel_path: относительный путь к подкаталогу относительно корня Mf (`mf_paths[0]`).
	  Пример:
		- корень = /User/Downloads/parent/folder
		- подкаталог = /User/Downloads/parent/folder/subfolder
		- rel_path = /subfolder
	- mod: дата модификации каталога (os.stat.st_mtime), либо StopList.MOD для стоп-папки
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
	changed: list[DirItem]        # mod отличается (включая сброшенный в 0)
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


class ScanerParent:
	def __init__(self, scaner_item: BaseScanerItem):
		super().__init__()
		self.scaner_item = scaner_item


class DirsChangeWatcher(ScanerParent):
	"""Быстрая проверка: есть ли вообще изменения. Нужна только как оптимизация."""

	def __init__(self, scaner_item: BaseScanerItem):
		super().__init__(scaner_item)

	def is_changed(self) -> tuple[bool, list[DirItem]]:
		db_dirs: list[DirItem] = []
		mf = self.scaner_item.mf
		stop = StopList(mf.mf_stop_list)
		base_path = mf.mf_paths[0].strip(os.sep)
		q = (
			sqlalchemy.select(Dirs.rel_dir_path, Dirs.mod)
			.where(Dirs.mf_alias == mf.mf_alias)
		)
		with self.scaner_item.engine.connect() as conn:
			for rel_path, mod in conn.execute(q):
				abs_dir_path = os.path.join(
					os.sep,
					base_path,
					rel_path.strip(os.sep)
				)
				db_dirs.append(DirItem(
					abs_path=abs_dir_path,
					rel_path=rel_path,
					mod=mod
				))

		is_changed_flag = False

		for item in db_dirs:
			if not os.path.exists(item.abs_path):
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
				stat = os.stat(item.abs_path)
			except Exception as e:
				print("DirsChangeWatcher error", item.abs_path, e)
				continue

			# mod = 0 у обычной папки означает сброс (смена каталога или возврат из стоп-листа)
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
		"""
		scaner = self.scaner_item

		scaner.process_queue.put(ScanProgress("search_dirs", scaner.mf.mf_alias))

		stop = StopList(scaner.mf.mf_stop_list)
		dirs: list[DirItem] = []
		stack = [scaner.mf.mf_paths[0]]

		while stack:
			try:
				scandir_iterator = os.scandir(stack.pop())
			except Exception:
				print(traceback.format_exc())
				continue

			for entry in scandir_iterator:
				try:
					if not entry.is_dir():
						continue
				except Exception:
					print(traceback.format_exc())
					continue

				rel_path = Utils.remove_mf_path(
					mf_path=scaner.mf.mf_paths[0],
					abs_path=entry.path
				)

				if stop.contains(rel_path):
					dirs.append(DirItem(entry.path, rel_path, StopList.MOD))
					continue

				stack.append(entry.path)
				mod = int(entry.stat().st_mtime)
				dirs.append(DirItem(entry.path, rel_path, mod))

		try:
			stats = os.stat(scaner.mf.mf_paths[0])
			dirs.append(DirItem(scaner.mf.mf_paths[0], os.sep, int(stats.st_mtime)))
		except Exception:
			print(traceback.format_exc())

		return dirs


class DirsDbUpdater(ScanerParent):
	def __init__(self, scaner_item: BaseScanerItem, dirs_to_scan: list[DirItem]):
		super().__init__(scaner_item)
		self.dirs_to_scan = dirs_to_scan

	def upsert_records(self):
		"""
		Запускать в самом конце сканирования, когда обновлена таблица Thumbs
		и произведена работа с миниатюрами в `hashdir`.
		"""
		scaner = self.scaner_item

		if not os.path.exists(scaner.mf.mf_paths[0]):
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
		"""
		finder_images: list[ImgItem] = []

		for dir_item in self.dirs_to_scan:
			try:
				scandir_iterator = os.scandir(dir_item.abs_path)
			except Exception:
				print(traceback.format_exc())
				continue

			for entry in scandir_iterator:
				if entry.path.endswith(ImgUtils.ext_all):
					try:
						stat = entry.stat()
					except Exception:
						print(traceback.format_exc())
						continue

					size = int(stat.st_size)
					mod = int(stat.st_mtime)

					img_item = ImgItem(entry.path, size, mod)
					finder_images.append(img_item)

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
				abs_img_path = Utils.add_mf_path(
					mf_path=scaner.mf.mf_paths[0],
					rel_path=rel_path
				)
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

	def _progress(self) -> ScanProgress:
		scaner = self.scaner_item
		return ScanProgress(
			kind="indexing",
			mf_alias=scaner.mf.mf_alias,
			current=scaner.current_count,
			total=scaner.total_count,
		)

	def del_thumbs(self):
		"""
		Удаляет миниатюры и соответствующие записи из БД пакетами по 10.

		Перед каждым пакетом проверяет доступность источника (Mf) и
		прерывается при его недоступности.
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

		def _remove_thumb(img_item: ImgItem):
			scaner.current_count += 1
			scaner.process_queue.put(self._progress())
			abs_thumb_path = Utils.get_abs_thumb_path(
				img_item.rel_thumb_path
			)
			try:
				os.remove(abs_thumb_path)
				try:
					os.rmdir(os.path.dirname(abs_thumb_path))
				except OSError:
					pass
				return True
			except Exception:
				print(traceback.format_exc())
				return False

		step = 10
		chunked_del_images = [
			self.removed_images[i:i+step]
			for i in range(0, len(self.removed_images), step)
		]
		for chunk in chunked_del_images:
			if not os.path.exists(scaner.mf.mf_paths[0]):
				break
			good_chunk: list[ImgItem] = []
			for img_item in chunk:
				if _remove_thumb(img_item):
					good_chunk.append(img_item)
			if good_chunk:
				_del_records(good_chunk)

	def add_thumbs(self):
		"""
		Создает миниатюры и соответствующие записи из БД пакетами по 10.

		Перед каждым пакетом проверяет доступность источника (Mf) и
		прерывается при его недоступности.
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
					rel_img_path = Utils.remove_mf_path(
						mf_path=scaner.mf.mf_paths[0],
						abs_path=img_item.abs_img_path
					)
					abs_thumb_path = Utils.create_abs_thumb_path(
						rel_img_path=rel_img_path,
						mf_alias=scaner.mf.mf_alias
					)
					rel_thumb_path = Utils.get_rel_thumb_path(abs_thumb_path)
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

		def _create_thumb(img_item: ImgItem):
			"""
			Создает и записывает в `hashdir` миниатюру.
			"""
			scaner.current_count += 1
			scaner.process_queue.put(self._progress())
			img = ImgUtils.read_img(img_item.abs_img_path)
			img = ImgUtils.fit_to_thumb(img, Static.THUMB_MAX_SIZE)
			rel_img_path = Utils.remove_mf_path(
				mf_path=scaner.mf.mf_paths[0],
				abs_path=img_item.abs_img_path
			)
			thumb_path = Utils.create_abs_thumb_path(
				rel_img_path=rel_img_path,
				mf_alias=scaner.mf.mf_alias
			)
			if ImgUtils.write_thumb(thumb_path, img):
				return True
			return False

		step = 10
		chunked_new_images = [
			self.new_images[i:i+step]
			for i in range(0, len(self.new_images), step)
		]
		for chunk in chunked_new_images:
			if not os.path.exists(scaner.mf.mf_paths[0]):
				break
			good_chunk: list[ImgItem] = []
			for img_item in chunk:
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
		Добавляет и удаляет миниатюры в hashdir, затем обновляет таблицы Thumbs и Dirs.
		Изменения применяются сразу, без подтверждения.
		"""
		scaner = self.scaner_item

		img_loader = ImgLoader(scaner, self.dirs_to_scan)
		finder_images = img_loader.get_finder_images()
		db_images = img_loader.get_db_images()

		img_comparator = ImgComparator(scaner, finder_images, db_images)
		removed_images, new_images = img_comparator.start()

		scaner.total_count = len(removed_images) + len(new_images)

		thumbs_updater = ThumbsUpdater(scaner, removed_images, new_images)
		thumbs_updater.del_thumbs()
		thumbs_updater.add_thumbs()

		dirs_updater = DirsDbUpdater(scaner, self.dirs_to_scan)
		dirs_updater.upsert_records()


class RemovedDirsCleaner(ScanerParent):

	def __init__(self, scaner_item: BaseScanerItem, removed_dirs: list[DirItem]):
		super().__init__(scaner_item)
		self.removed_dirs = removed_dirs

	def remove_thumbs(self):
		"""
		Удаляет миниатюры из 'hashdir' и записи в базе данных Thumbs
		"""
		scaner = self.scaner_item

		def _get_thumbs(conn: sqlalchemy.Connection, dir_item: DirItem):
			prefix = Utils.escape_like(dir_item.rel_path)
			one_slash = f"{prefix}/%"
			stmt_thumbs_to_remove = (
				sqlalchemy.select(Thumbs.rel_thumb_path)
				.where(Thumbs.rel_img_path.ilike(one_slash, escape="\\"))
				.where(Thumbs.mf_alias == scaner.mf.mf_alias)
			)
			return conn.execute(stmt_thumbs_to_remove).scalars().all()

		def _remove_thumb(rel_thumb_path: str):
			abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
			try:
				os.remove(abs_thumb_path)
			except Exception:
				print(traceback.format_exc())
			try:
				os.rmdir(os.path.dirname(abs_thumb_path))
			except OSError:
				pass

		def _remove_records(conn: sqlalchemy.Connection, thumbs_to_remove):
			del_stmt = (
				sqlalchemy.delete(Thumbs.table)
				.where(Thumbs.rel_thumb_path.in_(thumbs_to_remove))
				.where(Thumbs.mf_alias == scaner.mf.mf_alias)
			)
			conn.execute(del_stmt)

		with scaner.engine.begin() as conn:
			for dir_item in self.removed_dirs:
				thumbs_to_remove = _get_thumbs(conn, dir_item)
				if thumbs_to_remove:
					for rel_thumb_path in thumbs_to_remove:
						_remove_thumb(rel_thumb_path)
					_remove_records(conn, thumbs_to_remove)

	def remove_dirs(self):
		"""
		Удаляет записи в базе данных Dirs
		"""
		scaner = self.scaner_item

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
	def start(mf_list: list[Mf], queue: Queue):
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
			# проверка доступности хранилища: при недоступности записи не трогаем
			if scaner_item.mf.get_avaiable_mf_path():
				try:
					print("scaner started", scaner_item.mf.mf_alias)
					BaseScaner.single_mf_scan(scaner_item)
					print("scaner finished", scaner_item.mf.mf_alias)
				except Exception:
					print(traceback.format_exc())
					continue
			else:
				scaner_item.process_queue.put(
					ScanProgress("no_connection", scaner_item.mf.mf_alias)
				)
				print("no connection", scaner_item.mf.mf_alias)
				sleep(3)
		engine.dispose()

	@staticmethod
	def single_mf_scan(scaner_item: BaseScanerItem):
		watcher = DirsChangeWatcher(scaner_item)
		is_changed, db_dirs = watcher.is_changed()
		if not is_changed:
			print(scaner_item.mf.mf_alias, "not changed")
			return

		finder_dirs = DirsLoader(scaner_item).get_finder_dirs()
		if not finder_dirs:
			return

		diff = diff_dirs(finder_dirs, db_dirs)

		# удаление: пропавшие папки и папки, ставшие стоп-папками
		to_clean = diff.removed + diff.newly_stopped
		if to_clean:
			BaseScaner.log_removed_dirs(scaner_item, finder_dirs, to_clean)
			cleaner = RemovedDirsCleaner(scaner_item, to_clean)
			cleaner.remove_thumbs()
			cleaner.remove_dirs()

		# стоп-папки: только запись mod = 0 в Dirs, изображения не трогаем
		if diff.stopped:
			DirsDbUpdater(scaner_item, diff.stopped).upsert_records()

		# добавленные и изменённые: сверяем изображения и обновляем Dirs
		to_scan = diff.added + diff.changed
		if to_scan:
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
			f"Mf: {scaner_item.mf.mf_alias}, {scaner_item.mf.mf_paths[0]}",
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

		Параметры:
		- mf: сканируемая директория должна принадлежать определенному Mf
		- dirs_to_scan: директории, которые нужно просканировать
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
		if scaner_item.mf.get_avaiable_mf_path():
			dir_items: list[DirItem] = []
			stop = StopList(mf.mf_stop_list)
			for i in dirs_to_scan:
				rel_path = Utils.remove_mf_path(mf.mf_paths[0], i)
				if stop.contains(rel_path):
					continue
				try:
					mod = int(os.stat(i).st_mtime)
				except Exception:
					print(traceback.format_exc())
					continue
				item = DirItem(
					abs_path=i,
					rel_path=rel_path,
					mod=mod
				)
				if item not in dir_items:
					dir_items.append(item)
			if dir_items:
				updater = DirImagesUpdater(scaner_item, dir_items)
				updater.start()