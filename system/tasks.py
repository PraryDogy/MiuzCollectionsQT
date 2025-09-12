import gc
import os
import re
from collections import defaultdict
from datetime import datetime

import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from sqlalchemy import select, update

from cfg import Dynamic, Cfg, Static

from .database import THUMBS, Dbase, DIRS
from .lang import Lng
from .main_folder import MainFolder
from .new_scaner.scaner_utils import (DbUpdater, DirsUpdater, HashdirUpdater,
                                      ImgCompator, ImgLoader, ImgRemover)
from .utils import ImgUtils, MainUtils, PixmapUtils, ThumbUtils, URunnable


class _CopyFilesSigs(QObject):
    finished_ = pyqtSignal(list)
    value_changed = pyqtSignal(int)
    progress_changed = pyqtSignal(tuple)
    file_changed = pyqtSignal(str)

class CopyFilesTask(URunnable):
    list_: list["CopyFilesTask"] = []
    copied_files_: list[list[str]] = []

    def __init__(self, dest: str, files: list):
        """
        Копирует файлы в новую директорию.

        Поведение:
        - Добавляется в список активных задач CopyFilesTask.list_
        - По завершении удаляется из этого списка
        - Список путей скопированных файлов добавляется в CopyFilesTask.copied_files

        Сигналы:
        - finished(list[str]) — список скопированных файлов
        - value_changed(int) — значение от 0 до 100 для QProgressBar
        """
        super().__init__()
        self.sigs = _CopyFilesSigs()
        self.files = files
        self.dest = dest

    @classmethod
    def get_current_tasks(cls):
        """
        Возвращает список действующих задач CopyFilesTask:   
        Сигналы:
        - finished(список путей к скопированным файлам)
        - value_changed(0-100, для передачи в QProgressBar)
        """
        return CopyFilesTask.list_
    
    @classmethod
    def copied_files(cls):
        """
        Возвращает список списков с путями к уже скопированным файлам.  
        Формат:[[<путь_к_файлу1>, <путь_к_файлу2>],...]
        """
        return CopyFilesTask.copied_files_

    def task(self):
        CopyFilesTask.list_.append(self)

        copied_size = 0
        files_dests = []

        try:
            total_size = sum(os.path.getsize(file) for file in self.files)
        except Exception as e:
            MainUtils.print_error()
            self.copy_files_finished(files_dests)
            return

        self.sigs.value_changed.emit(0)

        for x, file_path in enumerate(self.files, start=1):
            
            if not self.task_state.should_run():
                break

            self.sigs.progress_changed.emit(
                (x, len(self.files))
            )
            self.sigs.file_changed.emit(
                os.path.basename(file_path)
            )
            dest_path = os.path.join(self.dest, os.path.basename(file_path))
            files_dests.append(dest_path)

            try:
                with open(file_path, 'rb') as fsrc, open(dest_path, 'wb') as fdest:
                    while self.task_state.should_run():
                        buf = fsrc.read(1024*1024)
                        if not buf:
                            break
                        fdest.write(buf)
                        copied_size += len(buf)
                        percent = int((copied_size / total_size) * 100)
                        self.sigs.value_changed.emit(percent)
            except Exception as e:
                MainUtils.print_error()
                break
        
        self.copy_files_finished(files_dests)

    def copy_files_finished(self, files_dests: list[str]):
        self.sigs.value_changed.emit(100)
        self.sigs.finished_.emit(files_dests)
        CopyFilesTask.copied_files_.append(files_dests)
        CopyFilesTask.list_.remove(self)


class _FavSigs(QObject):
    finished_ = pyqtSignal(int)


class FavTask(URunnable):
    def __init__(self, rel_img_path: str, value: int):
        super().__init__()
        self.sigs = _FavSigs()
        self.rel_img_path = rel_img_path
        self.value = value

    def task(self):
        values = {"fav": self.value}
        q = update(THUMBS)
        q = q.where(THUMBS.c.short_src == self.rel_img_path)
        q = q.where(THUMBS.c.brand == MainFolder.current.name)
        q = q.values(**values)
        conn = Dbase.engine.connect()
        try:
            conn.execute(q)
            conn.commit()
            self.sigs.finished_.emit(self.value)
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()
        conn.close()


class _LoadCollListSigs(QObject):
    finished_ = pyqtSignal(tuple)


class LoadCollListTask(URunnable):
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.sigs = _LoadCollListSigs()
        self.conn = Dbase.engine.connect()

    def task(self) -> None:
        menus = self.get_collections_list()
        root = self.get_root()
        self.sigs.finished_.emit((menus, root))
        self.conn.close()

    def get_collections_list(self):
        q = select(THUMBS.c.coll)
        q = q.where(THUMBS.c.brand == self.main_folder.name)
        q = q.where(THUMBS.c.short_src.ilike("/%/%"))
        q = q.distinct()
        res = self.conn.execute(q).scalars()

        if not res:
            return list()

        if Cfg.abc_sort:
            return sorted(res, key=self.strip_to_first_letter)
        else:
            return list(res)
        
    def get_root(self):
        q = select(THUMBS.c.coll)
        q = q.where(THUMBS.c.brand == self.main_folder.name)
        q = q.where(THUMBS.c.short_src.ilike("/%"))
        q = q.where(THUMBS.c.short_src.not_ilike("/%/%"))
        q = q.distinct()
        return self.conn.execute(q).scalar_one_or_none()
    
    def strip_to_first_letter(self, s: str) -> str:
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)
        

class _LoadOneImgSigs(QObject):
    finished_ = pyqtSignal(tuple)


class LoadOneImgTask(URunnable):
    max_images_count = 50

    def __init__(self, img_path: str, cached_images: dict[str, QPixmap]):
        """
        Возвращает в сигнале finished_ (img_path, QImage)
        """
        super().__init__()
        self.sigs = _LoadOneImgSigs()
        self.img_path = img_path
        self.cached_images = cached_images

    def task(self):
        if self.img_path not in self.cached_images:
            img = ImgUtils.read_image(self.img_path)
            if img is not None:
                img = ImgUtils.desaturate_image(img, 0.2)
                self.qimage = PixmapUtils.qimage_from_array(img)
                self.cached_images[self.img_path] = self.qimage
                del img 
                gc.collect()
        else:
            self.qimage = self.cached_images.get(self.img_path)

        if not hasattr(self, "qimage"):
            self.qimage = None

        if len(self.cached_images) > self.max_images_count:
            self.cached_images.pop(next(iter(self.cached_images)))

        image_data = (self.img_path, self.qimage)
        self.sigs.finished_.emit(image_data)


class _OneFileInfoSigs(QObject):
    finished_ = pyqtSignal(dict)
    delayed_info = pyqtSignal(str)


class OneFileInfoTask(URunnable):
    max_row = 50
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.sigs = _OneFileInfoSigs()

    def task(self):
        mail_folder_path = MainFolder.current.get_curr_path()
        try:
            name = os.path.basename(self.url)
            _, type_ = os.path.splitext(name)
            stats = os.stat(self.url)
            size = MainUtils.get_f_size(stats.st_size)
            mod = MainUtils.get_f_date(stats.st_mtime)
            coll = MainUtils.get_coll_name(mail_folder_path, self.url)
            thumb_path = ThumbUtils.create_thumb_path(self.url)

            res = {
                Lng.file_name[Cfg.lng]: self.lined_text(name),
                Lng.type_[Cfg.lng]: type_,
                Lng.file_size[Cfg.lng]: size,
                Lng.place[Cfg.lng]: self.lined_text(self.url),
                Lng.thumb_path[Cfg.lng]: self.lined_text(thumb_path),
                Lng.changed[Cfg.lng]: mod,
                Lng.resol[Cfg.lng]: Lng.calculating[Cfg.lng],
                }
            
            self.sigs.finished_.emit(res)

            res = self.get_img_resol(self.url)
            if res:
                self.sigs.delayed_info.emit(res)
        
        except Exception as e:
            MainUtils.print_error()
            res = {
                Lng.file_name[Cfg.lng]: self.lined_text(os.path.basename(self.url)),
                Lng.place[Cfg.lng]: self.lined_text(self.url),
                Lng.type_[Cfg.lng]: self.lined_text(os.path.splitext(self.url)[0])
                }
            self.sigs.finished_.emit(res)

    def get_img_resol(self, img_path: str):
        img_ = ImgUtils.read_image(img_path)
        if img_ is not None and len(img_.shape) > 1:
            h, w = img_.shape[0], img_.shape[1]
            return f"{w}x{h}"
        else:
            return ""

    def lined_text(self, text: str):
        if len(text) > self.max_row:
            text = [
                text[i:i + self.max_row]
                for i in range(0, len(text), self.max_row)
                ]
            return "\n".join(text)
        else:
            return text


class MultiFileInfoTask(URunnable):
    max_row = 50
    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.img_path_list = img_path_list
        self.sigs = _OneFileInfoSigs()
    
    def task(self):
        names = [
            os.path.basename(i)
            for i in self.img_path_list
        ]
        names = names[:10]
        names = ", ".join(names)
        names = self.lined_text(names)
        if len(self.img_path_list) > 10:
            names = names + ", ..."

        res = {
            Lng.file_name[Cfg.lng]: names,
            Lng.total[Cfg.lng]: str(len(self.img_path_list)),
            Lng.file_size[Cfg.lng]: self.get_total_size()
        }
        self.sigs.finished_.emit(res)

    def get_total_size(self):
        total = 0
        for i in self.img_path_list:
            stats = os.stat(i)
            size_ = stats.st_size
            total += size_

        return MainUtils.get_f_size(total)

    def lined_text(self, text: str):
        if len(text) > self.max_row:
            text = [
                text[i:i + self.max_row]
                for i in range(0, len(text), self.max_row)
                ]
            return "\n".join(text)
        else:
            return text


class _RmFilesSigs(QObject):
    finished_ = pyqtSignal()
    reload_gui = pyqtSignal()


class RmFilesTask(URunnable):

    def __init__(self, img_path_list: list[str], main_folder: MainFolder):
        """
        Удаляет изображения.
        Удаляет миниатюры из hashdir, удаляет записи об изображениях из бд.   
        Запуск: UThreadPool.start   
        Сигналы: finished_(), progress_text(str), reload_gui()
        """
        super().__init__()
        self.sigs = _RmFilesSigs()
        self.img_path_list = img_path_list
        self.main_folder = main_folder

    def task(self):
        self.remove_files()
        self.sigs.reload_gui.emit()
        self.sigs.finished_.emit()

    def remove_files(self):
        """
        Удаляет файлы.  
        Возвращает список успешно удаленных файлов.
        """
        files: list = []
        for i in self.img_path_list:
            try:
                os.remove(i)
                files.append(i)
            except Exception as e:
                print("system, tasks, rm files task error", e)
        return files

    def remove_thumbs(self):
        """
        Удаляет из hashdir и из базы данных.
        """      
        thumb_path_list = [
            ThumbUtils.create_thumb_path(img_path)
            for img_path in self.img_path_list
        ]
        rel_thumb_path_list = [
            ThumbUtils.get_rel_thumb_path(thumb_path)
            for thumb_path in thumb_path_list
        ]
        
        # new_items пустой так как мы только удаляем thumbs из hashdir
        file_updater = HashdirUpdater(rel_thumb_path_list, [], self.task_state, self.main_folder)
        del_items, new_items = file_updater.run()
        
        # new_items пустой так как мы только удаляем thumbs из бд
        db_updater = DbUpdater(del_items, [], MainFolder.current)
        db_updater.run()

        # [(rel dir path, mod time), ...]
        worker_dirs = [
            (
                MainUtils.get_rel_path(MainFolder.current.curr_path, os.path.dirname(i)),
                os.stat(os.path.dirname(i)).st_mtime
            )
            for i in self.img_path_list
        ]

        dirs_updater = DirsUpdater(self.main_folder, worker_dirs, worker_dirs)
        dirs_updater.run()

class LoadDbImagesItem:
    __slots__ = ["qimage", "rel_img_path", "coll_name", "fav", "f_mod"]
    def __init__(self, qimage: QImage, rel_img_path: str, coll: str, fav: int, f_mod: str):
        self.qimage = qimage
        self.rel_img_path = rel_img_path
        self.coll_name = coll
        self.fav = fav
        self.f_mod = f_mod


class _LoadDbImagesSigs(QObject):
    finished_ = pyqtSignal(dict)


class LoadDbImagesTask(URunnable):
    def __init__(self):
        super().__init__()
        self.sigs = _LoadDbImagesSigs()
        self.conn = Dbase.engine.connect()

    def task(self):
        stmt = self.get_stmt()
        res: list[tuple] = self.conn.execute(stmt).fetchall()

        self.conn.close()
        self.create_dict(res)

    def create_dict(self, res: list[tuple]) -> dict[str, list[LoadDbImagesItem]] | dict:
        thumbs_dict = defaultdict(list[LoadDbImagesItem])

        if not res:
            self.sigs.finished_.emit(thumbs_dict)
            return

        for rel_img_path, rel_thumb_path, mod, coll, fav in res:
            rel_img_path: str
            if not rel_img_path.endswith(Static.ext_all):
                continue
            f_mod = datetime.fromtimestamp(mod).date()
            thumb_path = ThumbUtils.get_thumb_path(rel_thumb_path)
            thumb = ThumbUtils.read_thumb(thumb_path)
            if isinstance(thumb, ndarray):
                qimage = PixmapUtils.qimage_from_array(thumb)
            else:
                continue
            if Dynamic.date_start or Dynamic.date_end:
                f_mod = f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"
            else:
                f_mod = f"{Lng.months[Cfg.lng][str(f_mod.month)]} {f_mod.year}"
            item = LoadDbImagesItem(qimage, rel_img_path, coll, fav, f_mod)
            # если сортировка по дате изменения, то thumbs dict будет состоять
            # из списков (список апрель 2023, список март 2023, ...)
            # иначе thumbs dict будет иметь только один список, но с сортировкой
            # по дате добавления
            if Dynamic.sort_by_mod:
                thumbs_dict[f_mod].append(item)
            else:
                thumbs_dict[0].append(item)
        self.sigs.finished_.emit(thumbs_dict)

    def get_stmt(self) -> sqlalchemy.Select:
        stmt = sqlalchemy.select(
            THUMBS.c.short_src, # rel img path
            THUMBS.c.short_hash, # rel thumb path
            THUMBS.c.mod,
            THUMBS.c.coll,
            THUMBS.c.fav
            )
        
        stmt = stmt.limit(Static.thumbnails_step).offset(Dynamic.thumbnails_count)
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
            or_conditions = [
                THUMBS.c.short_src.ilike(f"%{f}%")
                for f in Dynamic.enabled_filters
            ]
            stmt = stmt.where(sqlalchemy.or_(*or_conditions))

        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt = stmt.where(THUMBS.c.short_src.ilike(f"%{text}%"))
            return stmt

        if any((Dynamic.date_start, Dynamic.date_end)):
            start, end = self.combine_dates(Dynamic.date_start, Dynamic.date_end)
            stmt = stmt.where(THUMBS.c.mod > start)
            stmt = stmt.where(THUMBS.c.mod < end)

        return stmt

    def combine_dates(self, date_start: datetime, date_end: datetime) -> tuple[float, float]:
        """
        Объединяет даты `Dynamic.date_start` и `Dynamic.date_end` с минимальным и максимальным временем суток 
        соответственно (00:00:00 и 23:59:59), и возвращает кортеж меток времени (timestamp).
        Возвращает:
        - Кортеж timestamp (начало, конец).
        """
        start = datetime.combine(date_start, datetime.min.time())
        end = datetime.combine(date_end, datetime.max.time().replace(microsecond=0))
        return datetime.timestamp(start), datetime.timestamp(end)


class _LoadSortedDirsSigs(QObject):
    finished_ = pyqtSignal(dict)


class LoadSortedDirsTask(URunnable):
    def __init__(self, path: str):
        """
        сигнал finished возвращает словарь: путь - имя
        """
        super().__init__()
        self.sigs = _LoadSortedDirsSigs()
        self.path = path

    def task(self):
        if not os.path.exists(self.path):
            self.sigs.finished_.emit({})
        else:
            dirs = {i.path: i.name for i in os.scandir(self.path) if i.is_dir()}
            sorted_dirs = dict(
                sorted(dirs.items(), key=lambda kv: self.strip_to_first_letter(kv[1]))
            )
            self.sigs.finished_.emit(sorted_dirs)

    def strip_to_first_letter(self, s: str) -> str:
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)


class _CustomScanerSigs(QObject):
    finished_ = pyqtSignal()
    progress_text = pyqtSignal(str)


class CustomScanerTask(URunnable):
    def __init__(self, main_folder: MainFolder, scan_dir: str):
        """
        Аналог полноценного сканера, но принимает список директорий
        и выполняет сканирование для каждой из них.
        """
        super().__init__()
        self.sigs = _CustomScanerSigs()
        self.main_folder = main_folder
        self.scan_dir = scan_dir
        if main_folder.curr_path:
            self.true_name = os.path.basename(main_folder.curr_path)
        else:
            self.true_name = os.path.basename(main_folder.paths[0])
        self.alias = main_folder.name
        
    def task(self):
        rel_path = MainUtils.get_rel_path(self.main_folder.curr_path, self.scan_dir)
        mod_time = int(os.stat(self.scan_dir).st_mtime)
        new_dirs = [(rel_path, mod_time), ]

        img_loader = ImgLoader(new_dirs, self.main_folder, self.task_state)
        img_loader.progress_text.connect(self.sigs.progress_text.emit)
        finder_images = img_loader.finder_images()
        db_images = img_loader.db_images()
        if not finder_images or not self.task_state.should_run():
            print(self.main_folder.name, "no finder images")
            self.sigs.progress_text.emit("")
            return
                
        img_compator = ImgCompator(finder_images, db_images)
        del_images, new_images = img_compator.run()

        hashdir_updater = HashdirUpdater(del_images, new_images, self.task_state, self.main_folder)
        hashdir_updater.progress_text.connect(self.sigs.progress_text.emit)
        del_images, new_images = hashdir_updater.run()

        db_updater = DbUpdater(del_images, new_images, self.main_folder)
        db_updater.run()

        if not self.task_state.should_run():
            self.sigs.progress_text.emit("")
            return

        del_dirs = new_dirs
        dirs_updater = DirsUpdater(self.main_folder, del_dirs, new_dirs)
        dirs_updater.run()
        
        # скрываем текст
        self.sigs.progress_text.emit("")

        if new_images or del_images:
            self.sigs.finished_.emit()
            

class _ResetDataSigs(QObject):
    finished_ = pyqtSignal()


class ResetDataTask(URunnable):
    def __init__(self, main_folder_name: str):
        super().__init__()
        self.sigs = _ResetDataSigs()
        self.main_folder_name = main_folder_name
        
    def task(self):
        conn = Dbase.engine.connect()
        q = sqlalchemy.delete(DIRS)
        q = q.where(DIRS.c.brand == self.main_folder_name)
        try:
            conn.execute(q)
            conn.commit()
        except Exception as e:
            print("tasks, reset data task error", e)
        
        self.sigs.finished_.emit()