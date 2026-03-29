import os
import traceback
from collections import defaultdict
from datetime import datetime

import numpy as np
import sqlalchemy
from .items import DbImagesItem
from numpy import ndarray
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtGui import QImage

from cfg import Cfg, Dynamic, Static

from .database import ClmnNames, Dbase, Dirs, Thumbs
from .lang import Lng
from .main_folder import Mf
from .shared_utils import ImgUtils
from .utils import Utils


class URunnable(QRunnable):
    def __init__(self):
        super().__init__()
    
    def run(self):
        try:
            self.task()
        except Exception as e:
            print(traceback.format_exc())

    def task(self):
        raise NotImplementedError("Переопредели метод task() в подклассе.")
    

class UThreadPool:
    pool: QThreadPool = None

    @classmethod
    def init(cls):
        cls.pool = QThreadPool.globalInstance()

    @classmethod
    def start(cls, runnable: URunnable):
        cls.pool.start(runnable)


class SetFav(URunnable):
    """
    Менеджер избранного для изображений.
    Сигналы:
    - finished_(int): возвращает новое значение избранного после обновления.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(int)

    def __init__(self, rel_path: str, value: int):
        super().__init__()
        self.sigs = SetFav.Sigs()
        self.rel_path = rel_path
        self.value = value

    def task(self):
        with Dbase.main_engine.begin() as conn:
            stmt = (
                sqlalchemy.update(Thumbs.table)
                .where(Thumbs.rel_img_path==self.rel_path)
                .where(Thumbs.mf_alias==Mf.current_mf.mf_alias)
                .values({
                    ClmnNames.fav: self.value
                })
            )
            conn.execute(stmt)

        self.sigs.finished_.emit(self.value)


class DbImagesLoader(URunnable):
    """
    Загружает изображения из БД и формирует словарь для UI.

    Сигнал finished_ возвращает словарь:
    - ключ — дата изменения изображения (или 0 при сортировке по добавлению),
    - значение — список LoadDbImagesItem для соответствующей даты.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.sigs = DbImagesLoader.Sigs()

    def task(self):
        try:
            with Dbase.main_engine.connect() as conn:
                stmt = self.get_stmt()
                res = conn.execute(stmt).fetchall()
            if res:
                image_items_dict = self.create_dict(res)
                self.sigs.finished_.emit(image_items_dict)
            else:
                self.sigs.finished_.emit({})
        except Exception as e:
            print(traceback.format_exc())
            self.sigs.finished_.emit({})

    def create_dict(self, res: list[tuple]):
        thumbs_dict = defaultdict(list[DbImagesItem])

        for rel_img_path, rel_thumb_path, mod, fav in res:
            abs_thumb_path_ = Utils.get_abs_thumb_path(rel_thumb_path)

            if not os.path.exists(abs_thumb_path_):
                continue

            array_ = ImgUtils.read_thumb(abs_thumb_path_)
            qimage = Utils.qimage_from_array(array_)

            date_ = datetime.fromtimestamp(mod).date()
            month_ = Lng.months[Cfg.lng_index][str(date_.month)]
            month_gen_ = Lng.months_gen[Cfg.lng_index][str(date_.month)]
            day_month_year = f"{date_.day} {month_gen_} {date_.year}"

            if Dynamic.date_start or Dynamic.date_end:
                month_year = f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"
            else:
                month_year = f"{month_} {date_.year}"

            item = DbImagesItem(
                rel_img_path=rel_img_path,
                rel_thumb_path=rel_thumb_path,
                fav=fav,
                qimage=qimage,
                day_month_year=day_month_year,
                month_year=month_year
            )

            if Dynamic.sort_by_mod:
                thumbs_dict[month_year].append(item)
            else:
                thumbs_dict["any_key"].append(item)

        return thumbs_dict

    def get_stmt(self):
        stmt = (
            sqlalchemy.select(
                Thumbs.rel_img_path,
                Thumbs.rel_thumb_path,
                Thumbs.mod,
                Thumbs.fav
            )
            .where(Thumbs.mf_alias == Mf.current_mf.mf_alias)
            .where(Thumbs.rel_img_path.ilike(f"{Dynamic.current_dir}/%"))
            .order_by(-Thumbs.mod if Dynamic.sort_by_mod else -Thumbs.id)
            .limit(Static.thumbs_load_limit)
            .offset(Dynamic.loaded_thumbs)
        )

        if Dynamic.filter_favs:
            stmt = stmt.where(Thumbs.fav == 1)

        if Dynamic.filter_only_folder:
            two_slash = f"{Dynamic.current_dir}/%/%"
            stmt = (
                stmt
                .where(Thumbs.rel_img_path.not_ilike(two_slash))
            )

        if Dynamic.filters_enabled:
            filters = [
                Thumbs.rel_img_path.ilike(f"%{filter}%")
                for filter in Dynamic.filters_enabled
            ]
            stmt = stmt.where(sqlalchemy.or_(*filters))

        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt = stmt.where(Thumbs.rel_img_path.ilike(f"%{text}%"))

        if any((Dynamic.date_start, Dynamic.date_end)):
            start, end = self.combine_dates(
                Dynamic.date_start,
                Dynamic.date_end
            )
            stmt = stmt.where(Thumbs.mod > start, Thumbs.mod < end)

        return stmt

    def combine_dates(
            self,
            date_start: datetime,
            date_end: datetime
        ):
        """
        Преобразует даты в timestamp для фильтрации:
        - date_start → 00:00:00
        - date_end → 23:59:59
        Возвращает кортеж (start_timestamp, end_timestamp).
        """
        start = datetime.combine(
            date_start,
            datetime.min.time()
        )
        end = datetime.combine(
            date_end,
            datetime.max.time().replace(microsecond=0)
        )
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
        self.mf_alias = mf_name

    def task(self):
        try:
            self._task()
        except Exception as e:
            print(traceback.format_exc())
        self.sigs.finished_.emit()

    def _task(self):
        with Dbase.main_engine.begin() as conn:
            stmt = (
                sqlalchemy.select(Thumbs.rel_thumb_path)
                .where(Thumbs.mf_alias == self.mf_alias)
            )
            rel_thumb_paths = conn.execute(stmt).scalars().all()

            stmt = (
                sqlalchemy.delete(Dirs.table)
                .where(Dirs.mf_alias == self.mf_alias)
            )
            conn.execute(stmt)

            non_exist_thumbs = []

            for i in rel_thumb_paths:
                abs_thumb_path = Utils.get_abs_thumb_path(i)
                if not os.path.exists(abs_thumb_path):
                    non_exist_thumbs.append(i)
            
            stmt = (
                sqlalchemy.delete(Thumbs.table)
                .where(Thumbs.rel_thumb_path.in_(non_exist_thumbs))
                .where(Thumbs.mf_alias==self.mf_alias)
            )

            conn.execute(stmt)


class DbDirsLoader(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal(list)

    def __init__(self, mf: Mf):
        super().__init__()
        self.sigs = DbDirsLoader.Sigs()
        self.mf = mf

    def task(self):
        try:
            res = self._task()
        except Exception as e:
            print(traceback.format_exc())
            res = []
        self.sigs.finished_.emit(res)

    def _task(self):
        with Dbase.main_engine.begin() as conn:
            stmt = (
                sqlalchemy.select(Dirs.rel_dir_path)
                .where(Dirs.mf_alias == self.mf.mf_alias)
            )
            res = conn.execute(stmt).scalars().all()
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

    def task(self):
        try:
            self.sigs.finished_.emit(
                self._task()
            )
        except Exception as e:
            print("HashDirSize error", e)

    def _task(self):
        with Dbase.main_engine.begin() as conn:
            main_folder_sizes = {}
            for i in Mf.mf_list:
                stmt = (
                    sqlalchemy.select(Thumbs.rel_thumb_path)
                    .where(Thumbs.mf_alias == i.mf_alias)
                )
                res = conn.execute(stmt).scalars().all()
                size = sum([
                    os.path.getsize(Utils.get_abs_thumb_path(i))
                    for i in res
                    if os.path.exists(Utils.get_abs_thumb_path(i))
                ])
                main_folder_sizes[i.mf_alias] = {"size": size, "total": len(res)}
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