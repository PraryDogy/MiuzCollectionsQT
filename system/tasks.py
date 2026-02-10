import os
import shutil
from collections import defaultdict
from datetime import datetime

import numpy as np
import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtGui import QImage

from cfg import Dynamic, Static, cfg

from .database import Dbase, Dirs, Thumbs
from .lang import Lng
from .main_folder import Mf
from .shared_utils import ImgUtils
from .utils import Utils


class TaskState:
    __slots__ = ["_should_run", "_finished"]

    def __init__(self, value=True, finished=False):
        self._should_run = value
        self._finished = finished

    def should_run(self):
        return self._should_run
    
    def set_should_run(self, value: bool):
        self._should_run = value

    def set_finished(self, value: bool):
        self._finished = value

    def finished(self):
        return self._finished


class URunnable(QRunnable):
    def __init__(self):
        """
        Внимание:   
        Не переопределяйте метод self.run() как в QRunnable, переопределите
        метод self.task()

        self.task_state:
        - для управления QRunnable.
        - Можно остановить задачу self.task_state.set_should_run(False)
        - По завершению задачи self.task_state.finished() вернет True
        """
        super().__init__()
        self.task_state = TaskState()
    
    def run(self):
        try:
            self.task()
        finally:
            self.task_state.set_finished(True)
            # if self in UThreadPool.tasks:
                # QTimer.singleShot(5000, lambda: UThreadPool.tasks.remove(self))

    def task(self):
        raise NotImplementedError("Переопредели метод task() в подклассе.")
    

class UThreadPool:
    pool: QThreadPool = None
    tasks: list[URunnable] = []

    @classmethod
    def init(cls):
        cls.pool = QThreadPool.globalInstance()

    @classmethod
    def start(cls, runnable: URunnable):
        """
        Запускает URunnable, добавляет в список UThreadPool.tasks
        """
        # cls.tasks.append(runnable)
        cls.pool.start(runnable)


class FavManager(URunnable):
    """
    Менеджер избранного для изображений.
    
    Сигналы:
    - finished_(int): возвращает новое значение избранного после обновления.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(int)

    def __init__(self, rel_path: str, value: int):
        super().__init__()
        self.sigs = FavManager.Sigs()
        self.rel_path = rel_path
        self.value = value
        self.conn = Dbase.engine.connect()

    def task(self):
        """Обновляет поле 'fav' в БД и эмитит сигнал с результатом."""
        try:
            q = (
                sqlalchemy.update(Thumbs.table)
                .where(Thumbs.rel_img_path == self.rel_path)
                .where(Thumbs.mf_alias == Mf.current.alias)
                .values(fav=self.value)
            )
            self.conn.execute(q)
            self.conn.commit()
            self.sigs.finished_.emit(self.value)
        except Exception as e:
            Utils.print_error()
            self.conn.rollback()
        finally:
            self.conn.close()


class DbImagesLoader(URunnable):
    """
    Загружает изображения из БД и формирует словарь для UI.

    Сигнал finished_ возвращает словарь:
    - ключ — дата изменения изображения (или 0 при сортировке по добавлению),
    - значение — список LoadDbImagesItem для соответствующей даты.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(dict)

    class Item:
        __slots__ = ["qimage", "rel_path", "fav", "f_mod", "mod"]
        def __init__(self, qimage: QImage, rel_path: str, fav: int, f_mod: str, mod: str):
            self.qimage = qimage
            self.rel_path = rel_path
            self.fav = fav
            self.f_mod = f_mod
            self.mod = mod

    def __init__(self):
        super().__init__()
        self.sigs = DbImagesLoader.Sigs()
        self.conn = Dbase.engine.connect()

    def task(self):
        try:
            res = self._load_images()
        except Exception as e:
            print("DbImagesLoader error:", e)
        finally:
            self.sigs.finished_.emit(res)
            self.conn.close()

    def _load_images(self):
        stmt = self.get_stmt()
        res: list[tuple] = self.conn.execute(stmt).fetchall()
        return self.create_dict(res)

    def create_dict(self, res: list[tuple]):
        thumbs_dict = defaultdict(list[DbImagesLoader.Item])
        if not res:
            return {}

        for rel_path, rel_thumb_path, mod, fav in res:
            if not rel_path.endswith(ImgUtils.ext_all):
                continue

            f_mod = datetime.fromtimestamp(mod).date()
            thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
            thumb = Utils.read_thumb(thumb_path)
            if not isinstance(thumb, ndarray):
                continue

            qimage = Utils.qimage_from_array(thumb)

            if Dynamic.date_start or Dynamic.date_end:
                f_mod = f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"
            else:
                f_mod = f"{Lng.months[cfg.lng][str(f_mod.month)]} {f_mod.year}"

            date_time = datetime.fromtimestamp(mod)
            month = Lng.months_genitive_case[cfg.lng][str(date_time.month)]
            mod = f"{date_time.day} {month} {date_time.year}"

            item = DbImagesLoader.Item(qimage, rel_path, fav, f_mod, mod)

            if Dynamic.sort_by_mod:
                thumbs_dict[f_mod].append(item)
            else:
                thumbs_dict[0].append(item)

        return thumbs_dict

    def get_stmt(self) -> sqlalchemy.Select:
        stmt = sqlalchemy.select(
            Thumbs.rel_img_path,
            Thumbs.rel_thumb_path,
            Thumbs.mod,
            Thumbs.fav
        ).limit(Static.thumbs_load_limit).offset(Dynamic.loaded_thumbs)
        if Dynamic.sort_by_mod:
            stmt = stmt.order_by(-Thumbs.mod)
        else:
            stmt = stmt.order_by(-Thumbs.id)
        stmt = stmt.where(Thumbs.mf_alias == Mf.current.alias)
        stmt = stmt.where(Thumbs.rel_img_path.ilike(f"{Dynamic.current_dir}/%"))
        if Dynamic.filter_favs:
            stmt = stmt.where(Thumbs.fav == 1)
        if Dynamic.filter_only_folder:
            stmt = stmt.where(Thumbs.rel_img_path.not_ilike(f"{Dynamic.current_dir}/%/%"))
        if Dynamic.filters_enabled:
            stmt = stmt.where(
                sqlalchemy.or_(*[Thumbs.rel_img_path.ilike(f"%{f}%") for f in Dynamic.filters_enabled])
            )
        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt = stmt.where(Thumbs.rel_img_path.ilike(f"%{text}%"))
        if any((Dynamic.date_start, Dynamic.date_end)):
            start, end = self.combine_dates(Dynamic.date_start, Dynamic.date_end)
            stmt = stmt.where(Thumbs.mod > start).where(Thumbs.mod < end)
        return stmt

    def combine_dates(self, date_start: datetime, date_end: datetime) -> tuple[float, float]:
        """
        Преобразует даты в timestamp для фильтрации:
        - date_start → 00:00:00
        - date_end → 23:59:59
        Возвращает кортеж (start_timestamp, end_timestamp).
        """
        start = datetime.combine(date_start, datetime.min.time())
        end = datetime.combine(date_end, datetime.max.time().replace(microsecond=0))
        return datetime.timestamp(start), datetime.timestamp(end)


class MfDataCleaner(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal()

    """
    Сбрасывает данные в БД для пересканирования:
    
    - Удаляет записи из THUMBS, если файл миниатюры отсутствует.
    - Удаляет запись о папке `mf` из DIRS.
    """

    def __init__(self, mf_name: str):
        super().__init__()
        self.sigs = MfDataCleaner.Sigs()
        self.mf_name = mf_name
        self.conn = Dbase.engine.connect()

    def task(self):
        try:
            self._task()
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print("tasks, reset data task error:", e)
        finally:
            self.conn.close()
            self.sigs.finished_.emit()

    def _task(self):
        abs_path_list: list[str] = []
        stmt = (
            sqlalchemy.select(Thumbs.rel_img_path, Thumbs.rel_thumb_path)
            .where(Thumbs.mf_alias == self.mf_name)
        )
        res = self.conn.execute(stmt)
        for rel_path, rel_thumb_path in res:
            if not rel_path or not rel_thumb_path:
                continue
            abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
            if os.path.exists(abs_thumb_path):
                stmt = sqlalchemy.delete(Thumbs.table).where(Thumbs.rel_img_path == rel_path)
                self.conn.execute(stmt)
                abs_path_list.append(abs_thumb_path)
        self.conn.commit()

        for i in abs_path_list:
            try:
                os.remove(i)
                parent = os.path.dirname(i)
                if not os.listdir(parent):
                    shutil.rmtree(parent)
            except Exception as e:
                print("system>tasks>MfDataCleaner remove thumb error", e)

        stmt = sqlalchemy.delete(Dirs.table).where(Thumbs.mf_alias == self.mf_name)
        self.conn.execute(stmt)
        self.conn.commit()


class DbDirsLoader(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal(list)

    def __init__(self, mf: Mf):
        super().__init__()
        self.sigs = DbDirsLoader.Sigs()
        self.mf = mf
        self.conn = Dbase.engine.connect()

    def task(self):
        try:
            res = self._task()
            self.sigs.finished_.emit(res)
        except Exception as e:
            print("DbDirsLoader error:", e)
            import traceback
            print(traceback.format_exc())

    def _task(self):
        stmt = (
            sqlalchemy.select(Dirs.rel_dir_path)
            .where(Dirs.mf_alias == self.mf.alias)
        )

        res = list(self.conn.execute(stmt).scalars())
        return self.fill_missing_paths(res)
        
    def fill_missing_paths(self, paths: list[str]) -> list[str]:
        """Добавляет недостающие промежуточные директории."""
        full_set = set()
        for p in paths:
            parts = p.strip("/").split("/")
            curr = ""
            for part in parts:
                curr = curr + "/" + part if curr else "/" + part
                full_set.add(curr)
        return sorted(full_set)


class HashDirSize(URunnable):
    
    class Sigs(QObject):
        finished_ = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.sigs = HashDirSize.Sigs()
        self.conn = Dbase.engine.connect()

    def task(self):
        try:
            self.sigs.finished_.emit(
                self._task()
            )
        except Exception as e:
            print("HashDirSize error", e)

    def _task(self):
        main_folder_sizes = {}
        for i in Mf.list_:
            stmt = (
                sqlalchemy.select(Thumbs.rel_thumb_path)
                .where(Thumbs.mf_alias == i.alias)
            )
            res = list(self.conn.execute(stmt).scalars())
            size = sum([
                os.path.getsize(Utils.get_abs_thumb_path(i))
                for i in res
                if os.path.exists(Utils.get_abs_thumb_path(i))
            ])
            if i.get_available_path():
                real_name = os.path.basename(i.curr_path)
            else:
                real_name = os.path.basename(i.paths[0])
            name = f"{real_name} ({i.alias})"
            main_folder_sizes[name] = {"size": size, "total": len(res)}
        return main_folder_sizes
    

class ImgArrayQImage(URunnable):
    
    class Sigs(QObject):
        finished_ = pyqtSignal(QImage)

    def __init__(self, img_array: np.ndarray):
        super().__init__()
        self.sigs = ImgArrayQImage.Sigs()
        self.img_array = img_array

    def task(self):
        self.sigs.finished_.emit(
            Utils.qimage_from_array(self.img_array)
        )