import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Queue
from time import sleep

import sqlalchemy
from typing_extensions import Literal

from cfg import Static
from system.database import Dbase, Dirs, Thumbs
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import BaseProcessWorker
from system.shared_utils import ImgUtils
from system.utils import Utils


class Tools:    
    def log(text: str):
        filepath = os.path.join(Static.APP_DATA_DIR, "log.txt")
        with open(filepath, "a") as f:
            f.write(text)


class ScanerWorker(BaseProcessWorker):
    def __init__(self, target: callable, args: tuple):
        self.process_queue = Queue()
        self.response_queue = Queue()
        super().__init__(target, (*args, self.process_queue, self.response_queue))


@dataclass(slots=True)
class DirItem:
    """
    Параметры:
    - rel_path: относительный путь к подкаталогу относительно `Mf.curr_path`.
      Пример:
        - Mf.curr_path = /User/Downloads/parent/folder
        - подкаталог = /User/Downloads/parent/folder/subfolder
        - rel_path = /subfolder
    - mod: дата модификации каталога (os.stat.st_mtime)
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


@dataclass(slots=True)
class ForcedScanerItem:
    mf: Mf
    dirs_to_scan: list[str]
    lng_index: int


@dataclass(slots=True)
class BaseScanerItem:
    mf: Mf
    engine: sqlalchemy.Engine
    process_queue: Queue
    response_queue: Queue
    lng_index: int
    total_count: int
    current_count: int
    scaner_type: Literal["forced", "base"]


class ScanerParent:
    def __init__(self, scaner_item: BaseScanerItem):
        super().__init__()
        self.scaner_item = scaner_item


class DirsChangeWatcher(ScanerParent):
    def __init__(self, scaner_item: BaseScanerItem):
        super().__init__(scaner_item)

    def is_changed(self) -> tuple[bool, list[DirItem]]:
        db_dirs: list[DirItem] = []
        mf_alias = self.scaner_item.mf.mf_alias
        base_path = self.scaner_item.mf.mf_current_path.strip(os.sep)
        q = (
            sqlalchemy.select(Dirs.rel_dir_path, Dirs.mod)
            .where(Dirs.mf_alias == mf_alias)
        )
        with self.scaner_item.engine.connect() as conn:
            for rel_path, mod in conn.execute(q):
                abs_dir_path = os.path.join(
                    os.sep,
                    base_path,
                    rel_path.strip(os.sep)
                )
                item = DirItem(
                    abs_path=abs_dir_path,
                    rel_path=rel_path,
                    mod=mod
                )
                db_dirs.append(item)
                
        is_changed_flag = False

        for item in db_dirs:
            if not os.path.exists(item.abs_path):
                is_changed_flag = True
                break
            try:
                stat = os.stat(item.abs_path)
            except Exception as e:
                print("DirsChangeWatcher error", item.abs_path, e)
                continue
            if int(stat.st_mtime) > item.mod:
                is_changed_flag = True
                break
        if not db_dirs:
            is_changed_flag = True
        return (is_changed_flag, db_dirs)

    

import os
import traceback

class ScanerParent:
    def __init__(self, scaner_item: BaseScanerItem):
        super().__init__()
        self.scaner_item = scaner_item


class DirsLoader(ScanerParent):

    def __init__(self, scaner_item: BaseScanerItem):
        super().__init__(scaner_item)

    def get_finder_dirs(self) -> list[DirItem]:
        """
        Собирает список директорий, которые:
        - есть в каталоге `Mf.curr_path`
        - не в стоп-листе `Mf.stop_list`
        """
        scaner = self.scaner_item
        
        text = (
            f"{scaner.mf.mf_alias}: "
            f"{Lng.search_in[scaner.lng_index].lower()}"
        )
        scaner.process_queue.put(text)

        dirs: list[DirItem] = []
        stack = [scaner.mf.mf_current_path]
        
        while stack:
            try:
                scandir_iterator = os.scandir(stack.pop())
            except Exception as e:
                print(traceback.format_exc())
                continue
                
            for entry in scandir_iterator:
                try:
                    is_allowed = entry.name not in scaner.mf.mf_stop_list
                    stmt = (entry.is_dir() and is_allowed)
                except Exception as e:
                    print(traceback.format_exc())
                    continue
                    
                if stmt:
                    stack.append(entry.path)
                    rel_path = Utils.remove_mf_path(
                        mf_path=scaner.mf.mf_current_path,
                        abs_path=entry.path
                    )
                    stats = entry.stat()
                    mod = int(stats.st_mtime)
                    dir_item = DirItem(entry.path, rel_path, mod)
                    dirs.append(dir_item)

        try:
            stats = os.stat(scaner.mf.mf_current_path)
            mod = int(stats.st_mtime)
            dir_item = DirItem(
                scaner.mf.mf_current_path,
                os.sep,
                mod
            )
            dirs.append(dir_item)
        except Exception as e:
            print(traceback.format_exc())
            
        return dirs


class DirsComparator(ScanerParent):
    def __init__(self, scaner_item: BaseScanerItem, finder_dirs: list[DirItem], db_dirs: list[DirItem]):
        super().__init__(scaner_item)
        self.finder_dirs = finder_dirs
        self.db_dirs = db_dirs

    def get_dirs_to_remove(self):
        """
        Собирает список `DirItem`:
        - которых больше нет в Finder, но есть в базе данных
        - которые нужно удалить из базы данных
        """
        rel_paths = [dir_item.rel_path for dir_item in self.finder_dirs]
        return [
            dir_item
            for dir_item in self.db_dirs
            if dir_item.rel_path not in rel_paths
        ]

    def get_dirs_to_scan(self):
        """
        Собирает список `DirItem`:
        - которые есть в Finder, но нет в базе данных
        - которые нужно добавить в базу данных
        """
        rel_paths = [
            (dir_item.rel_path, dir_item.mod)
            for dir_item in self.db_dirs
        ]
        return [
            dir_item
            for dir_item in self.finder_dirs
            if (dir_item.rel_path, dir_item.mod) not in rel_paths
        ]


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
        
        if not os.path.exists(scaner.mf.mf_current_path):
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
        # Передаем scaner_item в родительский класс
        super().__init__(scaner_item)
        # Сохраняем список директорий для сканирования как свойство экземпляра
        self.dirs_to_scan = dirs_to_scan

    def get_finder_images(self) -> list[ImgItem]:
        """
        Собирает список `ImgItem` из указанных директорий:
        - finder_images список ImgItem
        """
        finder_images: list[ImgItem] = []
        
        # Используем сохраненный в self список директорий
        for dir_item in self.dirs_to_scan:
            try:
                scandir_iterator = os.scandir(dir_item.abs_path)
            except Exception as e:
                print(traceback.format_exc())
                continue
                
            for entry in scandir_iterator:
                if entry.path.endswith(ImgUtils.ext_all):
                    try:
                        stat = entry.stat()
                    except Exception as e:
                        print(traceback.format_exc())
                        continue
                        
                    size = int(stat.st_size)
                    mod = int(stat.st_mtime)
                    
                    img_item = ImgItem(entry.path, size, mod)
                    finder_images.append(img_item)
                    
        return finder_images

    def get_db_images(self) -> list[ImgItem]:
        """
        Возвращает информацию об изображениях в БД из указанных директорий:
        - db_images список ImgItem
        """
        # Используем self.scaner_item напрямую
        scaner = self.scaner_item
        conn = scaner.engine.connect()
        db_images: list[ImgItem] = []
        
        # Используем сохраненный в self список директорий
        for dir_item in self.dirs_to_scan:
            stmt = (
                sqlalchemy.select(
                    Thumbs.rel_thumb_path,
                    Thumbs.rel_img_path,
                    Thumbs.size,
                    Thumbs.mod
                )
                .where(Thumbs.mf_alias == scaner.mf.mf_alias)
            )
            
            if dir_item.rel_path == os.sep:
                one_slash = "/%"
                two_slash = "/%/%"
                stmt = (
                    stmt
                    .where(Thumbs.rel_img_path.ilike(one_slash))
                    .where(Thumbs.rel_img_path.not_ilike(two_slash))
                )
            else:
                one_slash = f"{dir_item.rel_path}/%"
                two_slash = f"{dir_item.rel_path}/%/%"
                stmt = (
                    stmt
                    .where(Thumbs.rel_img_path.ilike(one_slash))
                    .where(Thumbs.rel_img_path.not_ilike(two_slash))
                )
                
            for rel_thumb_path, rel_path, size, mod in conn.execute(stmt):
                abs_img_path = Utils.add_mf_path(
                    mf_path=scaner.mf.mf_current_path,
                    rel_path=rel_path
                )
                img_item = ImgItem(
                    abs_img_path, size, mod, rel_thumb_path
                )
                db_images.append(img_item)
                
        conn.close()
        return db_images


class ImgComparator(ScanerParent):

    def __init__(self, scaner_item: BaseScanerItem, finder_images: list[ImgItem], db_images: list[ImgItem]):
        # Сохраняем списки изображений как свойства экземпляра класса
        super().__init__(scaner_item)
        self.finder_images = finder_images
        self.db_images = db_images

    def start(self):
        """
        Сравнивает данные об изображениях из Finder и базы данных.  
        Получить данные об изображениях необходимо из ImgLoader.    

        Собирает списки `ImgItem`:
        - изображения, которых больше нет в Finder но есть в БД
        - изображения, которых нет в БД, но есть в Finder
        """
        # Используем списки из свойств self
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
        # Передаем scaner_item в родительский класс
        super().__init__(scaner_item)
        # Сохраняем списки изображений как свойства экземпляра класса
        self.removed_images = removed_images
        self.new_images = new_images

    def del_thumbs(self):
        """
        Удаляет миниатюры и соответствующие записи из БД пакетами по 10.

        Перед каждым пакетом проверяет доступность источника (Mf) и
        прерывается при его недоступности.
        """
        scaner = self.scaner_item

        def _del_records(good_chunk: list[ImgItem]):
            """
            Удаляет из БД записи о миниатюрах.
            """
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
            scaner.process_queue.put(
                self.get_gui_text()
            )
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
            except Exception as e:
                print(traceback.format_exc())
                return False

        step = 10
        chunked_del_images = [
            self.removed_images[i:i+step]
            for i in range(0, len(self.removed_images), step)
        ]
        for chunk in chunked_del_images:
            if not os.path.exists(scaner.mf.mf_current_path):
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
            """
            Добавляет записи в БД об миниатюрах.
            """
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
                        mf_path=scaner.mf.mf_current_path,
                        abs_path=img_item.abs_img_path
                    )
                    abs_thumb_path = Utils.create_abs_thumb_path(
                        rel_img_path=rel_img_path,
                        mf_alias=scaner.mf.mf_alias
                    )
                    rel_thumb_path = Utils.get_rel_thumb_path(abs_thumb_path)
                    root = os.path.dirname(rel_img_path)
                    properties = (
                        rel_img_path,
                        rel_thumb_path,
                        img_item.size,
                        img_item.mod,
                        root,
                        scaner.mf.mf_alias
                    )
                    for i in properties:
                        if i is None:
                            continue
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
            scaner.process_queue.put(
                self.get_gui_text()
            )
            img = ImgUtils.read_img(img_item.abs_img_path)
            img = ImgUtils.fit_to_thumb(img, Static.THUMB_MAX_SIZE)
            rel_img_path = Utils.remove_mf_path(
                mf_path=scaner.mf.mf_current_path,
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
            if not os.path.exists(scaner.mf.mf_current_path):
                break
            good_chunk: list[ImgItem] = []
            for img_item in chunk:
                if _create_thumb(img_item):
                    good_chunk.append(img_item)
            if good_chunk:
                _upsert_records(good_chunk)
    
    def get_gui_text(self):
        # sleep(0.5)
        scaner = self.scaner_item
        return (
            f"{scaner.mf.mf_alias}: "
            f"{Lng.indexing[scaner.lng_index].lower()} "
            f"{scaner.current_count} {Lng.from_[scaner.lng_index]} {scaner.total_count}"
        )


class DirImagesUpdater(ScanerParent):   
    # Константу класса оставляем на уровне класса
    removed_images_count = 50

    def __init__(self, scaner_item: BaseScanerItem, dirs_to_scan: list[DirItem]):
        # Передаем scaner_item в родительский класс
        super().__init__(scaner_item)
        # Сохраняем список директорий для сканирования как свойство экземпляра
        self.dirs_to_scan = dirs_to_scan

    def start(self):
        """
        На основе сохраненного списка добавляются и удаляются миниатюры в "hashdir",
        а также обновляются базы данных THUMBS и DIRS.
        """
        # Используем свойства экземпляра self
        scaner = self.scaner_item
        
        img_loader = ImgLoader(scaner, self.dirs_to_scan)
        finder_images = img_loader.get_finder_images()
        db_images = img_loader.get_db_images()

        img_comparator = ImgComparator(scaner, finder_images, db_images)
        removed_images, new_images = img_comparator.start()

        # мы проверяем на удаление
        # если из каталога удаляется более Х изображений
        # это подозрительно
        # возможно пользователь указал неправильный путь к каталогу
        # из-за чего приложение пытается все удалить из старого каталога
        # чтобы добавить все из нового
        stmt = all((
            len(removed_images) > self.removed_images_count,
            scaner.scaner_type == "base",
        ))
        if stmt:
            data = (scaner.mf.mf_alias, len(removed_images))
            scaner.process_queue.put(data)
            while True:
                if not scaner.response_queue.empty():
                    can_continue = scaner.response_queue.get()
                    if can_continue:
                        break
                    else:
                        return

        # общий счет для отображения в GUI
        scaner.total_count = len(removed_images) + len(new_images)
        
        thumbs_updater = ThumbsUpdater(scaner, removed_images, new_images)
        thumbs_updater.del_thumbs()
        thumbs_updater.add_thumbs()
        
        dirs_updater = DirsDbUpdater(scaner, self.dirs_to_scan)
        dirs_updater.upsert_records()


class RemovedDirsCleaner(ScanerParent):

    def __init__(self, scaner_item: BaseScanerItem, removed_dirs: list[DirItem]):
        # Передаем scaner_item в родительский класс
        super().__init__(scaner_item)
        # Сохраняем список удаленных директорий как свойство экземпляра
        self.removed_dirs = removed_dirs

    def remove_thumbs(self):
        """
        Удаляет миниатюры из 'hashdir' и записи в базе данных Thumbs
        """
        scaner = self.scaner_item

        def _get_thumbs(conn: sqlalchemy.Connection, dir_item: DirItem):
            one_slash = f"{dir_item.rel_path}/%"
            stmt_thumbs_to_remove = (
                sqlalchemy.select(Thumbs.rel_thumb_path)
                .where(Thumbs.rel_img_path.ilike(one_slash))
                .where(Thumbs.mf_alias == scaner.mf.mf_alias)
            )
            return conn.execute(stmt_thumbs_to_remove).scalars().all()
        
        def _remove_thumb(rel_thumb_path: str):
            abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
            try:
                os.remove(abs_thumb_path)
            except Exception as e:
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
            # Используем self.removed_dirs
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
            # Используем self.removed_dirs
            for dir_item in self.removed_dirs:
                stmt = (
                    sqlalchemy.delete(Dirs.table)
                    .where(Dirs.rel_dir_path == dir_item.rel_path)
                    .where(Dirs.mf_alias == scaner.mf.mf_alias)
                )
                conn.execute(stmt)


class BaseScaner:
    @staticmethod
    def start(mf_list: list[Mf], lng_index: int, queue: Queue, response_queue: Queue):
        engine = Dbase.create_engine()
        # нельзя обращаться сразу к Mf так как это мультипроцесс
        for mf in mf_list:
            scaner_item = BaseScanerItem(
                mf=mf,
                engine=engine, 
                process_queue=queue,
                response_queue=response_queue,
                lng_index=lng_index,
                total_count=0,
                current_count=0,
                scaner_type="base"
            )
            avaiable_mf_path = scaner_item.mf.get_avaiable_mf_path()
            if avaiable_mf_path:
                scaner_item.mf.set_mf_current_path(avaiable_mf_path)
                try:
                    print("scaner started", scaner_item.mf.mf_alias)
                    BaseScaner.single_mf_scan(scaner_item)
                    print("scaner finished", scaner_item.mf.mf_alias)
                except Exception as e:
                    print(traceback.format_exc())
                    continue
            else:
                text = (
                    f"{scaner_item.mf.mf_alias}: "
                    f"{Lng.no_connection[lng_index].lower()}"
                )
                scaner_item.process_queue.put(text)
                print(text)
                sleep(3)
        engine.dispose()

    @staticmethod
    def single_mf_scan(scaner_item: BaseScanerItem):
        watcher = DirsChangeWatcher(scaner_item)
        is_changed, db_dirs = watcher.is_changed()
        if not is_changed:
            print(scaner_item.mf.mf_alias, "not changed")
            return
        dirs_loader = DirsLoader(scaner_item)
        finder_dirs = dirs_loader.get_finder_dirs()
        if not finder_dirs:
            return
        dirs_comparator = DirsComparator(scaner_item, finder_dirs, db_dirs)
        removed_dirs = dirs_comparator.get_dirs_to_remove()
        dirs_to_scan = dirs_comparator.get_dirs_to_scan()
        # это нужно, когда удалена вся папка "имя папки"
        # то есть не когда "имя папки" пуста, но существует,
        # а когда папка "имя папки" не существуетre
        if removed_dirs:
            BaseScaner.log_removed_dirs(scaner_item, finder_dirs, removed_dirs)
            if len(finder_dirs) != len(removed_dirs):
                cleaner = RemovedDirsCleaner(scaner_item, removed_dirs)
                cleaner.remove_thumbs()
                cleaner.remove_dirs()
        if dirs_to_scan:
            updater = DirImagesUpdater(scaner_item, dirs_to_scan)
            updater.start()
    
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
            f"Mf: {scaner_item.mf.mf_alias}, {scaner_item.mf.mf_current_path}",
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
    def start(item: ForcedScanerItem, queue: Queue, response_queue: Queue):
        print("single dir scaner started, mf:", item.mf.mf_alias)
        ForcedScaner.single_mf_scan(
            mf=item.mf,
            dirs_to_scan=item.dirs_to_scan,
            lng_index=item.lng_index,
            queue=queue,
            response_queue=response_queue
        )
        print("single dir scaner finished, mf:", item.mf.mf_alias)


    @staticmethod
    def single_mf_scan(mf: Mf, dirs_to_scan: list[str], lng_index: int, queue: Queue, response_queue: Queue):
        """
        Сканирует заданне директории в пределах Mf на предмет новых или
        удаленных изображений.

        Параметры:
        - mf: сканируемая директория должна принадлежать определенному Mf
        - dirs_to_scan: директории, которые нужно просканировать
        """
        engine = Dbase.create_engine()
        scaner_item = BaseScanerItem(
            mf=mf,
            engine=engine,
            process_queue=queue,
            response_queue=response_queue,
            lng_index=lng_index, 
            total_count=0,
            current_count=0,
            scaner_type="forced"
        )
        avaiable_mf_path = scaner_item.mf.get_avaiable_mf_path()
        if avaiable_mf_path:
            scaner_item.mf.set_mf_current_path(avaiable_mf_path)
            dir_items: list[DirItem] = []
            for i in dirs_to_scan:
                try:
                    mod = int(os.stat(i).st_mtime)
                except Exception as e:
                    print(traceback.format_exc())
                    continue
                item = DirItem(
                    abs_path=i,
                    rel_path=Utils.remove_mf_path(mf.mf_current_path, i),
                    mod=mod
                )
                if item not in dir_items:
                    dir_items.append(item)
            if dir_items:
                updater = DirImagesUpdater(scaner_item, dir_items)
                updater.start()