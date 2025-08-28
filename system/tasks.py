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

from cfg import Dynamic, Static, JsonData

from .database import THUMBS, Dbase
from .filters import SystemFilter, UserFilter
from .lang import Lang
from .main_folder import MainFolder
from .old_scaner.scaner_utils import DbUpdater, HashdirUpdater
from .utils import (ImgUtils, MainUtils, PixmapUtils, ThumbUtils, URunnable,
                    UThreadPool)


class CopyFilesSignals(QObject):
    finished_ = pyqtSignal(list)
    value_changed = pyqtSignal(int)


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
        self.signals_ = CopyFilesSignals()
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

        self.signals_.value_changed.emit(0)

        for file_path in self.files:
            
            if not self.task_state.should_run():
                break

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
                        self.signals_.value_changed.emit(percent)
            except Exception as e:
                MainUtils.print_error()
                break
        
        self.copy_files_finished(files_dests)

    def copy_files_finished(self, files_dests: list[str]):
        self.signals_.value_changed.emit(100)
        self.signals_.finished_.emit(files_dests)
        CopyFilesTask.copied_files_.append(files_dests)
        CopyFilesTask.list_.remove(self)


class FavSignals(QObject):
    finished_ = pyqtSignal(int)


class FavTask(URunnable):
    def __init__(self, rel_img_path: str, value: int):
        super().__init__()
        self.signals_ = FavSignals()
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
            self.signals_.finished_.emit(self.value)
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()
        conn.close()


class MenuSignals(QObject):
    finished_ = pyqtSignal(list)


class LoadCollListTask(URunnable):
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.signals_ = MenuSignals()

    def task(self) -> None:
        menus = self.get_collections_list()
        try:
            self.signals_.finished_.emit(menus)
        except RuntimeError as e:
            MainUtils.print_error()

    def get_collections_list(self) -> list[dict]:
        conn = Dbase.engine.connect()
        q = select(THUMBS.c.coll)
        q = q.where(THUMBS.c.brand == self.main_folder.name)
        q = q.distinct()
        res = conn.execute(q).scalars()
        conn.close()

        if not res:
            return list()

        if JsonData.abc_sort:
            return sorted(res, key=self.strip_to_first_letter)
        else:
            return list(res)
    
    def strip_to_first_letter(self, s: str) -> str:
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)
        

class LoadImageSignals(QObject):
    finished_ = pyqtSignal(tuple)


class LoadImage(URunnable):
    max_images_count = 50

    def __init__(self, img_path: str, cached_images: dict[str, QPixmap]):
        """
        Возвращает в сигнале finished_ (img_path, QImage)
        """
        super().__init__()
        self.signals_ = LoadImageSignals()
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

        try:
            self.signals_.finished_.emit(image_data)
        except RuntimeError:
            ...


class ImgInfoSignals(QObject):
    finished_ = pyqtSignal(dict)
    delayed_info = pyqtSignal(str)


class SingleImgInfo(URunnable):
    max_row = 50

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals_ = ImgInfoSignals()

    def task(self):
        mail_folder_path = MainFolder.current.availability()
        try:
            name = os.path.basename(self.url)
            _, type_ = os.path.splitext(name)
            stats = os.stat(self.url)
            size = MainUtils.get_f_size(stats.st_size)
            mod = MainUtils.get_f_date(stats.st_mtime)
            coll = MainUtils.get_coll_name(mail_folder_path, self.url)
            thumb_path = ThumbUtils.create_thumb_path(self.url)

            res = {
                Lang.file_name: self.lined_text(name),
                Lang.type_: type_,
                Lang.file_size: size,
                Lang.place: self.lined_text(self.url),
                Lang.thumb_path: self.lined_text(thumb_path),
                Lang.changed: mod,
                Lang.collection: self.lined_text(coll),
                Lang.resol: Lang.calculating,
                }
            
            self.signals_.finished_.emit(res)

            res = self.get_img_resol(self.url)
            if res:
                self.signals_.delayed_info.emit(res)
        
        except Exception as e:
            MainUtils.print_error()
            res = {
                Lang.file_name: self.lined_text(os.path.basename(self.url)),
                Lang.place: self.lined_text(self.url),
                Lang.type_: self.lined_text(os.path.splitext(self.url)[0])
                }
            self.signals_.finished_.emit(res)

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


class MultipleImgInfo(URunnable):
    max_row = 50

    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.img_path_list = img_path_list
        self.signals_ = ImgInfoSignals()
    
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
            Lang.file_name: names,
            Lang.total: str(len(self.img_path_list)),
            Lang.file_size: self.get_total_size()
        }
        self.signals_.finished_.emit(res)

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


class RemoveFilesSignals(QObject):
    finished_ = pyqtSignal()
    progress_text = pyqtSignal(str)
    reload_gui = pyqtSignal()


class RemoveFilesTask(URunnable):
    def __init__(self, img_path_list: list[str]):
        """
        Удаляет изображения.
        Удаляет миниатюры из hashdir, удаляет записи об изображениях из бд.   
        Запуск: UThreadPool.start   
        Сигналы: finished_(), progress_text(str), reload_gui()
        """
        super().__init__()
        self.signals_ = RemoveFilesSignals()
        self.img_path_list = img_path_list

    def task(self):
        try:
            if len(self.img_path_list) > 0:
                text = f"{Lang.removing_images} ({len(self.img_path_list)})"
                self.signals_.progress_text.emit(text)
            self.remove_files()
            self.remove_thumbs()
        except Exception as e:
            MainUtils.print_error()
        try:
            self.signals_.progress_text.emit("")
            self.signals_.reload_gui.emit()
            self.signals_.finished_.emit()
        except RuntimeError as e:
            MainUtils.print_error()

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
                MainUtils.print_error()
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

        main_folder = MainFolder.current
        
        # new_items пустой так как мы только удаляем thumbs из hashdir
        file_updater = HashdirUpdater(rel_thumb_path_list, [], main_folder, self.task_state)
        del_items, new_items = file_updater.run()
        
        # new_items пустой так как мы только удаляем thumbs из бд
        conn = Dbase.engine.connect()
        db_updater = DbUpdater(del_items, [], main_folder)
        db_updater.run()
        conn.close()


class UploadFilesSignals(QObject):
    finished_ = pyqtSignal()
    progress_text = pyqtSignal(str)
    reload_gui = pyqtSignal()


class UploadFilesTask(URunnable):
    def __init__(self, img_path_list: list, main_folder: MainFolder):
        """ 
        Запуск: UThreadPool.start   
        Сигналы: finished_(), progress_text(str), reload_gui()

        Подготавливает списки `del_items` и `new_items` для `FileUpdater` и `DbUpdater`.    
        Добавляет записи в базу данных и миниатюры в hashdir.   
        Механизм реализует корректное обновление записей в базе данных и миниатюр в `hashdir`   
        в случае, если файл был заменён на новый с тем же именем. Пример:

        - В папке уже есть файл `1.jpg`
        - Пользователь копирует новый `1.jpg` в ту же папку через `CopyFilesTask`
        - Старый `1.jpg` автоматически заменяется
        - Однако в базе данных и `hashdir` остаются данные о старом файле
        - Поэтому:
        - старая запись из БД удаляется
        - старая миниатюра удаляется из `hashdir`
        - создаются новые запись и миниатюра для нового файла

        Это необходимо, чтобы избежать конфликтов и дубликатов,     
        так как новый файл с тем же именем является другим объектом     
        (другой хеш, размер и т.п.).
        """
        super().__init__()
        self.img_path_list = img_path_list
        self.main_folder = main_folder
        self.signals_ = UploadFilesSignals()

    def task(self):
        """
        ДОБАВЛЯЕТ В БД В ТЕКУЩУЮ MAINFOLDER
        """
        img_with_stats_list = []
        rel_thumb_path_list = []
        for img_path in self.img_path_list:
            try:
                stat = os.stat(img_path)
            except Exception as e:
                MainUtils.print_error()
                continue
            size, birth, mod = stat.st_size, stat.st_birthtime, stat.st_mtime
            data = (img_path, size, birth, mod)
            img_with_stats_list.append(data)

            thumb_path = ThumbUtils.create_thumb_path(img_path)
            rel_thumb_path = ThumbUtils.get_rel_thumb_path(thumb_path)
            rel_thumb_path_list.append(rel_thumb_path)

        if rel_thumb_path_list:
            text = f"{Lang.updating_data} {Lang.izobrazhenii.lower()}: {len(rel_thumb_path_list)} "
            self.signals_.progress_text.emit(text)

        args = (rel_thumb_path_list, img_with_stats_list, self.main_folder, self.task_state)
        file_updater = HashdirUpdater(*args)
        rel_thumb_path_list, new_items = file_updater.run()

        db_updater = DbUpdater(rel_thumb_path_list, new_items, self.main_folder)
        db_updater.run()

        try:
            self.signals_.progress_text.emit("")
            self.signals_.reload_gui.emit()
            self.signals_.finished_.emit()
        except RuntimeError as e:
            MainUtils.print_error()
    

class MoveFilesTask(QObject):
    set_progress_text = pyqtSignal(str)
    reload_gui = pyqtSignal()

    def __init__(self, dest: str, img_path_list: list):
        """
        Важно: это QObject, не URunnable. Объединяет несколько URunnable-задач.

        Старт: вызов run()  
        Сигналы: 
        - set_progress_text(str)
        - reload_gui()

        Действия:
        - Копирует файлы в новую директорию
        - Удаляет исходные файлы
        - Обновляет hashdir и базу данных
        """
        super().__init__()
        self.dest = dest
        self.img_path_list = img_path_list

    def run(self):
        self.start_copy_task()

    def start_copy_task(self):
        """
        Копирует файлы в заданную директорию.
        """
        copy_task = CopyFilesTask(self.dest, self.img_path_list)
        cmd = lambda new_img_path_list: self.start_remove_task(self.img_path_list, new_img_path_list)
        copy_task.signals_.finished_.connect(cmd)
        UThreadPool.start(copy_task)

    def start_remove_task(self, img_path_list: list, new_img_path_list: list):
        """
        Удаляет исходные файлы (перемещение из исходной директории).
        """
        remove_task = RemoveFilesTask(img_path_list)
        cmd = lambda: self.start_upload_task(new_img_path_list)
        remove_task.signals_.finished_.connect(cmd)
        remove_task.signals_.progress_text.connect(lambda text: self.set_progress_text.emit(text))
        UThreadPool.start(remove_task)

    def start_upload_task(self, new_img_path_list: list):
        """
        Загружает в hadhdir миниатюры и делает записи в базу данных.
        """
        upload_task = UploadFilesTask(new_img_path_list)
        upload_task.signals_.progress_text.connect(lambda text: self.set_progress_text.emit(text))
        upload_task.signals_.reload_gui.connect(lambda: self.reload_gui.emit())
        UThreadPool.start(upload_task)


class LoadDbImagesItem:
    __slots__ = ["qimage", "rel_img_path", "coll_name", "fav", "f_mod"]
    def __init__(self, qimage: QImage, rel_img_path: str, coll: str, fav: int, f_mod: str):
        self.qimage = qimage
        self.rel_img_path = rel_img_path
        self.coll_name = coll
        self.fav = fav
        self.f_mod = f_mod


class LoadDbImagesSignals(QObject):
    finished_ = pyqtSignal(dict)


class LoadDbImagesTask(URunnable):
    def __init__(self):
        super().__init__()
        self.signals_ = LoadDbImagesSignals()
        self.conn = Dbase.engine.connect()

    def task(self):
        stmt = self.get_stmt()
        res: list[tuple] = self.conn.execute(stmt).fetchall()

        self.conn.close()
        self.create_dict(res)

    def create_dict(self, res: list[tuple]) -> dict[str, list[LoadDbImagesItem]] | dict:
        thumbs_dict = defaultdict(list[LoadDbImagesItem])

        if len(Dynamic.types) == 1:
            exts_ = Dynamic.types[0]
        else:
            exts_ = Static.ext_all

        if not res:
            self.signals_.finished_.emit(thumbs_dict)
            return

        for rel_img_path, rel_thumb_path, mod, coll, fav in res:
            rel_img_path: str
            if not rel_img_path.endswith(exts_):
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
                f_mod = f"{Lang.months[str(f_mod.month)]} {f_mod.year}"
            item = LoadDbImagesItem(qimage, rel_img_path, coll, fav, f_mod)
            if Dynamic.curr_coll_name == Static.NAME_RECENTS:
                thumbs_dict[0].append(item)
            else:
                thumbs_dict[f_mod].append(item)
        try:
            self.signals_.finished_.emit(thumbs_dict)
        except RuntimeError:
            ...

    def get_stmt(self) -> sqlalchemy.Select:
        stmt = sqlalchemy.select(
            THUMBS.c.short_src, # rel img path
            THUMBS.c.short_hash, # rel thumb path
            THUMBS.c.mod,
            THUMBS.c.coll,
            THUMBS.c.fav
            )
        
        stmt = stmt.limit(Static.GRID_LIMIT).offset(Dynamic.grid_buff_size)
        stmt = stmt.where(THUMBS.c.brand == MainFolder.current.name)

        if Dynamic.curr_coll_name == Static.NAME_RECENTS:
            stmt = stmt.order_by(-THUMBS.c.id)
        else:
            stmt = stmt.order_by(-THUMBS.c.mod)

        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt = stmt.where(THUMBS.c.short_src.ilike(f"%{text}%"))
            return stmt

        if Dynamic.curr_coll_name == Static.NAME_FAVS:
            stmt = stmt.where(THUMBS.c.fav == 1)

        elif Dynamic.curr_coll_name not in (Static.NAME_ALL_COLLS, Static.NAME_RECENTS):
            stmt = stmt.where(THUMBS.c.coll == Dynamic.curr_coll_name)

        if any((Dynamic.date_start, Dynamic.date_end)):
            start, end = self.combine_dates(Dynamic.date_start, Dynamic.date_end)
            stmt = stmt.where(THUMBS.c.mod > start)
            stmt = stmt.where(THUMBS.c.mod < end)

        all_values = {i.value for i in UserFilter.list_} | {SystemFilter.value}

        if len(all_values) == 1:
            return stmt
    
        include_conditions = [
            self.get_include_condition(i.dir_name)
            for i in UserFilter.list_
            if i.value
        ]

        exclude_conditions = [
            self.get_exclude_condition(i.dir_name)
            for i in UserFilter.list_
        ]

        if include_conditions and SystemFilter.value:
            stmt = stmt.where(sqlalchemy.or_(
                sqlalchemy.or_(*include_conditions),
                sqlalchemy.and_(*exclude_conditions)
            ))

        elif include_conditions:
            stmt = stmt.where(sqlalchemy.or_(*include_conditions))

        elif SystemFilter.value:
            stmt = stmt.where(sqlalchemy.and_(*exclude_conditions))

        return stmt

    def get_exclude_condition(self, dir_name: str):
        """
        Формирует условие для исключения всех путей, содержащих любую из папок фильтров.
        """
        return THUMBS.c.short_src.not_ilike(f"%/{dir_name}/%")

    def get_include_condition(self, dir_name: str):
        """
        Формирует условие для включения путей, содержащих указанную папку.
        """
        return THUMBS.c.short_src.ilike(f"%/{dir_name}/%")


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
