import os
import traceback
from collections import defaultdict
from datetime import datetime

import cv2
import numpy as np
import sqlalchemy
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtGui import QImage

from cfg import Cfg, Dynamic, Static

from .database import Dbase, Dirs, Thumbs
from .items import DbImagesItem, HashDirSizeItem
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
                    Thumbs.fav.name: self.value
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
        finished_ = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.sigs = DbImagesLoader.Sigs()

    def task(self):
        try:
            with Dbase.main_engine.connect() as conn:
                stmt = self.get_stmt()
                res = conn.execute(stmt).fetchall()
            if res:
                image_items = self.create_dict(res)
                self.sigs.finished_.emit(image_items)
            else:
                self.sigs.finished_.emit([])
        except Exception as e:
            print(traceback.format_exc())
            self.sigs.finished_.emit({})

    def create_dict(self, res: list[tuple]):
        # thumbs_dict = defaultdict(list[DbImagesItem])
        thumbs = []

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
            month_year = f"{month_} {date_.year}"

            item = DbImagesItem(
                rel_img_path=rel_img_path,
                rel_thumb_path=rel_thumb_path,
                fav=fav,
                qimage=qimage,
                day_month_year=day_month_year,
                month_year=month_year
            )
            thumbs.append(item)
        return thumbs

    def get_stmt(self):
        rel_path = Dynamic.current_dir
        if rel_path == os.sep:
            rel_path = ""
        stmt = (
            sqlalchemy.select(
                Thumbs.rel_img_path,
                Thumbs.rel_thumb_path,
                Thumbs.mod,
                Thumbs.fav
            )
            .where(Thumbs.mf_alias == Mf.current_mf.mf_alias)
            .where(Thumbs.rel_img_path.ilike(f"{rel_path}/%"))
            .order_by(-Thumbs.mod if Dynamic.sort_by_mod else -Thumbs.id)
            .limit(Static.thumbs_load_limit)
            .offset(Dynamic.loaded_thumbs)
        )

        if Dynamic.filter_favs:
            stmt = stmt.where(Thumbs.fav == 1)

        if Dynamic.filter_only_folder:
            two_slash = f"{rel_path}/%/%"
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

# ТУТ ТУ Т УТУТТУТУТУТу
        if Dynamic.thumb_path_set:
            # lst = list(Dynamic.thumb_names_list)
            stmt = stmt.where(Thumbs.rel_thumb_path.in_(Dynamic.thumb_path_set))

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
                sqlalchemy.select(Thumbs.root)
                .where(Thumbs.mf_alias == self.mf.mf_alias)
            ).distinct()
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
        finished_ = pyqtSignal(list)

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
        items: list[HashDirSizeItem] = []
        with Dbase.main_engine.begin() as conn:
            for mf in Mf.items:
                stmt = (
                    sqlalchemy.select(Thumbs.rel_thumb_path)
                    .where(Thumbs.mf_alias == mf.mf_alias)
                )
                rel_thumb_paths = conn.execute(stmt).scalars().all()
                size = sum([
                    os.path.getsize(Utils.get_abs_thumb_path(x))
                    for x in rel_thumb_paths
                    if os.path.exists(Utils.get_abs_thumb_path(x))
                ])
                item = HashDirSizeItem(
                    mf=mf,
                    size=size,
                    total_images=len(rel_thumb_paths)
                )
                items.append(item)
        return items
    

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



class ImageSearcher(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal(set)

    def __init__(self, src_img, hash_dir=None, max_side=500):
        """
        Инициализация класса поиска.
        :param src_img: Исходное изображение (numpy array)
        :param hash_dir: Путь к базовой директории с подпапками (по умолчанию из Static)
        :param max_side: Максимальный размер стороны для масштабирования исходника
        """
        super().__init__()
        self.sigs = ImageSearcher.Sigs()
        self.hash_dir = hash_dir if hash_dir else Static.external_hashdir
        self.max_side = max_side
        self.sift = cv2.SIFT_create()
        self.thumb_path_set: set[str] = set()
        
        # Предварительная подготовка эталона при создании объекта
        self.processed_src = self._prepare_source(src_img)
        self.src_hist = self._get_color_histogram(self.processed_src)
        
        gray_src = cv2.cvtColor(self.processed_src, cv2.COLOR_BGR2GRAY)
        _, self.des_src = self.sift.detectAndCompute(gray_src, None)

    def _get_color_histogram(self, image):
        """Вычисляет нормализованную гистограмму в пространстве HSV."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist

    def _compare_sift(self, thumbnail):
        """Проверка миниатюры по ключевым точкам (SIFT)."""
        gray_thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2GRAY)
        kp_thumb, des_thumb = self.sift.detectAndCompute(gray_thumbnail, None)

        if self.des_src is None or des_thumb is None or len(des_thumb) < 10:
            return 0

        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        matches = flann.knnMatch(des_thumb, self.des_src, k=2)

        good_matches = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

        if not kp_thumb:
            return 0
            
        score = min(int((len(good_matches) / len(kp_thumb)) * 100), 100) 
        return score

    def _prepare_source(self, src_img):
        """Масштабирует исходное изображение, если оно больше лимита."""
        h_src, w_src = src_img.shape[:2]
        if max(h_src, w_src) > self.max_side:
            scale = self.max_side / max(h_src, w_src)
            return cv2.resize(src_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return src_img.copy()

    def start(self, min_sift=70, min_color=60):
        """
        Запускает процесс сканирования директории и сравнения файлов.
        :param min_sift: Порог совпадения по точкам SIFT
        :param min_color: Порог совпадения по цвету
        """
        # Сканирование директорий
        for i in os.scandir(self.hash_dir):
            if i.is_dir():
                for x in os.scandir(i.path):
                    if x.name.endswith(".jpg"):
                        thumbnail = cv2.imread(x.path)
                        if thumbnail is None:
                            continue
                        
                        # 1. Проверка по цвету
                        thumb_hist = self._get_color_histogram(thumbnail)
                        hist_similarity = cv2.compareHist(self.src_hist, thumb_hist, cv2.HISTCMP_CORREL)
                        color_score = int(hist_similarity * 100)
                        
                        # 2. Проверка по точкам
                        sift_score = self._compare_sift(thumbnail)
                        
                        # Условие соответствия OR
                        if sift_score > min_sift or color_score > min_color:
                            rel_path = Utils.get_rel_thumb_path(x.path)
                            self.thumb_path_set.add(rel_path)

    def task(self):
        self.start(min_sift=70, min_color=60)
        self.sigs.finished_.emit(self.thumb_path_set)
