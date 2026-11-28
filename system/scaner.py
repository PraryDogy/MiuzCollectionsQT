import os
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from multiprocessing import Queue
from time import sleep
from typing import Callable, Literal

import sqlalchemy

from cfg import Static

from .database import Dbase, Dirs, Properties, Thumbs
from .image_reader import ImageReader
from .items import ImageArrayItem, Mf
from .multiprocess import BaseProcessWorker
from .utils import Utils

# ==========================================
# Константы
# ==========================================

# Порог совпадения при смене пути и размер выборки для проверки каталога
MATCH_THRESHOLD = 80
SAMPLE_SIZE = 500

# Сколько файлов обрабатывать пакетом перед записью в БД
BATCH_SIZE = 10

# mod = StopList.MOD (0): стоп-папка
# mod = PENDING_MOD (-1): папка найдена, но её изображения ещё не проверены.
#   Такая папка всегда считается изменённой, пока скан не дойдёт до неё.
PENDING_MOD = -1


# ==========================================
# Лог
# ==========================================

class Tools:
    @staticmethod
    def log(text: str) -> None:
        filepath = Static.APP_DATA_DIR / "log.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")


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
class MfScanned:
    """В БД записаны изменения каталога. GUI может перерисовать сетку."""
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
    def __init__(self, target: Callable, args: tuple):
        self.process_queue = Queue()
        super().__init__(target, (*args, self.process_queue))


# ==========================================
# Данные
# ==========================================

@dataclass(slots=True)
class DirItem:
    """
    - rel_path: относительный путь к подкаталогу относительно корня Mf.
      Пример: корень = /User/Downloads/parent/folder,
              подкаталог = /User/Downloads/parent/folder/subfolder,
              rel_path = /subfolder
    - mod: дата модификации каталога (st_mtime),
      StopList.MOD для стоп-папки или PENDING_MOD для непроверенной папки
    """
    abs_path: str
    rel_path: str
    mod: int


@dataclass(slots=True)
class ImgItem:
    """
    - abs_img_path: полный путь до изображения
    - size: размер в байтах
    - mod: st_mtime
    - rel_thumb_path: путь до миниатюры /hashdir/thumb.jpg
    """
    abs_img_path: str
    size: int
    mod: int
    rel_thumb_path: str = ""


@dataclass(frozen=True, slots=True)
class ScanEnv:
    """Неизменяемое окружение одного прохода: что сканируем, куда пишем, куда шлём прогресс."""
    mf: Mf
    engine: sqlalchemy.Engine
    queue: Queue


@dataclass(slots=True)
class DirsDiff:
    removed: list[DirItem]        # удалены с диска
    added: list[DirItem]          # новые на диске
    changed: list[DirItem]        # mod отличается (включая PENDING_MOD)
    stopped: list[DirItem]        # стоп-папки на диске, mod = StopList.MOD
    newly_stopped: list[DirItem]  # стали стоп-папкой только что


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


class Progress:
    """Счётчики индексации одного прохода. Отправляет ScanProgress в очередь."""

    def __init__(self, env: ScanEnv):
        self._env = env
        self.current = 0
        self.total = 0

    def set_total(self, total: int) -> None:
        self.total = total

    def tick(self, abs_img_path: str) -> None:
        self.current += 1
        self._env.queue.put(ScanProgress(
            kind="indexing",
            mf_alias=self._env.mf.mf_alias,
            current=self.current,
            total=self.total,
            dir_path=os.path.dirname(abs_img_path),
        ))


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


def _delete_thumb_file(rel_thumb_path: str) -> bool:
    """Удаляет файл миниатюры и пустую папку hashdir. False — если удалить не удалось."""
    abs_thumb_path = Mf.get_abs_thumb_path(rel_thumb_path)
    try:
        os.remove(abs_thumb_path)
    except FileNotFoundError:
        pass
    except Exception:
        print(traceback.format_exc())
        return False
    try:
        os.rmdir(os.path.dirname(abs_thumb_path))
    except OSError:
        pass
    return True


# ==========================================
# Один проход сканирования по одному Mf
# ==========================================

class MfScan:
    """
    Один проход по одному Mf. Окружение лежит в self.env,
    счётчики прогресса — в self.progress. Остальные поля — удобные ссылки.
    Проверку идентичности каталога делает вызывающий код (см. _run_mf).
    """

    def __init__(self, env: ScanEnv):
        self.env = env
        self.mf = env.mf
        self.engine = env.engine
        self.progress = Progress(env)
        self.changed = False  # были ли записи в БД

    # ---------- публичные точки входа ----------

    def check_identity(self) -> bool:
        """True, если каталог совпал с БД (или совпадение не требуется)."""
        sample = CatalogIdentity.sample_db_images(self.engine, self.mf.mf_alias)
        percent = CatalogIdentity.match_percent(self.mf, sample)
        if percent < MATCH_THRESHOLD:
            self.env.queue.put(PathMismatch(self.mf.mf_alias, percent))
            print("path mismatch", self.mf.mf_alias, percent)
            return False
        self.env.queue.put(PathCheckPassed(self.mf.mf_alias, percent))
        return True

    def run(self, force_full: bool) -> None:
        """Полный цикл: поиск изменений на диске → обновление папок и изображений."""
        db_dirs = self._load_db_dirs()
        if force_full:
            # полный пересказ: все папки помечаются как изменённые
            db_dirs = [replace(d, mod=PENDING_MOD) for d in db_dirs]
        elif not self._has_changes(db_dirs):
            print(self.mf.mf_alias, "not changed")
            return

        try:
            finder_dirs = self._load_finder_dirs()
        except ScanIncomplete:
            print("scan incomplete, root lost", self.mf.mf_alias)
            return
        if not finder_dirs:
            return

        # корень мог пропасть во время обхода: неполный список не сравниваем
        if not self.mf.is_root_alive():
            print("root lost after dirs scan, skip", self.mf.mf_alias)
            return

        diff = diff_dirs(finder_dirs, db_dirs)

        # удаление: пропавшие папки и папки, ставшие стоп-папками
        to_clean = diff.removed + diff.newly_stopped
        if to_clean and self.mf.is_root_alive():
            self._log_removed_dirs(finder_dirs, to_clean)
            self._remove_dirs(to_clean)

        # стоп-папки: только mod = StopList.MOD в Dirs, изображения не трогаем
        if diff.stopped and self.mf.is_root_alive():
            self._write_dirs(diff.stopped)

        # добавленные и изменённые: сначала папки с PENDING_MOD, затем картинки
        to_scan = diff.added + diff.changed
        if to_scan and self.mf.is_root_alive():
            self._write_dirs([replace(d, mod=PENDING_MOD) for d in to_scan])
            self.env.queue.put(DirsReady(self.mf.mf_alias))
            self.sync_images(to_scan)

    def sync_images(self, dirs: list[DirItem]) -> None:
        """Сравнивает изображения указанных папок с БД и применяет изменения."""
        try:
            finder_images = self._load_finder_images(dirs)
        except ScanIncomplete:
            print("scan incomplete, root lost", self.mf.mf_alias)
            return

        db_images = self._load_db_images(dirs)

        # диск мог пропасть во время сбора: неполный finder_images нельзя сравнивать
        if not self.mf.is_root_alive():
            print("root lost before compare, skip", self.mf.mf_alias)
            return

        removed, new = self._compare_images(finder_images, db_images)
        self.progress.set_total(len(removed) + len(new))

        self._del_thumbs(removed)
        self._add_thumbs(new)

        # реальные mod вместо PENDING_MOD
        if self.mf.is_root_alive():
            self._write_dirs(dirs)

    @staticmethod
    def build_dir_items(mf: Mf, dirs_to_scan: list[str]) -> list[DirItem]:
        """Превращает абсолютные пути в DirItem. Стоп-папки и недоступные пути пропускаются."""
        stop = StopList(mf.mf_stop_list)
        items: list[DirItem] = []
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
            if item not in items:
                items.append(item)
        return items

    # ---------- быстрая проверка изменений ----------

    def _has_changes(self, db_dirs: list[DirItem]) -> bool:
        """Быстрая проверка: есть ли вообще изменения. Нужна только как оптимизация."""
        if not db_dirs:
            return True

        stop = StopList(self.mf.mf_stop_list)
        base_path = self.mf.mf_path.strip(os.sep)

        for item in db_dirs:
            abs_dir_path = os.path.join(os.sep, base_path, item.rel_path.strip(os.sep))
            if not os.path.exists(abs_dir_path):
                return True

            if stop.contains(item.rel_path):
                # стоп-папка: mtime не отслеживаем, но если в БД ещё не стоит MOD,
                # нужно её перезаписать
                if item.mod != StopList.MOD:
                    return True
                continue

            try:
                stat = os.stat(abs_dir_path)
            except Exception as e:
                print("DirsChangeWatcher error", abs_dir_path, e)
                continue

            # PENDING_MOD (-1) всегда меньше mtime, поэтому папка считается изменённой
            if item.mod == StopList.MOD or int(stat.st_mtime) > item.mod:
                return True

        return False

    # ---------- чтение из БД ----------

    def _load_db_dirs(self) -> list[DirItem]:
        q = (
            sqlalchemy.select(Dirs.rel_dir_path, Dirs.mod)
            .where(Dirs.mf_alias == self.mf.mf_alias)
        )
        base = os.path.join(os.sep, self.mf.mf_path.strip(os.sep))
        with self.engine.connect() as conn:
            return [
                DirItem(
                    abs_path=os.path.join(base, rel_path.strip(os.sep)),
                    rel_path=rel_path,
                    mod=mod,
                )
                for rel_path, mod in conn.execute(q)
            ]

    def _load_db_images(self, dirs: list[DirItem]) -> list[ImgItem]:
        """Записи об изображениях из БД для указанных папок. Один запрос на весь Mf."""
        wanted = {d.rel_path for d in dirs}
        stmt = (
            sqlalchemy.select(
                Thumbs.rel_thumb_path,
                Thumbs.rel_img_path,
                Thumbs.size,
                Thumbs.mod,
            )
            .where(Thumbs.mf_alias == self.mf.mf_alias)
        )

        result: list[ImgItem] = []
        with self.engine.connect() as conn:
            for rel_thumb_path, rel_path, size, mod in conn.execute(stmt):
                if os.path.dirname(rel_path) not in wanted:
                    continue
                result.append(ImgItem(
                    abs_img_path=self.mf.create_abs_path(rel_path),
                    size=size,
                    mod=mod,
                    rel_thumb_path=rel_thumb_path,
                ))
        return result

    # ---------- обход диска ----------

    def _load_finder_dirs(self) -> list[DirItem]:
        """
        Список папок на диске:
        - стоп-папка попадает в список с mod = StopList.MOD, внутрь не заходим;
        - если недоступен сам корень, поднимает ScanIncomplete.
        """
        root = self.mf.mf_path
        self.env.queue.put(ScanProgress("search_dirs", self.mf.mf_alias))

        stop = StopList(self.mf.mf_stop_list)
        dirs: list[DirItem] = []
        stack = [root]

        while stack:
            path = stack.pop()
            try:
                scandir_iterator = os.scandir(path)
            except OSError:
                if path == root:
                    raise ScanIncomplete(root)  # диск пропал, список неполный
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

                    rel_path = self.mf.create_rel_path(entry.path)

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

    def _load_finder_images(self, dirs: list[DirItem]) -> list[ImgItem]:
        """
        Изображения с диска в указанных папках.
        Если недоступен корень, поднимает ScanIncomplete.
        Ошибка отдельной папки при живом корне пропускается.
        """
        root = self.mf.mf_path
        result: list[ImgItem] = []

        for d in dirs:
            try:
                scandir_iterator = os.scandir(d.abs_path)
            except OSError:
                if not os.path.isdir(root):
                    raise ScanIncomplete(root)
                print(traceback.format_exc())
                continue

            with scandir_iterator:
                for entry in scandir_iterator:
                    if not entry.path.endswith(ImageReader.ext_all):
                        continue
                    try:
                        stat = entry.stat()
                    except OSError:
                        print(traceback.format_exc())
                        continue
                    result.append(ImgItem(entry.path, int(stat.st_size), int(stat.st_mtime)))

        return result

    # ---------- сравнение ----------

    @staticmethod
    def _compare_images(
        finder_images: list[ImgItem],
        db_images: list[ImgItem],
    ) -> tuple[list[ImgItem], list[ImgItem]]:
        """Возвращает (удалённые с диска, новые на диске)."""
        finder_keys = {(i.abs_img_path, i.size, i.mod): i for i in finder_images}
        db_keys = {(i.abs_img_path, i.size, i.mod): i for i in db_images}

        removed = [img for key, img in db_keys.items() if key not in finder_keys]
        new = [img for key, img in finder_keys.items() if key not in db_keys]
        return removed, new

    # ---------- миниатюры ----------

    def _del_thumbs(self, removed: list[ImgItem]) -> None:
        for i in range(0, len(removed), BATCH_SIZE):
            if not self.mf.is_root_alive():
                print("root lost, stop thumbs deletion", self.mf.mf_alias)
                return

            chunk: list[ImgItem] = []
            for img in removed[i:i + BATCH_SIZE]:
                self.progress.tick(img.abs_img_path)
                if _delete_thumb_file(img.rel_thumb_path):
                    chunk.append(img)

            if chunk:
                self._delete_thumb_records(chunk)

    def _add_thumbs(self, new: list[ImgItem]) -> None:
        for i in range(0, len(new), BATCH_SIZE):
            if not self.mf.is_root_alive():
                print("root lost, stop thumbs creation", self.mf.mf_alias)
                return

            chunk = new[i:i + BATCH_SIZE]
            for img in chunk:
                self._create_thumb(img)
            self._upsert_thumb_records(chunk)

    def _create_thumb(self, img: ImgItem) -> None:
        """Миниатюра записывается в любом случае (для битых файлов — заглушка)."""
        self.progress.tick(img.abs_img_path)

        array_item = ImageArrayItem(img.abs_img_path)
        array_item.load()
        if array_item.image_array is None:
            thumbnail = Utils.get_broken_thumbnail()
        else:
            thumbnail = array_item.resize(Static.THUMB_MAX_SIZE)

        rel_img_path = self.mf.create_rel_path(img.abs_img_path)
        thumb_path = self.mf.create_abs_thumb_path(rel_img_path)

        if Utils.write_thumbnail(thumbnail, thumb_path) is None:
            Utils.write_thumbnail(Utils.get_broken_thumbnail(), thumb_path)

    def _delete_thumb_records(self, chunk: list[ImgItem]) -> None:
        if chunk:
            self.changed = True
        rel_thumb_paths = [i.rel_thumb_path for i in chunk]
        with self.engine.begin() as conn:
            thumb_ids = (
                sqlalchemy.select(Thumbs.id)
                .where(Thumbs.rel_thumb_path.in_(rel_thumb_paths))
                .where(Thumbs.mf_alias == self.mf.mf_alias)
            )
            conn.execute(
                sqlalchemy.delete(Properties.table)
                .where(Properties.thumb_id.in_(thumb_ids))
            )
            conn.execute(
                sqlalchemy.delete(Thumbs.table)
                .where(Thumbs.rel_thumb_path.in_(rel_thumb_paths))
                .where(Thumbs.mf_alias == self.mf.mf_alias)
            )

    def _upsert_thumb_records(self, chunk: list[ImgItem]) -> None:
        if chunk:
            self.changed = True
        rows = []
        for img in chunk:
            rel_img_path = self.mf.create_rel_path(img.abs_img_path)
            abs_thumb_path = self.mf.create_abs_thumb_path(rel_img_path)
            rel_thumb_path = Mf.get_rel_thumb_path(abs_thumb_path)
            rows.append({
                Thumbs.rel_img_path.name: rel_img_path,
                Thumbs.rel_thumb_path.name: rel_thumb_path,
                Thumbs.size.name: img.size,
                Thumbs.birth.name: 0,
                Thumbs.mod.name: img.mod,
                Thumbs.root.name: os.path.dirname(rel_img_path),
                Thumbs.name_key.name: "none",
                Thumbs.fav.name: 0,
                Thumbs.mf_alias.name: self.mf.mf_alias,
            })

        with self.engine.begin() as conn:
            # удаляем по тем же путям миниатюр, что и вставляем
            rel_thumb_paths = [r[Thumbs.rel_thumb_path.name] for r in rows]
            thumb_ids = (
                sqlalchemy.select(Thumbs.id)
                .where(Thumbs.rel_thumb_path.in_(rel_thumb_paths))
                .where(Thumbs.mf_alias == self.mf.mf_alias)
            )
            conn.execute(
                sqlalchemy.delete(Properties.table)
                .where(Properties.thumb_id.in_(thumb_ids))
            )
            conn.execute(
                sqlalchemy.delete(Thumbs.table)
                .where(Thumbs.rel_thumb_path.in_(rel_thumb_paths))
                .where(Thumbs.mf_alias == self.mf.mf_alias)
            )
            conn.execute(sqlalchemy.insert(Thumbs.table).values(rows))

    # ---------- папки в БД ----------

    def _write_dirs(self, dirs: list[DirItem]) -> None:
        """Записывает папки в Dirs одной транзакцией (delete + insert)."""
        if dirs:
            self.changed = True
        if not self.mf.is_root_alive():
            print("root lost, skip Dirs update", self.mf.mf_alias)
            return

        with self.engine.begin() as conn:
            conn.execute(
                sqlalchemy.delete(Dirs.table)
                .where(Dirs.rel_dir_path.in_([d.rel_path for d in dirs]))
                .where(Dirs.mf_alias == self.mf.mf_alias)
            )
            values = [
                {
                    Dirs.rel_dir_path.name: d.rel_path,
                    Dirs.mod.name: d.mod,
                    Dirs.mf_alias.name: self.mf.mf_alias,
                }
                for d in dirs
            ]
            if values:
                conn.execute(sqlalchemy.insert(Dirs.table), values)

    def _remove_dirs(self, dirs: list[DirItem]) -> None:
        if dirs:
            self.changed = True
        self._remove_dir_thumbs(dirs)
        self._delete_dir_records(dirs)

    def _remove_dir_thumbs(self, dirs: list[DirItem]) -> None:
        """Удаляет миниатюры удалённых папок и их записи в Thumbs пакетами."""
        with self.engine.begin() as conn:
            for d in dirs:
                prefix = Utils.escape_like(d.rel_path)
                thumbs = conn.execute(
                    sqlalchemy.select(Thumbs.rel_thumb_path)
                    .where(Thumbs.rel_img_path.ilike(f"{prefix}/%", escape="\\"))
                    .where(Thumbs.mf_alias == self.mf.mf_alias)
                ).scalars().all()

                for i in range(0, len(thumbs), BATCH_SIZE):
                    if not self.mf.is_root_alive():
                        print("root lost, stop removing thumbs", self.mf.mf_alias)
                        return
                    chunk = thumbs[i:i + BATCH_SIZE]
                    thumb_ids = (
                        sqlalchemy.select(Thumbs.id)
                        .where(Thumbs.rel_thumb_path.in_(chunk))
                        .where(Thumbs.mf_alias == self.mf.mf_alias)
                    )
                    conn.execute(
                        sqlalchemy.delete(Properties.table)
                        .where(Properties.thumb_id.in_(thumb_ids))
                    )
                    conn.execute(
                        sqlalchemy.delete(Thumbs.table)
                        .where(Thumbs.rel_thumb_path.in_(chunk))
                        .where(Thumbs.mf_alias == self.mf.mf_alias)
                    )
                    for rel_thumb_path in chunk:
                        _delete_thumb_file(rel_thumb_path)

    def _delete_dir_records(self, dirs: list[DirItem]) -> None:
        if not self.mf.is_root_alive():
            print("root lost, skip Dirs removal", self.mf.mf_alias)
            return

        with self.engine.begin() as conn:
            for d in dirs:
                conn.execute(
                    sqlalchemy.delete(Dirs.table)
                    .where(Dirs.rel_dir_path == d.rel_path)
                    .where(Dirs.mf_alias == self.mf.mf_alias)
                )

    # ---------- лог ----------

    def _log_removed_dirs(self, finder_dirs: list[DirItem], removed_dirs: list[DirItem]) -> None:
        finder_lines = [f"{i.abs_path}, {i.rel_path}" for i in finder_dirs]
        removed_lines = [f"{i.abs_path}, {i.rel_path}" for i in removed_dirs]
        sep = "==========="
        lines = [
            sep,
            datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
            f"Mf: {self.mf.mf_alias}, {self.mf.mf_path}",
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
            "\n\n",
        ]
        Tools.log("\n".join(lines))


# ==========================================
# Общие части точек входа
# ==========================================

@contextmanager
def _engine():
    """Engine создаётся внутри дочернего процесса и гарантированно освобождается."""
    engine = Dbase.create_engine()
    try:
        yield engine
    finally:
        engine.dispose()


def _run_mf(
    mf: Mf,
    engine: sqlalchemy.Engine,
    queue: Queue,
    action: Callable[[MfScan], None],
) -> bool:
    """
    Общая обёртка одного Mf: проверка доступности корня, проверка идентичности
    каталога (если выставлен old_mf_path) и выполнение действия. Исключения логируются.
    Возвращает True, если в БД были записаны изменения.
    """
    if not mf.is_root_alive():
        queue.put(ScanProgress("no_connection", mf.mf_alias))
        print("no connection", mf.mf_alias)
        sleep(3)
        return False

    scan = None
    try:
        scan = MfScan(ScanEnv(mf, engine, queue))
        if mf.old_mf_path is not None and not scan.check_identity():
            return False  # БД не трогаем
        action(scan)
    except Exception:
        print(traceback.format_exc())
    return scan is not None and scan.changed


# ==========================================
# Точки входа для дочернего процесса
# ==========================================

class BaseScaner:
    @staticmethod
    def start(mf_list: list[Mf], force_full: bool, queue: Queue) -> None:
        """Полный проход: поиск изменений по всему дереву каждого Mf."""
        with _engine() as engine:
            for mf in mf_list:
                print("scaner started", mf.mf_alias)
                changed = _run_mf(mf, engine, queue, lambda scan: scan.run(force_full))
                if changed:
                    queue.put(MfScanned(mf.mf_alias))
                print("scaner finished", mf.mf_alias)


class ForcedScaner:
    @staticmethod
    def start(mf: Mf, dirs: list[str], queue: Queue) -> None:
        """Точечный проход: только переданные папки, без обхода дерева."""
        print("single dir scaner started, mf:", mf.mf_alias)
        dir_items = MfScan.build_dir_items(mf, dirs)
        if dir_items:
            with _engine() as engine:
                _run_mf(mf, engine, queue, lambda scan: scan.sync_images(dir_items))
        print("single dir scaner finished, mf:", mf.mf_alias)