import gc
import os
import shutil
from multiprocessing import Queue
from time import sleep

import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Static, cfg
from system.database import DIRS, THUMBS, ClmNames, Dbase
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import ImgUtils
from system.tasks import TaskState
from system.utils import Utils

from .items import ScanerItem


class DirItem:
    def __init__(self, rel_path: str, mod: int):
        self.rel_path = rel_path
        self.mod = mod


class DirsManager:

    @staticmethod
    def get_finder_dirs(scaner_item: ScanerItem, q: Queue):
        """
        Возвращает список DirItem
        - которые есть в директории (Mf.curr_path)
        - которых нет в стоп листе Mf.stop_list
        """
        # отправляем текст в гуи что идет поиск в папке
        # gui_text: Имя папки (псевдоним папки): поиск в папке
        scaner_item.gui_text = f"{scaner_item.mf_real_name} ({scaner_item.mf_alias}): {Lng.search_in[cfg.lng].lower()}"
        q.put(scaner_item)
        dirs: list[DirItem] = []
        stack = [scaner_item.mf.curr_path]
        while stack:
            current = stack.pop()
            for entry in os.scandir(current):
                try:
                    stmt = entry.is_dir() and entry.name not in scaner_item.mf.stop_list
                except Exception as e:
                    print("new scaner utils, dirs loader, finder dirs error", e)
                    scaner_item.stop_task = True
                    break
                if stmt:
                    stack.append(entry.path)
                    rel_path = Utils.get_rel_path(scaner_item.mf.curr_path, entry.path)
                    stats = entry.stat()
                    mod = int(stats.st_mtime)
                    dir_item = DirItem(rel_path, mod)
                    dirs.append(dir_item)

        try:
            stats = os.stat(scaner_item.mf.curr_path)
            mod = int(stats.st_mtime)
            dir_item = DirItem(os.sep, mod)
        except Exception as e:
            print("new scaner dirs loader finder dirs error add root dir", e)
        return dirs

    @staticmethod
    def get_db_dirs(scaner_item: ScanerItem):
        """
        Возвращает список DirItem
        - которые есть в базе данных и соответствуют псевдониму Mf
        """
        conn = scaner_item.engine.connect()
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod).where(
            DIRS.c.brand == scaner_item.mf_alias
        )
        res = [DirItem(rel_path, mod) for rel_path, mod in conn.execute(q)]
        conn.close()
        return res


class DirsCompator:

    @staticmethod
    def get_dirs_to_remove(finder_dirs: list[DirItem], db_dirs: list[DirItem]):
        """
        Параметры:
        - finder_dirs список DirItem
        - db_dirs список DirItem

        Возвращает список DirItem
        - которых больше нет в Finder, но есть в базе данных
        - которые нужно удалить из базы данных
        """
        rel_paths = [dir_item.rel_path for dir_item in finder_dirs]
        return [
            dir_item
            for dir_item in db_dirs
            if dir_item.rel_path not in rel_paths
        ]

    @staticmethod
    def get_dirs_to_scan(finder_dirs: list[DirItem], db_dirs: list[DirItem]):
        """
        Параметры:
        - finder_dirs список DirItem
        - db_dirs список DirItem

        Возвращает список DirItem
        - которые есть в Finder, но нет в базе данных
        - которые нужно добавить в базу данных
        """
        rel_paths = [
            (dir_item.rel_path, dir_item.mod)
            for dir_item in db_dirs
        ]
        return [
            dir_item
            for dir_item in finder_dirs
            if (dir_item.rel_path, dir_item.mod) not in rel_paths
        ]


class DirsUpdater:

    @staticmethod
    def start(scaner_item: ScanerItem, dir_list: list[DirItem]):
        """
        Параметры:
        - dir_list список DirItem

        Запускается только после работы с изображениями:
        - добавление и удаление изображений из базы данных THUMBS
        - добавление и удаление изображений из "hashdir"

        Что делает:
        - удаляет записи из DIRS, которые соответствуют Mf.alias
        - добавляет записи в DIRS, которые соответствуют Mf.alias
        - по сути это замена sqlalchemy.update
        """
        # удалить старые записи
        if not dir_list:
            return
        conn = scaner_item.engine.connect()
        rel_paths = [dir_item.rel_path for dir_item in dir_list]
        del_stmt = sqlalchemy.delete(DIRS).where(
            DIRS.c.short_src.in_(rel_paths),
            DIRS.c.brand == scaner_item.mf_alias
        )
        conn.execute(del_stmt)

        # вставить новые записи батчем
        values_list = [
            {
                ClmNames.short_src: dir_item.rel_path,
                ClmNames.mod: dir_item.mod,
                ClmNames.brand: scaner_item.mf_alias
            }
            for dir_item in dir_list
        ]
        if values_list:
            conn.execute(sqlalchemy.insert(DIRS), values_list)
        conn.commit()
        conn.close()


class ImgLoader:

    @staticmethod
    def get_finder_images(scaner_item: ScanerItem, q: Queue, dirs_to_scan: list):
        """
        Параметры:
        - dirs_to_scan: [(rel_dir_path, mod_time), ...]

        Получает и возвращает список изображений из указанных директорий:
        - [(abs_path, size, birth_time, mod_time), ...]    
        """
        # передает в гуи текст
        # имя папки (псевдоним): поиск
        text = f"{scaner_item.mf_real_name} ({scaner_item.mf_alias}): {Lng.search[cfg.lng].lower()}"
        scaner_item.gui_text = text
        q.put(scaner_item)
        finder_images = []
        for rel_dir_path, _ in dirs_to_scan:
            abs_dir_path = Utils.get_abs_path(scaner_item.mf.curr_path, rel_dir_path)
            for entry in os.scandir(abs_dir_path):
                # если где то ранее был включен флаг то возвращаем пустой список
                if scaner_item.stop_task:
                    return []
                if entry.path.endswith(ImgUtils.ext_all):
                    # если нет доступа к изображению, то продолжить
                    try:
                        stat = entry.stat()
                    except Exception as e:
                        print("new scaner utils, img loader, finder images, error", e)
                        continue
                    size = int(stat.st_size)
                    birth = int(stat.st_birthtime)
                    mod = int(stat.st_mtime)
                    finder_images.append((entry.path, size, birth, mod))
        return finder_images

    @staticmethod
    def get_db_images(scaner_item: ScanerItem, dirs_to_scan: list):
        """
        Параметры:
        - dirs_to_scan: [(rel_dir_path, mod_time), ...]

        Получает и возвращает информацию об изображениях в базе данных из указанных директорий:
        - {rel_thumb_path: (abs_path, size, birth, mod), ...}  
        """
        conn = scaner_item.engine.connect()
        db_images: dict = {}
        for rel_dir_path, mod in dirs_to_scan:
            q = sqlalchemy.select(
                THUMBS.c.short_hash, # rel thumb path
                THUMBS.c.short_src,
                THUMBS.c.size,
                THUMBS.c.birth,
                THUMBS.c.mod
                )
            q = q.where(THUMBS.c.brand == scaner_item.mf_alias)
            if rel_dir_path == "/":
                q = q.where(THUMBS.c.short_src.ilike("/%"))
                q = q.where(THUMBS.c.short_src.not_ilike(f"/%/%"))
            else:
                q = q.where(THUMBS.c.short_src.ilike(f"{rel_dir_path}/%"))
                q = q.where(THUMBS.c.short_src.not_ilike(f"{rel_dir_path}/%/%"))
            for rel_thumb_path, rel_path, size, birth, mod in conn.execute(q):
                abs_path = Utils.get_abs_path(scaner_item.mf.curr_path, rel_path)
                db_images[rel_thumb_path] = (abs_path, size, birth, mod)
        conn.close()
        return db_images


class _ImgCompator:

    @staticmethod
    def start(finder_images: list, db_images: dict):
        """
        Сравнивает данные об изображениях из Finder и базы данных.  
        Получить данные об изображениях необходимо из ImgLoader.    
        Параметры:      
        - finder_images: [(abs_path, size, birth_time, mod_time), ...]    
        - db_images: {rel thumb path: (abs img path, size, birth time, mod time), ...}

        Возвращает:
        - изображения, которых больше нет в Finder но есть в базе данных [rel thumb path, ...]
        - изображения, которых нет в базе данных, но есть в Finder [(abs path, size, birth, mod), ...]
        """
        finder_set = set(finder_images)
        db_values = set(db_images.values())
        del_images = [k for k, v in db_images.items() if v not in finder_set]
        new_images = list(finder_set - db_values)
        return del_images, new_images


class HashdirUpdater(QObject):
 
    @staticmethod
    def start(scaner_item: ScanerItem, q: Queue, del_images: list, new_images: list):
        """
        - Удаляет из "hashdir" изображения, которых больше нет в Finder.
        - Добавляет изображения, которые есть в Finder, в "hashdir".
        - Возвращает список успешно удаленных и список успешно добавленных изображений.
        - Далее необходимо обновить информацию в базе данных на основе полученных списков.

        Получить данные del_images и new_images необходимо из ImgCompator.  
        Параметры:  
        - del_images [rel thumb path, ...]
        - new_images [(abs path, size, birth, mod), ...]

        Возвращает:     
        - успешно удаленные из "hashdir" [rel_thumb_path, ...]    
        - успешно добавленные в "hashdir" [(abs path, size, birth, mod), ...]
        """
        if scaner_item.stop_task:
            return ([], [])
        scaner_item.total_count = len(del_images) + len(new_images)
        new_del_images = HashdirUpdater.run_del_images(scaner_item, q, del_images)
        new_items = HashdirUpdater.run_new_images(scaner_item, q, new_images)
        return del_images, new_items

    @staticmethod
    def run_del_images(scaner_item: ScanerItem, q: Queue, del_images: list):
        """
        Пытается удалить изображения из "hashdir" и пустые папки.   
        Возвращает список успешно удаленных изображений.
        """
        new_del_images = []
        for rel_thumb_path in del_images:
            if scaner_item.stop_task:
                return new_del_images
            thumb_path = Utils.get_abs_hash(rel_thumb_path)
            if os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                    folder = os.path.dirname(thumb_path)
                    if not os.listdir(folder):
                        shutil.rmtree(folder)
                except Exception as e:
                    print("new scaner utils, hashdir updater, remove img error", e)
                    continue
                new_del_images.append(rel_thumb_path)
                scaner_item.total_count -= 1
                HashdirUpdater.send_text(scaner_item, q)
        return new_del_images

    @staticmethod
    def run_new_images(scaner_item: ScanerItem, q: Queue, new_images: list):
        """
        Пытается создать изображения в "hashdir".     
        Возвращает список успешно созданных изображений.
        """
        new_new_images = []
        for path, size, birth, mod in new_images:
            if scaner_item.stop_task:
                return new_new_images
            img = ImgUtils.read_img(path)
            img = Utils.fit_to_thumb(img, Static.max_img_size)
            if img is not None:
                try:
                    thumb_path = Utils.create_abs_hash(path)
                    Utils.write_thumb(thumb_path, img)
                    new_new_images.append((path, size, birth, mod))
                    scaner_item.total_count -= 1
                    HashdirUpdater.send_text(scaner_item, q)
                except Exception as e:
                    print("new scaner utils, hashdir updater, create new img error", e)
                    continue
        return new_new_images

    @staticmethod
    def send_text(scaner_item: ScanerItem, q: Queue):
        """
        Посылает текст в гуи.   
        Имя папки (псевдоним): обновление (оставшееся число)
        """
        text = f"{scaner_item.mf_real_name} ({scaner_item.mf_alias}): {Lng.updating[cfg.lng].lower()} ({scaner_item.total_count})"
        scaner_item.gui_text = text
        q.put(scaner_item)

    @staticmethod
    def create_thumb(path: str) -> ndarray | None:
        img = ImgUtils.read_img(path)
        img = Utils.fit_to_thumb(img, Static.max_img_size)


class DbUpdater:
    def __init__(self, del_images: list, new_images: list, mf: Mf):
        """
        Удаляет записи thumbs из бд, добавляет записи thumbs в бд.  
        Запуск: run()  

        Принимает:  
        - del_items: [rel_thumb_path, ...]       
        - new_items: [(path, size, birth, mod), ...]          
        """
        super().__init__()
        self.mf = mf
        self.del_images = del_images
        self.new_images = new_images
        self.conn = Dbase.engine.connect()

    def run(self):
        self.run_del_items()
        self.del_dublicates()
        self.run_new_items()

    def run_del_items(self):
        if self.del_images:
            q = sqlalchemy.delete(THUMBS).where(
                THUMBS.c.short_hash.in_(self.del_images),
                THUMBS.c.brand == self.mf.alias
            )
            self.conn.execute(q)
            self.conn.commit()

    def del_dublicates(self):
        short_paths = [
            Utils.get_rel_path(self.mf.curr_path, path)
            for path, size, birth, mod in self.new_images
        ]
        q = sqlalchemy.delete(THUMBS).where(
            THUMBS.c.short_src.in_(short_paths),
            THUMBS.c.brand == self.mf.alias
        )
        self.conn.execute(q)
        self.conn.commit()

    def run_new_items(self):
        values_list = []
        for path, size, birth, mod in self.new_images:
            abs_hash = Utils.create_abs_hash(path)
            short_hash = Utils.get_rel_hash(abs_hash)
            short_src = Utils.get_rel_path(self.mf.curr_path, path)
            values_list.append({
                ClmNames.short_src: short_src,
                ClmNames.short_hash: short_hash,
                ClmNames.size: size,
                ClmNames.birth: birth,
                ClmNames.mod: mod,
                ClmNames.resol: "",
                ClmNames.coll: "",
                ClmNames.fav: 0,
                ClmNames.brand: self.mf.alias
            })
        self.conn.execute(sqlalchemy.insert(THUMBS), values_list)
        self.conn.commit()


class NewDirsHandler(QObject):
    progress_text = pyqtSignal(str)
   
    def __init__(self, dirs_to_scan: list[str], mf: Mf, task_state: TaskState):
        """
        dirs_to_scan: [(rel dir path, int modified time), ...]
        """
        super().__init__()
        self.dirs_to_scan = dirs_to_scan
        self.mf = mf
        self.task_state = task_state
    
    @staticmethod
    def start(new_dirs: list, scaner_item: ScanerItem, q: Queue):
        """
        new_dirs: [(rel dir path, int modified time), ...]
        """
        img_loader = ImgLoader(new_dirs, scaner_item)
        finder_images = img_loader.finder_images()
        db_images = img_loader.db_images()
        if not self.task_state.should_run():
            print(self.mf.alias, "new scaner utils, ScanDirs, img_loader, сканирование прервано task state")
            return

        # сравниваем Finder и БД изображения
        img_compator = _ImgCompator(finder_images, db_images)
        del_images, new_images = img_compator.run()
        
        # создаем / обновляем изображения в hashdir
        hashdir_updater = _ImgHashdirUpdater(del_images, new_images, self.task_state, self.mf)
        hashdir_updater.progress_text.connect(self.progress_text.emit)
        del_images, new_images = hashdir_updater.run()

        if not self.task_state.should_run():
            print(self.mf.alias, "new scaner utils, ScanDirs, db updater, сканирование прервано task state")
            return

        # обновляем БД
        db_updater = _ImgDbUpdater(del_images, new_images, self.mf)
        db_updater.run()

        dirs_updater = DirsUpdater(self.mf, self.dirs_to_scan)
        dirs_updater.run()

        self.progress_text.emit("")

        return (del_images, new_images)
    

class RemovedDirsHandler(QObject):
    def __init__(self, dirs_to_del: list, mf: Mf):
        """
        dirs_to_del: [(rel dir path, int modified time), ...]
        """
        super().__init__()
        self.dirs_to_del = dirs_to_del
        self.mf = mf
        self.conn = Dbase.engine.connect()

    def run(self):
        try:
            self._process_dirs()
        except Exception as e:
            print("DelDirsHandler, run error:", e)

    def _process_dirs(self):
        def remove_thumbs(rel_dir: str):
            stmt = (
                sqlalchemy.select(THUMBS.c.short_hash)
                .where(THUMBS.c.short_src.ilike(f"{rel_dir}/%"))
                .where(THUMBS.c.short_src.not_ilike(f"{rel_dir}/%/%"))
                .where(THUMBS.c.brand == self.mf.alias)
            )
            for short_hash in self.conn.execute(stmt).scalars():
                try:
                    os.remove(Utils.get_abs_hash(short_hash))
                except Exception as e:
                    print("DelDirsHandler, remove thumb:", e)

            del_stmt = (
                sqlalchemy.delete(THUMBS)
                .where(THUMBS.c.short_src.ilike(f"{rel_dir}/%"))
                .where(THUMBS.c.short_src.not_ilike(f"{rel_dir}/%/%"))
                .where(THUMBS.c.brand == self.mf.alias)
            )
            self.conn.execute(del_stmt)

        def remove_dir_entry(rel_dir: str):
            stmt = (
                sqlalchemy.delete(DIRS)
                .where(DIRS.c.short_src == rel_dir)
                .where(DIRS.c.brand == self.mf.alias)
            )
            self.conn.execute(stmt)

        for rel_dir, _ in self.dirs_to_del:
            remove_thumbs(rel_dir)
            remove_dir_entry(rel_dir)

        self.conn.commit()


class ScanerTask:
    """
    Что на счет проверки на таймаут сканера (если он завис)
    Если сканер завис, он перестанет посылать q.put в основной гуи
    И мы не сможем текущим методом сравнить время в ScanerItem и время в гуи
    Нужно задать время в основном гуи и обнулять его каждый раз, когда получает ScanerItem
    Но тогда нужно регулярно отправлять ScanerItem, чтобы обнулять время
    А это может не подойти, так как ScanerItem обновляет gui_text
    С другой стороны можно не париться и обновлять gui_text при каждом q.put
    Потому что мы будем делать poll_task например раз в 1-2 секунды
    """

    @staticmethod
    def start(mf_list: list[Mf], q: Queue):
        engine = Dbase.create_engine()
        # нельзя обращаться сразу к Mf так как это мультипроцесс
        for mf in mf_list:
            scaner_item = ScanerItem(mf, engine)
            if scaner_item.mf.get_available_path():
                print("scaner started", scaner_item.mf_alias)
                ScanerTask.mf_scan(scaner_item, q)
                gc.collect()
                print("scaner finished", scaner_item.mf_alias)
            else:
                # Отправляем текст в гуи что нет подключения к папке
                # Имя папки (псевдоним): нет подключения
                no_conn = Lng.no_connection[cfg.lng].lower()
                text = f"{scaner_item.mf_real_name} ({scaner_item.mf_alias}): {no_conn}"
                scaner_item.gui_text = text
                q.put(scaner_item)
                print("scaner no connection", scaner_item.mf_real_name, scaner_item.mf_alias)
                sleep(5)
            # после работы с очередной папкой отправляем айтем в гуи, чтобы перезагрузить гуи
            # флаг reload gui устанавливается на false в основном гуи после перезагрузки гуи
            if scaner_item.reload_gui:
                q.put(scaner_item)
        engine.dispose()
        # в маин гуи if not ScanerTask.is_alive(): устанавливай прогресс текст на пустышку

    @staticmethod
    def mf_scan(scaner_item: ScanerItem, q: Queue):
        try:
            ScanerTask._mf_scan(scaner_item, q)
        except Exception as e:
            print("scaner, main folder scan error", scaner_item.mf_real_name, scaner_item.mf_alias, e)

    @staticmethod
    def _mf_scan(scaner_item: ScanerItem, q: Queue):
        # собираем Finder директории и директории из БД
        finder_dirs = DirsManager.get_finder_dirs(scaner_item, q)
        db_dirs = DirsManager.get_db_dirs(scaner_item)
        if not finder_dirs or scaner_item.stop_task:
            print(scaner_item.mf_alias, "no finder dirs")
            return

        # сравниваем кортежи (директория, дата изменения)
        # new_dirs: директории, которые нужно просканировать на изображения
        # и обновить в БД данные об изображениях и о директориях
        # del_dirs: директории, которых были удалены в Finder, то 
        # есть когда была удалена папка целиком
        new_dirs = DirsCompator.get_dirs_to_scan(finder_dirs, db_dirs)
        removed_dirs = DirsCompator.get_dirs_to_remove(finder_dirs, db_dirs)
        
        # обходим новые директории, добавляем / удаляем изображения
        if new_dirs:
            scan_dirs = NewDirsHandler(new_dirs, scaner_item)
            scan_dirs.run()
        
        # удаляем удаленные Finder директории
        if removed_dirs:
            del_handler = RemovedDirsHandler(removed_dirs, mf)
            del_handler.run()