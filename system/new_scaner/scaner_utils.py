import gc
import os
import shutil

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


class DirsLoader(QObject):
    progress_text = pyqtSignal(str)

    def __init__(self, mf: Mf, task_state: TaskState):
        super().__init__()
        self.mf = mf
        self.mf_path = mf.curr_path
        self.task_state = task_state
        if mf.curr_path:
            self.true_name = os.path.basename(mf.curr_path)
        else:
            self.true_name = os.path.basename(mf.paths[0])
        self.alias = mf.alias

    def finder_dirs(self) -> list[tuple]:
        """
        Возвращает:
        - [(rel_dir_path, mod_time), ...]
        """
        dirs = []
        stack = [self.mf_path]
        
        self.progress_text.emit(
            f"{self.true_name} ({self.alias}): {Lng.search_in[cfg.lng].lower()}"
        )

        def iter_dir(entry: os.DirEntry):
            if entry.is_dir() and entry.name not in self.mf.stop_list:
                stack.append(entry.path)
                rel_path = Utils.get_rel_img_path(self.mf_path, entry.path)
                stats = entry.stat()
                mod = int(stats.st_mtime)
                dirs.append((rel_path, mod))

        while stack:
            current = stack.pop()
            with os.scandir(current) as it:
                for entry in it:
                    if not self.task_state.should_run():
                        break
                    try:
                        iter_dir(entry)
                    except Exception as e:
                        print("new scaner utils, dirs loader, finder dirs error", e)
                        self.task_state.set_should_run(False)

        try:
            stats = os.stat(self.mf_path)
            data = (os.sep, int(stats.st_mtime))
            dirs.append(data)
        except Exception as e:
            print("new scaner dirs loader finder dirs error add root dir", e)
        return dirs

    def db_dirs(self) -> list[tuple]:
        """
        Возвращает:
        - [(rel_dir_path, mod_time), ...]
        """
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod).where(
            DIRS.c.brand == self.mf.alias
        )
        res = [(short_src, mod) for short_src, mod in conn.execute(q)]
        conn.close()
        return res


class DirsCompator:
    @classmethod
    def get_dirs_to_remove(cls, finder_dirs: list, db_dirs: list) -> list :
        """
        Параметры:
        - finder_dirs: [(rel_dir_path, mod_time), ...]
        - db_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает директории Finder, которые были удалены:
        - [(rel_dir_path, mod_time), ...]
        """
        finder_paths = [rel_path for rel_path, _ in finder_dirs]
        return [
            (rel_dir_path, int(mod))
            for rel_dir_path, mod in db_dirs
            if rel_dir_path not in finder_paths
        ]

    @classmethod
    def get_dirs_to_scan(cls, finder_dirs: list, db_dirs: list) -> list:
        """
        Параметры:
        - finder_dirs: [(rel_dir_path, mod_time), ...]
        - db_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает директории Finder, которые необходимо просканировать
        - [(rel_dir_path, mod_time), ...]
        """
        return [
            (rel_dir_path, int(mod))
            for (rel_dir_path, mod) in finder_dirs
            if (rel_dir_path, mod) not in db_dirs
        ]


class DirsUpdater:
    def __init__(self, mf: Mf, dirs_to_scan: list[str]):
        """
        - dirs_to_scan: [(rel_dir_path, mod_time), ...]
        """
        super().__init__()
        self.mf = mf
        self.dirs_to_scan = dirs_to_scan
        self.conn = Dbase.engine.connect()
        
    def run(self):
        self.update_dirs()
        self.conn.close()

    def update_dirs(self):
        # удалить старые записи
        short_paths = [short_src for short_src, _ in self.dirs_to_scan]
        if short_paths:
            del_stmt = sqlalchemy.delete(DIRS).where(
                DIRS.c.short_src.in_(short_paths),
                DIRS.c.brand == self.mf.alias
            )
            self.conn.execute(del_stmt)

        # вставить новые записи батчем
        values_list = [
            {
                ClmNames.short_src: short_src,
                ClmNames.mod: mod,
                ClmNames.brand: self.mf.alias
            }
            for short_src, mod in self.dirs_to_scan
        ]
        if values_list:
            self.conn.execute(sqlalchemy.insert(DIRS), values_list)

        self.conn.commit()


class ImgLoader(QObject):
    progress_text = pyqtSignal(str)

    def __init__(self, dirs_to_scan: list[str, int], mf: Mf, task_state: TaskState):
        """
        dirs_to_scan: [(rel dir path, int modified time), ...]
        """
        super().__init__()
        self.dirs_to_scan = dirs_to_scan
        self.mf = mf
        self.mf_path = mf.curr_path
        self.task_state = task_state
        if mf.curr_path:
            self.true_name = os.path.basename(mf.curr_path)
        else:
            self.true_name = os.path.basename(mf.paths[0])
        self.alias = mf.alias

    def finder_images(self) -> list[tuple]:
        """
        Параметры:
        - new_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает изображения в указанных директориях:
        - [(abs_path, size, birth_time, mod_time), ...]    
        """

        self.progress_text.emit(
            f"{self.true_name} ({self.alias}): {Lng.search[cfg.lng].lower()}"
        )
        finder_images = []

        def process_entry(entry: os.DirEntry):
            abs_path = entry.path
            stats = entry.stat()
            size = int(stats.st_size)
            birth = int(stats.st_birthtime)
            mod = int(stats.st_mtime)
            finder_images.append((abs_path, size, birth, mod))

        for rel_dir_path, mod in self.dirs_to_scan:
            abs_dir_path = Utils.get_abs_img_path(self.mf_path, rel_dir_path)
            for entry in os.scandir(abs_dir_path):
                if not self.task_state.should_run():
                    return []
                if entry.path.endswith(ImgUtils.ext_all):
                    try:
                        process_entry(entry)
                    except Exception as e:
                        print("new scaner utils, img loader, finder images, error", e)
                        self.task_state.set_should_run(False)
                        break

        # print(self.mf.name, len(finder_images))
        return finder_images

    def db_images(self) -> list[tuple]:
        """
        Параметры:
        - new_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает изображения в указанных директориях:
        - {rel_thumb_path: (abs_path, size, birth, mod), ...}  
        """
        conn = Dbase.engine.connect()
        db_images: dict = {}
        for rel_dir_path, mod in self.dirs_to_scan:
            q = sqlalchemy.select(
                THUMBS.c.short_hash, # rel thumb path
                THUMBS.c.short_src,
                THUMBS.c.size,
                THUMBS.c.birth,
                THUMBS.c.mod
                )
            q = q.where(THUMBS.c.brand == self.mf.alias)
            if rel_dir_path == "/":
                q = q.where(THUMBS.c.short_src.ilike("/%"))
                q = q.where(THUMBS.c.short_src.not_ilike(f"/%/%"))
            else:
                q = q.where(THUMBS.c.short_src.ilike(f"{rel_dir_path}/%"))
                q = q.where(THUMBS.c.short_src.not_ilike(f"{rel_dir_path}/%/%"))
            for rel_thumb_path, rel_path, size, birth, mod in conn.execute(q):
                abs_path = Utils.get_abs_img_path(self.mf_path, rel_path)
                db_images[rel_thumb_path] = (abs_path, size, birth, mod)
        conn.close()
        return db_images


class _ImgCompator:
    def __init__(self, finder_images: dict, db_images: dict):
        """
        Сравнивает данные об изображениях FinderImages и DbImages.  
        Запуск: run()

        Принимает:      
        finder_images: [(abs_path, size, birth_time, mod_time), ...]    
        db_images:  {rel thumb path: (abs img path, size, birth time, mod time), ...}

        Возвращает:
        del_items: [rel thumb path, ...]    
        new_items: [(abs path, size, birth, mod), ...]
        """
        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def run(self):
        finder_set = set(self.finder_images)
        db_values = set(self.db_images.values())
        del_items = [k for k, v in self.db_images.items() if v not in finder_set]
        ins_items = list(finder_set - db_values)
        return del_items, ins_items


class _ImgHashdirUpdater(QObject):
    progress_text = pyqtSignal(str)
    def __init__(self, del_items: list, new_items: list, task_state: TaskState, mf: Mf):
        """
        Удаляет thumbs из hashdir, добавляет thumbs в hashdir.  
        Запуск: run()   
        Сигналы: progress_text(str)
        
        Принимает:  
        del_items: [rel_thumb_path, ...]    
        new_items: [(path, size, birth, mod), ...]  


        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(path, size, birth, mod), ...]  
        """
        super().__init__()
        self.del_items = del_items
        self.new_items = new_items
        self.task_state = task_state
        self.mf = mf
        self.total = len(new_items) + len(del_items)
        if mf.curr_path:
            self.true_name = os.path.basename(mf.curr_path)
        else:
            self.true_name = os.path.basename(mf.paths[0])
        self.alias = mf.alias

    def run(self) -> tuple[list, list]:
        """
        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(path, size, birth, mod), ...]  
        """
        if not self.task_state.should_run():
            return ([], [])
        del_items = self.run_del_items()
        new_items = self.run_new_items()
        return del_items, new_items

    def run_del_items(self):
        new_del_items = []
        for rel_thumb_path in self.del_items:
            if not self.task_state.should_run():
                break
            thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
            if os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                    folder = os.path.dirname(thumb_path)
                    if not os.listdir(folder):
                        os.rmdir(folder)
                    new_del_items.append(rel_thumb_path)
                    self.total -= 1
                    self.send_text()
                except Exception as e:
                    print("new scaner utils, hashdir updater, remove img error", e)
                    continue
        return new_del_items
    
    def send_text(self):
        self.progress_text.emit(
            f"{self.true_name} ({self.alias}): {Lng.updating[cfg.lng].lower()} ({self.total})"
            )

    def create_thumb(self, path: str) -> ndarray | None:
        img = ImgUtils.read_img(path)
        thumb = Utils.fit_to_thumb(img, Static.max_img_size)
        del img
        gc.collect()
        if isinstance(thumb, ndarray):
            return thumb
        else:
            return None

    def run_new_items(self):
        new_new_items = []
        for path, size, birth, mod in self.new_items:
            if not self.task_state.should_run():
                break
            try:
                thumb = self.create_thumb(path)
                thumb_path = Utils.create_abs_thumb_path(path)
                Utils.write_thumb(thumb_path, thumb)
                new_new_items.append((path, size, birth, mod))
                self.total -= 1
                self.send_text()
            except Exception as e:
                print("new scaner utils, hashdir updater, create new img error", e)
                continue
        return new_new_items


class _ImgDbUpdater:
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
            Utils.get_rel_img_path(self.mf.curr_path, path)
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
            abs_hash = Utils.create_abs_thumb_path(path)
            short_hash = Utils.get_rel_thumb_path(abs_hash)
            short_src = Utils.get_rel_img_path(self.mf.curr_path, path)
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
    
    def run(self):
        img_loader = ImgLoader(self.dirs_to_scan, self.mf, self.task_state)
        img_loader.progress_text.connect(self.progress_text.emit)
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
                    os.remove(Utils.get_abs_thumb_path(short_hash))
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
