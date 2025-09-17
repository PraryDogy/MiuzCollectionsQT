import gc
import os
import re
from collections import defaultdict
from datetime import datetime

import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from cfg import Cfg, Dynamic, Static

from .database import DIRS, THUMBS, Dbase
from .lang import Lng
from .main_folder import MainFolder
from .shared_utils import ReadImage, SharedUtils
from .utils import MainUtils


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


class CopyFilesManager(URunnable):
    """
    Копирует файлы в указанную директорию с обновлением прогресса.

    Сигналы:
    - finished_(list[str]): список скопированных файлов
    - value_changed(int): значение от 0 до 100 для QProgressBar
    - progress_changed(tuple): (текущий индекс, общее количество файлов)
    - file_changed(str): имя текущего копируемого файла
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(list)
        value_changed = pyqtSignal(int)
        progress_changed = pyqtSignal(tuple)
        file_changed = pyqtSignal(str)

    def __init__(self, dest: str, files: list[str]):
        super().__init__()
        self.sigs = CopyFilesManager.Sigs()
        self.files = files
        self.dest = dest

    def task(self):
        """Основной метод с обработкой исключений."""
        try:
            self._finish_copy(self._copy_files())
        except Exception as e:
            MainUtils.print_error()
            self._finish_copy([])

    def _copy_files(self):
        """Приватный метод: копирует все файлы и обновляет прогресс."""
        copied_size = 0
        files_dests = []

        try:
            total_size = sum(os.path.getsize(f) for f in self.files)
        except Exception as e:
            print("CopyFilesManager error:", e)
            return files_dests

        self.sigs.value_changed.emit(0)

        for idx, file_path in enumerate(self.files, start=1):
            if not self.task_state.should_run():
                break

            dest_path = os.path.join(self.dest, os.path.basename(file_path))
            if dest_path == file_path:
                print("нельзя копировать файл в себя:", dest_path)
                continue
            files_dests.append(dest_path)

            self.sigs.progress_changed.emit((idx, len(self.files)))
            self.sigs.file_changed.emit(os.path.basename(file_path))

            copied_size = self._copy_file(file_path, dest_path, copied_size, total_size)

        return files_dests

    def _copy_file(self, src: str, dst: str, copied_size: int, total_size: int) -> int:
        """Приватный метод для копирования одного файла с обновлением прогресса."""
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while self.task_state.should_run():
                buf = fsrc.read(1024 * 1024)
                if not buf:
                    break
                fdst.write(buf)
                copied_size += len(buf)
                percent = int((copied_size / total_size) * 100)
                self.sigs.value_changed.emit(percent)
        return copied_size

    def _finish_copy(self, files_dests: list[str]):
        """Приватный метод для завершения копирования и эмита сигнала finished_."""
        self.sigs.value_changed.emit(100)
        self.sigs.finished_.emit(files_dests)


class FavManager(URunnable):
    """
    Менеджер избранного для изображений.
    
    Сигналы:
    - finished_(int): возвращает новое значение избранного после обновления.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(int)

    def __init__(self, rel_img_path: str, value: int):
        super().__init__()
        self.sigs = FavManager.Sigs()
        self.rel_img_path = rel_img_path
        self.value = value
        self.conn = Dbase.engine.connect()

    def task(self):
        """Обновляет поле 'fav' в БД и эмитит сигнал с результатом."""
        try:
            q = (
                sqlalchemy.update(THUMBS)
                .where(THUMBS.c.short_src == self.rel_img_path)
                .where(THUMBS.c.brand == MainFolder.current.name)
                .values(fav=self.value)
            )
            self.conn.execute(q)
            self.conn.commit()
            self.sigs.finished_.emit(self.value)
        except Exception as e:
            MainUtils.print_error()
            self.conn.rollback()
        finally:
            self.conn.close()


class OneImgLoader(URunnable):
    """
    Загружает одно изображение, десатурирует его и кэширует в словаре.

    Сигналы:
    - finished_(tuple): возвращает кортеж (img_path, QPixmap или None)
    """

    max_images_count = 50

    class Sigs(QObject):
        finished_ = pyqtSignal(tuple)

    def __init__(self, abs_img_path: str, cached_images: dict[str, QPixmap]):
        """
        :param img_path: путь к изображению
        :param cached_images: словарь кэшированных изображений {путь: QPixmap}
        """
        super().__init__()
        self.sigs = OneImgLoader.Sigs()
        self.abs_img_path = abs_img_path
        self.cached_images = cached_images

    def task(self):
        """Выполняет загрузку изображения и эмитит сигнал."""
        try:
            self.sigs.finished_.emit(
                (self.abs_img_path, self._load_image())
            )
        except Exception as e:
            print("OneImgLoader error:", e)
            self.sigs.finished_.emit(
                (self.abs_img_path, None)
            )

    def _load_image(self):
        """Приватный метод: загружает и кэширует изображение."""
        if self.abs_img_path in self.cached_images:
            return self.cached_images.get(self.abs_img_path)

        img = ReadImage.read_image(self.abs_img_path)
        if img is None:
            return None

        img = MainUtils.desaturate_image(img, 0.2)
        qimage = MainUtils.qimage_from_array(img)
        self.cached_images[self.abs_img_path] = qimage

        del img
        gc.collect()

        # Если кэш превышает лимит, удаляем самый старый элемент
        if len(self.cached_images) > self.max_images_count:
            first_key = next(iter(self.cached_images))
            self.cached_images.pop(first_key)

        return qimage


class OneFileInfo(URunnable):
    """
    Загружает информацию об одном файле и формирует сигналы для UI.

    Сигналы:
    - finished_(dict): информация о файле (имя, тип, размер, путь, миниатюра, дата изменения).
    - delayed_info(str): разрешение изображения (emited после вычисления).
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(dict)
        delayed_info = pyqtSignal(str)

    max_row = 50

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.sigs = OneFileInfo.Sigs()

    def task(self):
        """Выполняет сбор информации и эмит сигналы."""
        try:
            res = self._gather_info()
            self.sigs.finished_.emit(res)

            resol = self.get_img_resol(self.url)
            if resol:
                self.sigs.delayed_info.emit(resol)
        except Exception as e:
            MainUtils.print_error()
            res = {
                Lng.file_name[Cfg.lng]: self.lined_text(os.path.basename(self.url)),
                Lng.place[Cfg.lng]: self.lined_text(self.url),
                Lng.type_[Cfg.lng]: self.lined_text(os.path.splitext(self.url)[0]),
            }
            self.sigs.finished_.emit(res)

    def _gather_info(self) -> dict:
        """Приватный метод: собирает всю информацию о файле."""
        mail_folder_path = MainFolder.current.get_curr_path()
        name = os.path.basename(self.url)
        _, type_ = os.path.splitext(name)
        stats = os.stat(self.url)
        size = SharedUtils.get_f_size(stats.st_size)
        mod = SharedUtils.get_f_date(stats.st_mtime)
        thumb_path = MainUtils.create_abs_hash(self.url)

        res = {
            Lng.file_name[Cfg.lng]: self.lined_text(name),
            Lng.type_[Cfg.lng]: type_,
            Lng.file_size[Cfg.lng]: size,
            Lng.place[Cfg.lng]: self.lined_text(self.url),
            Lng.thumb_path[Cfg.lng]: self.lined_text(thumb_path),
            Lng.changed[Cfg.lng]: mod,
            Lng.resol[Cfg.lng]: Lng.calculating[Cfg.lng],
        }

        return res

    def get_img_resol(self, img_path: str) -> str:
        """Возвращает разрешение изображения в формате 'WxH' или пустую строку."""
        img_ = ReadImage.read_image(img_path)
        if img_ is not None and len(img_.shape) > 1:
            h, w = img_.shape[0], img_.shape[1]
            return f"{w}x{h}"
        return ""

    def lined_text(self, text: str) -> str:
        """Разбивает текст на строки длиной не более max_row символов."""
        if len(text) > self.max_row:
            return "\n".join(
                text[i:i + self.max_row]
                for i in range(0, len(text), self.max_row)
            )
        return text


class MultiFileInfo(URunnable):
    """
    Формирует информацию о нескольких файлах.

    Сигналы:
    - finished_(dict): возвращает словарь с информацией:
        - языковая ссылка: имена файлов,
        - языковая ссылка: общее количество файлов,
        - языковая ссылка: суммарный размер файлов.
    """
    max_row = 50

    class Sigs(QObject):
        finished_ = pyqtSignal(dict)
        delayed_info = pyqtSignal(str)

    def __init__(self, img_paths: list[str]):
        super().__init__()
        self.img_paths = img_paths
        self.sigs = MultiFileInfo.Sigs()

    def task(self):
        """Выполняет сбор информации и эмит сигнал с результатом."""
        try:
            self.sigs.finished_.emit(self._prepare_info())
        except Exception as e:
            print("MultiFileInfo error:", e)
            self.sigs.finished_.emit({})

    def _prepare_info(self) -> dict:
        """Приватный метод: собирает словарь информации о файлах."""
        # Формируем строку имён (не более 10)
        names = [os.path.basename(p) for p in self.img_paths][:10]
        names = ", ".join(names)
        names = self.lined_text(names)
        if len(self.img_paths) > 10:
            names += ", ..."

        return {
            Lng.file_name[Cfg.lng]: names,
            Lng.total[Cfg.lng]: str(len(self.img_paths)),
            Lng.file_size[Cfg.lng]: self.get_total_size()
        }

    def get_total_size(self) -> str:
        """Возвращает суммарный размер всех файлов в удобочитаемом формате."""
        total = sum(os.stat(p).st_size for p in self.img_paths)
        return SharedUtils.get_f_size(total)

    def lined_text(self, text: str) -> str:
        """Разбивает строку на строки длиной не более max_row символов."""
        if len(text) > self.max_row:
            return "\n".join(text[i:i + self.max_row] for i in range(0, len(text), self.max_row))
        return text


class FilesRemover(URunnable):
    """
    Удаляет указанные файлы.

    Запуск через: UThreadPool.start
    Сигналы:
    - finished_(): вызывается после завершения удаления.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal()

    def __init__(self, img_paths: list[str]):
        super().__init__()
        self.sigs = FilesRemover.Sigs()
        self.img_paths = img_paths

    def task(self):
        # Здесь не нужен try/except, ошибки обрабатываются в _remove_files
        self._remove_files()
        self.sigs.finished_.emit()

    def _remove_files(self) -> list[str]:
        """
        Удаляет файлы по списку self.img_paths.

        Возвращает список успешно удалённых файлов.
        """
        deleted_files = []
        for path in self.img_paths:
            try:
                os.remove(path)
                deleted_files.append(path)
            except Exception as e:
                print("FilesRemover error:", e)
        return deleted_files


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
        __slots__ = ["qimage", "rel_img_path", "coll_name", "fav", "f_mod"]
        def __init__(self, qimage: QImage, rel_img_path: str, coll: str, fav: int, f_mod: str):
            self.qimage = qimage
            self.rel_img_path = rel_img_path
            self.coll_name = coll
            self.fav = fav
            self.f_mod = f_mod

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

        for rel_img_path, rel_thumb_path, mod, coll, fav in res:
            if not rel_img_path.endswith(Static.ext_all):
                continue

            f_mod = datetime.fromtimestamp(mod).date()
            thumb_path = MainUtils.get_abs_hash(rel_thumb_path)
            thumb = MainUtils.read_thumb(thumb_path)
            if not isinstance(thumb, ndarray):
                continue

            qimage = MainUtils.qimage_from_array(thumb)

            if Dynamic.date_start or Dynamic.date_end:
                f_mod = f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"
                # f_mod = f"{Dynamic.date_start} - {Dynamic.date_end}"
            else:
                f_mod = f"{Lng.months[Cfg.lng][str(f_mod.month)]} {f_mod.year}"

            item = DbImagesLoader.Item(qimage, rel_img_path, coll, fav, f_mod)

            if Dynamic.sort_by_mod:
                thumbs_dict[f_mod].append(item)
            else:
                thumbs_dict[0].append(item)

        return thumbs_dict

    def get_stmt(self) -> sqlalchemy.Select:
        stmt = sqlalchemy.select(
            THUMBS.c.short_src,
            THUMBS.c.short_hash,
            THUMBS.c.mod,
            THUMBS.c.coll,
            THUMBS.c.fav
        ).limit(Static.thumbnails_step).offset(Dynamic.thumbnails_count)

        stmt = stmt.where(THUMBS.c.brand == MainFolder.current.name)

        if Dynamic.sort_by_mod:
            stmt = stmt.order_by(-THUMBS.c.mod)
        else:
            stmt = stmt.order_by(-THUMBS.c.id)

        if Dynamic.current_dir == Static.NAME_FAVS:
            stmt = stmt.where(THUMBS.c.fav == 1)
        else:
            stmt = stmt.where(THUMBS.c.short_src.ilike(f"{Dynamic.current_dir}/%"))

        if Dynamic.enabled_filters:
            stmt = stmt.where(
                sqlalchemy.or_(*[THUMBS.c.short_src.ilike(f"%{f}%") for f in Dynamic.enabled_filters])
            )

        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt = stmt.where(THUMBS.c.short_src.ilike(f"%{text}%"))

        if any((Dynamic.date_start, Dynamic.date_end)):
            start, end = self.combine_dates(Dynamic.date_start, Dynamic.date_end)
            stmt = stmt.where(THUMBS.c.mod > start).where(THUMBS.c.mod < end)

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


class SortedDirsLoader(URunnable):
    """
    Загружает директории из указанного пути и сортирует их по имени.

    Сигнал finished_ возвращает словарь {путь: имя}:
    - ключ — абсолютный путь к директории,
    - значение — имя директории.
    """

    class Sigs(QObject):
        finished_ = pyqtSignal(dict)

    def __init__(self, path: str):
        """
        :param path: путь к папке, из которой нужно загрузить поддиректории
        """
        super().__init__()
        self.sigs = SortedDirsLoader.Sigs()
        self.path = path

    def task(self):
        """Выполняет загрузку директорий с обработкой ошибок."""
        try:
            sorted_dirs = self._load_dirs()
            self.sigs.finished_.emit(sorted_dirs)
        except Exception as e:
            print("SortedDirsLoader error:", e)
            self.sigs.finished_.emit({})

    def _load_dirs(self) -> dict:
        """Приватный метод: собирает и сортирует директории."""
        if not os.path.exists(self.path):
            return {}

        dirs = {i.path: i.name for i in os.scandir(self.path) if i.is_dir()}
        sorted_dirs = dict(
            sorted(dirs.items(), key=lambda kv: self.strip_to_first_letter(kv[1]))
        )
        return sorted_dirs
    
    def strip_to_first_letter(self, s: str) -> str:
        """Удаляет начальные символы, которые не являются буквами, для сортировки."""
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)


class MainFolderDataCleaner(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal()

    """
    Сбрасывает данные в БД для пересканирования:
    
    - Удаляет записи из THUMBS, если файл миниатюры отсутствует.
    - Удаляет запись о папке `main_folder` из DIRS.
    """

    def __init__(self, main_folder_name: str):
        super().__init__()
        self.sigs = MainFolderDataCleaner.Sigs()
        self.main_folder_name = main_folder_name
        self.conn = Dbase.engine.connect()

    def task(self):
        try:
            self._task()
        except Exception as e:
            print("tasks, reset data task error:", e)
        finally:
            self.conn.close()
            self.sigs.finished_.emit()

    def _task(self):
        # Удаляем битые миниатюры
        stmt = sqlalchemy.select(THUMBS.c.short_src, THUMBS.c.short_hash)
        for rel_img_path, rel_thumb_path in self.conn.execute(stmt):
            if not os.path.exists(MainUtils.get_abs_hash(rel_thumb_path)):
                self.conn.execute(
                    sqlalchemy.delete(THUMBS).where(THUMBS.c.short_src == rel_img_path)
                )
        self.conn.commit()

        # Удаляем папку
        stmt = sqlalchemy.delete(DIRS).where(DIRS.c.brand == self.main_folder_name)
        self.conn.execute(stmt)
        self.conn.commit()


class LoadDbMenu(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal()

    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.sigs = LoadDbMenu.Sigs()
        self.conn = Dbase.engine.connect()

    def task(self):
        try:
            self.sigs.finished_.emit(self._task())
        except Exception as e:
            print("LoadDbMenu error", e)

    def _task(self):
        ...