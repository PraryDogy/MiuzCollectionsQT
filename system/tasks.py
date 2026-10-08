import os
import traceback
from dataclasses import dataclass
from datetime import datetime, date

import cv2
# import imagehash
import numpy as np
import sqlalchemy
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap

from cfg import Dynamic, JsonData, Static

from .database import Dbase, Dirs, Properties, Thumbs
from .lang import Lng
from .main_folder import Mf
from .shared_utils import ImgUtils
from .utils import Utils

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QSize, QRectF
from PyQt6.QtGui import QImage, QPainter, QPainterPath, QColor


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


@dataclass(slots=True)
class DbImagesLoaderItem:
    rel_img_path: str
    rel_thumb_path: str
    fav: int
    qimage: QImage
    day_month_year: str
    month_year: str


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

            # qimages = []
            img_bgr = cv2.imread(abs_thumb_path_)
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            ind = Dynamic.current_pixmap_size_index
            current_size = Static.THUMB_WID_PIXMAP_SIZE[ind] * Utils.DPR

            qimage = Utils.pyqt_qimage_from_array(img_rgb)
            qimage_scaled = qimage.scaled(
                current_size, current_size,
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                transformMode=Qt.TransformationMode.SmoothTransformation
            )
            qimage_scaled.setDevicePixelRatio(Utils.DPR)

            date_ = datetime.fromtimestamp(mod).date()
            month_ = Lng.months[JsonData.lng_index][str(date_.month)]
            month_gen_ = Lng.months_gen[JsonData.lng_index][str(date_.month)]
            day_month_year = f"{date_.day} {month_gen_} {date_.year}"
            month_year = f"{month_} {date_.year}"

            item = DbImagesLoaderItem(
                rel_img_path=rel_img_path,
                rel_thumb_path=rel_thumb_path,
                fav=fav,
                qimage=qimage_scaled,
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
            .order_by(-Thumbs.mod if Dynamic.sort_by_mod_enabled else -Thumbs.id)
            .limit(Static.THUMBS_LOAD_LIMIT)
            .offset(Dynamic.loaded_thumbs)
        )

        if Dynamic.favs_tag_enabled:
            stmt = stmt.where(Thumbs.fav == 1)

        if Dynamic.no_subfolders_tag_enabled:
            two_slash = f"{rel_path}/%/%"
            stmt = (
                stmt
                .where(Thumbs.rel_img_path.not_ilike(two_slash))
            )

        if Dynamic.word_tags_list:
            filters = [
                Thumbs.rel_img_path.ilike(f"%{filter}%")
                for filter in Dynamic.word_tags_list
            ]
            stmt = stmt.where(sqlalchemy.or_(*filters))

        if Dynamic.search_words_list:
            search_conditions = [
                Thumbs.rel_img_path.ilike(f"%{word}%")
                for word in Dynamic.search_words_list
            ]

            stmt = stmt.where(sqlalchemy.or_(*search_conditions))

        if any((Dynamic.py_date_start, Dynamic.py_date_end)):
            start, end = self.combine_dates(
                Dynamic.py_date_start,
                Dynamic.py_date_end
            )
            stmt = stmt.where(Thumbs.mod > start, Thumbs.mod < end)

        if Dynamic.img_search_thumb_paths:
            stmt = stmt.where(Thumbs.rel_thumb_path.in_(Dynamic.img_search_thumb_paths))

        return stmt

    def combine_dates(self, date_start, date_end):
        """
        Преобразует даты в timestamp для фильтрации:
        - Если нет date_start -> 01.01.1970 00:00:00
        - Если нет date_end -> Сегодня 23:59:59
        Возвращает кортеж (start_timestamp, end_timestamp).
        """
        # Если из UI пришел None, задаем крайние точки прямо перед запросом
        if date_start is None:
            date_start = date(1970, 1, 1)
            
        if date_end is None:
            date_end = date.today()

        start = datetime.combine(
            date_start,
            datetime.min.time()
        )
        end = datetime.combine(
            date_end,
            datetime.max.time().replace(microsecond=0)
        )

        # Вызов .timestamp() напрямую у объекта работает чище
        return start.timestamp(), end.timestamp()


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
        # сейчас он просто удаляет dirs и несуществующие миниатюры
        # а надо удалять dirs для перескана
        # удалять дубликаты из базы данных?
        # удалять несуществующие пути к миниатюрам
        # broken_thumb если есть то попытаться пересканить



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


@dataclass(slots=True)
class HashDirSizeItem:
    mf: Mf
    size: int
    total_images: int


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
        qimage = Utils.pyqt_qimage_from_array(self.img_array)
        self.sigs.finished_.emit(qimage)


class ImagePreviewTask(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal(QImage)

    def __init__(self, img_array: np.ndarray, size: tuple = None, radius: float = 16.0):
        super().__init__()
        self.sigs = ImgArrayQImage.Sigs()
        self.size_ = size      # Логический размер виджета: tuple(width, height)
        self.radius = radius   # Логический радиус скругления углов
        self.img_array = img_array

    def task(self):
        orig_qimg = Utils.pyqt_qimage_from_array(self.img_array)
        if not self.size_:
            # Если размер не задан, просто применяем DPR к оригиналу
            orig_qimg.setDevicePixelRatio(Static.DPR)
            self.sigs.finished_.emit(orig_qimg)
            return

        # 1. Распаковываем кортеж и считаем физический размер в пикселях с учетом DPR
        logic_w, logic_h = self.size_
        physical_w = int(logic_w * Static.DPR)
        physical_h = int(logic_h * Static.DPR)
        target_size_physical = QSize(physical_w, physical_h)

        # ==========================================
        # ШАГ 1: Размытый фон (в физических пикселях)
        # ==========================================
        bg_qimg = orig_qimg.scaled(
            target_size_physical, 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        )

        # Трюк быстрого размытия (Downscale -> Upscale)
        # Используем IgnoreAspectRatio, чтобы блюр равномерно заполнил любой прямоугольник
        micro_size = QSize(15, 15)
        bg_blurred = bg_qimg.scaled(micro_size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        bg_blurred = bg_blurred.scaled(target_size_physical, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # ==========================================
        # ШАГ 2: Картинка на передний план (Foreground)
        # ==========================================
        fg_qimg = orig_qimg.scaled(
            target_size_physical, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

        # ==========================================
        # ШАГ 3: Композиция и скругление углов
        # ==========================================
        # Создаем холст в ФИЗИЧЕСКИХ пикселях
        final_qimg = QImage(target_size_physical, QImage.Format.Format_ARGB32_Premultiplied)
        final_qimg.fill(Qt.GlobalColor.transparent)

        painter = QPainter(final_qimg)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 3.1. Делаем обтравочную маску с заданным радиусом
        # Умножаем заданный радиус на DPR для корректного отображения
        physical_radius = self.radius * Static.DPR
        
        clip_path = QPainterPath()
        clip_path.addRoundedRect(
            QRectF(0, 0, target_size_physical.width(), target_size_physical.height()), 
            physical_radius, 
            physical_radius
        )
        painter.setClipPath(clip_path)

        # 3.2. Рисуем размытый фон
        bg_rect = bg_blurred.rect()
        bg_rect.moveCenter(final_qimg.rect().center())
        painter.drawImage(bg_rect, bg_blurred)

        # 3.3. Рисуем легкое затемнение
        painter.fillRect(final_qimg.rect(), QColor(0, 0, 0, 60))

        # 3.4. Рисуем саму картинку поверх фона
        fg_rect = fg_qimg.rect()
        fg_rect.moveCenter(final_qimg.rect().center())
        painter.drawImage(fg_rect, fg_qimg)

        painter.end() 

        # ==========================================
        # ШАГ 4: Применяем DPR к финализированному QImage
        # ==========================================
        final_qimg.setDevicePixelRatio(Static.DPR)

        self.sigs.finished_.emit(final_qimg)


class ImageSearcher(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal()
        found_image = pyqtSignal(str)

    def __init__(self, src_img: np.ndarray, similarity_value: int, mf: Mf):
        super().__init__()
        self.sigs = ImageSearcher.Sigs()
        self.src_img = src_img
        self.similarity_value = similarity_value / 100
        self.mf = mf
        self.current_count = 0
        self.total_count = 0
        self.stop_flag = False
        self.chunk_size = 500

        self.thumbs_with_hist = []
        self.thumbs_no_hist = []

        hsv1 = cv2.cvtColor(src_img, cv2.COLOR_BGR2HSV)
        self.hist1 = cv2.calcHist([hsv1], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(self.hist1, self.hist1, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

    def stop_task(self):
        self.stop_flag = True

    def task(self):
        self.start()
        if not self.stop_flag:
            self.sigs.finished_.emit()

    def start(self):
        self.split_by_histogram()
        self.set_total_count()
        self.manage_thumbs_no_hist()
        self.manage_thumbs_with_hist()
        
    def split_by_histogram(self):
        select_hist = (
            sqlalchemy.select(Thumbs.id, Thumbs.rel_thumb_path, Properties.bytes_hist)
            .join(Properties.table, Thumbs.id == Properties.thumb_id, isouter=True)
            .where(Thumbs.mf_alias == self.mf.mf_alias)
        )
        with Dbase.main_engine.connect() as conn:
            hist_result = conn.execute(select_hist)

        for id_, rel_thumb_path, bytes_hist in hist_result:
            if bytes_hist is None:
                self.thumbs_no_hist.append((id_, rel_thumb_path, bytes_hist))
            else:
                decoded_hist = self.decode_hist(bytes_hist)
                new_data = (id_, rel_thumb_path, decoded_hist)
                self.thumbs_with_hist.append(new_data)

    def set_total_count(self):
        self.total_count = len(self.thumbs_no_hist)

    def manage_thumbs_no_hist(self):
        db_data = []

        for x, (id_, rel_thumb_path, no_hist) in enumerate(self.thumbs_no_hist):
            if self.stop_flag:
                print("индексация гистограмм остановлена")
                return
            self.current_count += 1
            abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
            hist = self.calc_hist(abs_thumb_path)
            bytes_hist = hist.tobytes()
            self.thumbs_with_hist.append((id_, rel_thumb_path, hist))
            db_data.append((id_, rel_thumb_path, bytes_hist))
            if x % self.chunk_size == 0:
                self.write_to_db(db_data)
                db_data.clear()
        if db_data:
            self.write_to_db(db_data)
            db_data.clear()

    def calc_hist(self, abs_thumb_path: str):
        img = ImgUtils.read_img(abs_thumb_path)
        hsv2 = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)        
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist2, hist2, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist2

    def decode_hist(self, bytes_hist: bytes) -> np.ndarray:
        flat_array = np.frombuffer(bytes_hist, dtype=np.float32)
        hist = flat_array.reshape(50, 60)
        return hist

    def write_to_db(sefl, db_data: list):
        values = [
            {
                Properties.thumb_id.name: id_,
                Properties.bytes_hist.name: bytes_hist,
            }
            for id_, rel_thumb_path, bytes_hist in db_data
        ]
        stmt = (
            sqlalchemy.insert(Properties.table)
            .values(values)
        )
        with Dbase.main_engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def manage_thumbs_with_hist(self):
        for id_, rel_thumb_path, hist in self.thumbs_with_hist:
            result = self.compare_hist(hist)
            if result > self.similarity_value:
                self.sigs.found_image.emit(rel_thumb_path)

    def compare_hist(self, hist2):
        similarity = cv2.compareHist(self.hist1, hist2, cv2.HISTCMP_CORREL)
        return similarity




# class ImageSearcher(URunnable):

#     class Sigs(QObject):
#         finished_ = pyqtSignal()
#         found_image = pyqtSignal(str)

#     def __init__(self, src_img: np.ndarray, similarity_value: int, mf: Mf):
#         super().__init__()
#         self.sigs = ImageSearcher.Sigs()
#         self.src_img = src_img
#         self.similarity_value = similarity_value / 100
#         self.mf = mf
#         self.current_count = 0
#         self.total_count = 0
#         self.stop_flag = False
#         self.chunk_size = 500

#         self.sift = cv2.SIFT_create()
#         self.matcher = cv2.BFMatcher()

#         gray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
#         self.kp1, self.des1 = self.sift.detectAndCompute(gray, None)

#     def stop_task(self):
#         self.stop_flag = True

#     def task(self):
#         self.start()
#         if not self.stop_flag:
#             self.sigs.finished_.emit()

#     def start(self):
#         self.load_thumbs()
#         self.search()

#     def load_thumbs(self):
#         select = sqlalchemy.select(
#             Thumbs.id,
#             Thumbs.rel_thumb_path
#         ).where(
#             Thumbs.mf_alias == self.mf.mf_alias
#         ).order_by(
#             Thumbs.mod.desc()
#         )

#         with Dbase.main_engine.connect() as conn:
#             self.thumbs = conn.execute(select).fetchall()

#         self.total_count = len(self.thumbs)

#     def search(self):
#         if self.des1 is None:
#             return

#         for id_, rel_thumb_path in self.thumbs:
#             if self.stop_flag:
#                 return

#             self.current_count += 1
#             abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)

#             try:
#                 img = ImgUtils.read_img(abs_thumb_path)
#                 similarity = self.compare_sift(img)

#                 if similarity >= self.similarity_value:
#                     self.sigs.found_image.emit(rel_thumb_path)

#             except Exception as e:
#                 print(f"SIFT error: {abs_thumb_path}: {e}")

#     def compare_sift(self, img: np.ndarray) -> float:
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         kp2, des2 = self.sift.detectAndCompute(gray, None)

#         if des2 is None:
#             return 0.0

#         matches = self.matcher.knnMatch(self.des1, des2, k=2)

#         good = []
#         for m, n in matches:
#             if m.distance < 0.7 * n.distance:
#                 good.append(m)

#         if len(good) < 4:
#             return 0.0

#         src_pts = np.float32(
#             [self.kp1[m.queryIdx].pt for m in good]
#         ).reshape(-1, 1, 2)

#         dst_pts = np.float32(
#             [kp2[m.trainIdx].pt for m in good]
#         ).reshape(-1, 1, 2)

#         try:
#             _, mask = cv2.findHomography(
#                 src_pts,
#                 dst_pts,
#                 cv2.RANSAC,
#                 5.0
#             )
#         except cv2.error:
#             return 0.0

#         if mask is None:
#             return 0.0

#         inliers = mask.ravel().sum()

#         return inliers / len(good)