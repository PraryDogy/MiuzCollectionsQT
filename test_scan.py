import gc
import os

import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, pyqtSignal

from cfg import JsonData, Static, ThumbData
from system.database import DIRS, THUMBS, ClmNames, Dbase
from system.lang import Lang
from system.main_folder import MainFolder
from system.scaner_utils import Inspector, MainFolderRemover
from system.utils import ImgUtils, MainUtils, TaskState, ThumbUtils, URunnable


class DirsLoader:

    @classmethod
    def finder_dirs(
        cls,
        main_folder: MainFolder,
        task_state: TaskState,
        conn: sqlalchemy.Connection,
    ) -> list[tuple]:
        """
        Возвращает:
        - [(rel_dir_path, mod_time), ...]
        """
        dirs = []
        main_folder_path = main_folder.get_current_path()
        stack = [main_folder_path]


        def iter_dir(entry: os.DirEntry):
            if entry.is_dir() and entry.name not in main_folder.stop_list:
                stack.append(entry.path)
                rel_path = MainUtils.get_rel_path(main_folder_path, entry.path)
                stats = entry.stat()
                mod = int(stats.st_mtime)
                dirs.append((rel_path, mod))


        while stack:
            current = stack.pop()
            with os.scandir(current) as it:
                for entry in it:
                    if not task_state.should_run():
                        break
                    try:
                        iter_dir(entry)
                    except Exception:
                        MainUtils.print_error()
                        task_state.set_should_run(False)
        return dirs

    @classmethod
    def db_dirs(
        cls,
        main_folder: MainFolder,
        task_state: TaskState,
        conn: sqlalchemy.Connection,
    ) -> list[tuple]:
        """
        Возвращает:
        - [(rel_dir_path, mod_time), ...]
        """
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod)
        q = q.where(DIRS.c.brand == main_folder.name)
        res = conn.execute(q).fetchall()
        return [(short_src, mod) for short_src, mod in res]


class DirsCompator:
    @classmethod
    def get_rm_from_db_dirs(cls, finder_dirs: list, db_dirs: list) -> list :
        """
        Параметры:
        - finder_dirs: [(rel_dir_path, mod_time), ...]
        - db_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает те директории, которых нет в finder_dirs, но есть в db_dirs:
        - [(rel_dir_path, mod_time), ...]
        """
        return [
            (rel_dir_path, mod)
            for rel_dir_path, mod in db_dirs
            if (rel_dir_path, mod) not in finder_dirs
        ]

    @classmethod
    def get_add_to_db_dirs(cls, finder_dirs: list, db_dirs: list) -> list:
        """
        Параметры:
        - finder_dirs: [(rel_dir_path, mod_time), ...]
        - db_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает те директории, которых нет в db_dirs, но есть в finder_dirs:
        - [(rel_dir_path, mod_time), ...]
        """
        return [
            (rel_dir_path, mod)
            for (rel_dir_path, mod) in finder_dirs
            if (rel_dir_path, mod) not in db_dirs
        ]


class DirsUpdater:
    @classmethod
    def remove_db_dirs(
        cls,
        conn: sqlalchemy.Connection,
        main_folder: MainFolder,
        del_dirs: list,
        new_dirs: list,
    ):
        """
        Параметры:
        - del_dirs: [(rel_dir_path, mod_time), ...]

        Удаляет директории из таблицы DIRS
        """
        for rel_dir_path, mod in del_dirs:
            q = sqlalchemy.delete(DIRS)
            q = q.where(DIRS.c.short_src == rel_dir_path)
            q = q.where(DIRS.c.brand == main_folder.name)

            try:
                conn.execute(q)
            except Exception as e:
                MainUtils.print_error()
                conn.rollback()
                continue
        
        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()

    @classmethod
    def add_new_dirs(
        cls,
        conn: sqlalchemy.Connection,
        main_folder: MainFolder,
        del_dirs: list,
        new_dirs: list,
    ):
        """
        Параметры:
        - new_dirs: [(rel_dir_path, mod_time), ...]

        Добавляет директории в таблицу DIRS
        """
        for short_src, mod in new_dirs:
            values = {
                ClmNames.SHORT_SRC: short_src,
                ClmNames.MOD: mod,
                ClmNames.BRAND: main_folder.name
            }
            q = sqlalchemy.insert(DIRS).values(**values)

            try:
                conn.execute(q)
            except Exception as e:
                MainUtils.print_error()
                conn.rollback()
                continue
        
        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()


class ImgLoader:

    @classmethod
    def finder_images(
        cls,
        new_dirs: list,
        main_folder: MainFolder,
        task_state: TaskState,
        conn: sqlalchemy.Connection,
    ) -> list[tuple]:
        """
        Параметры:
        - new_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает изображения в указанных директориях:
        - [(abs_img_path, size, birth_time, mod_time), ...]    
        """
        finder_images = []
        main_folder_path = main_folder.get_current_path()


        def process_entry(entry: os.DirEntry):
            abs_img_path = entry.path
            stats = entry.stat()
            size = int(stats.st_size)
            birth = int(stats.st_birthtime)
            mod = int(stats.st_mtime)
            finder_images.append((abs_img_path, size, birth, mod))


        for rel_dir_path, mod in new_dirs:
            abs_dir_path = MainUtils.get_abs_path(main_folder_path, rel_dir_path)
            for entry in os.scandir(abs_dir_path):
                if entry.path.endswith(Static.ext_all):
                    try:
                        process_entry(entry)
                    except Exception as e:
                        MainUtils.print_error()
                        task_state.set_should_run(False)
                        break
        return finder_images

    @classmethod
    def db_images(
        cls,
        new_dirs: list,
        main_folder: MainFolder,
        task_state: TaskState,
        conn: sqlalchemy.Connection,
        ) -> list[tuple]:
        """
        Параметры:
        - new_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает изображения в указанных директориях:
        - {rel_thumb_path: (abs_img_path, size, birth, mod), ...}  
        """
        main_folder_path = main_folder.get_current_path()
        db_images: dict = {}
        for rel_dir_path, mod in new_dirs:
            q = sqlalchemy.select(
                THUMBS.c.short_hash, # rel thumb path
                THUMBS.c.short_src,
                THUMBS.c.size,
                THUMBS.c.birth,
                THUMBS.c.mod
                )
            q = q.where(THUMBS.c.short_src.ilike(f"{rel_dir_path}/%"))
            q = q.where(THUMBS.c.short_src.not_ilike(f"{rel_dir_path}/%/%"))
            q = q.where(THUMBS.c.brand == main_folder.name)
            try:
                res = conn.execute(q).fetchall()
                for rel_thumb_path, rel_img_path, size, birth, mod in res:
                    abs_img_path = MainUtils.get_abs_path(main_folder_path, rel_img_path)
                    db_images[rel_thumb_path] = (abs_img_path, size, birth, mod)
            except Exception:
                MainUtils.print_error()
                conn.rollback()
        return db_images


class ImgCompator:
    def __init__(self, finder_images: dict, db_images: dict):
        """
        Сравнивает данные об изображениях FinderImages и DbImages.  
        Запуск: run()

        Принимает:      
        finder_images: [(abs_img_path, size, birth_time, mod_time), ...]    
        db_images:  {rel thumb path: (abs img path, size, birth time, mod time), ...}

        Возвращает:
        del_items: [rel thumb path, ...]    
        new_items: [(abs img_path, size, birth, mod), ...]
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



class HashdirUpdater:
    # progress_text = pyqtSignal(str)

    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder, task_state: TaskState):
        """
        Удаляет thumbs из hashdir, добавляет thumbs в hashdir.  
        Запуск: run()   
        Сигналы: progress_text(str)
        
        Принимает:  
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  


        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        """
        super().__init__()
        self.del_items = del_items
        self.new_items = new_items
        self.main_folder = main_folder
        self.task_state = task_state

    def run(self) -> tuple[list, list]:
        """
        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        """
        if not self.task_state.should_run():
            return ([], [])
        del_items = self.run_del_items()
        new_items = self.run_new_items()
        # self.progress_text.emit("")
        return del_items, new_items

    def progressbar_text(self, text: str, x: int, total: int):
        """
        text: `Lang.adding`, `Lang.deleting`
        x: item of `enumerate`
        total: `len`
        """
        main_folder = self.main_folder.name.capitalize()
        t = f"{main_folder}: {text.lower()} {x} {Lang.from_} {total}"
        # self.progress_text.emit(t)

    def run_del_items(self):
        new_del_items = []
        total = len(self.del_items)
        for x, rel_thumb_path in enumerate(self.del_items, start=1):
            if not self.task_state.should_run():
                break
            thumb_path = ThumbUtils.get_thumb_path(rel_thumb_path)
            if os.path.exists(thumb_path):
                self.progressbar_text(Lang.deleting, x, total)
                try:
                    os.remove(thumb_path)
                    folder = os.path.dirname(thumb_path)
                    if not os.listdir(folder):
                        os.rmdir(folder)
                    new_del_items.append(rel_thumb_path)
                except Exception as e:
                    MainUtils.print_error()
                    continue
        return new_del_items

    def create_thumb(self, img_path: str) -> ndarray | None:
        img = ImgUtils.read_image(img_path)
        thumb = ThumbUtils.fit_to_thumb(img, ThumbData.DB_PIXMAP_SIZE)
        del img
        gc.collect()
        if isinstance(thumb, ndarray):
            return thumb
        else:
            return None

    def run_new_items(self):
        new_new_items = []
        total = len(self.new_items)
        for x, (img_path, size, birth, mod) in enumerate(self.new_items, start=1):
            if not self.task_state.should_run():
                break
            self.progressbar_text(Lang.adding, x, total)
            try:
                thumb = self.create_thumb(img_path)
                thumb_path = ThumbUtils.create_thumb_path(img_path)
                ThumbUtils.write_thumb(thumb_path, thumb)
                new_new_items.append((img_path, size, birth, mod))
            except Exception as e:
                MainUtils.print_error()
                continue
        return new_new_items


class DbUpdater:
    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder):
        """
        Удаляет записи thumbs из бд, добавляет записи thumbs в бд.  
        Запуск: run()  
        Сигналы: reload_gui()

        Принимает:  
        - del_items: [rel_thumb_path, ...]       
        - new_items: [(img_path, size, birth, mod), ...]          
        """
        super().__init__()
        self.main_folder = main_folder
        self.del_items = del_items
        self.new_items = new_items

    def run(self):
        self.run_del_items()
        self.run_new_items()

    def run_del_items(self):
        conn = Dbase.engine.connect()
        for rel_thumb_path in self.del_items:
            q = sqlalchemy.delete(THUMBS)
            q = q.where(THUMBS.c.short_hash==rel_thumb_path)
            q = q.where(THUMBS.c.brand==self.main_folder.name)
            try:
                conn.execute(q)
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
                MainUtils.print_error()
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                MainUtils.print_error()
                conn.rollback()
                return None
        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()

    def run_new_items(self):
        conn = Dbase.engine.connect()
        for img_path, size, birth, mod in self.new_items:
            small_img_path = ThumbUtils.create_thumb_path(img_path)
            short_img_path = MainUtils.get_rel_path(self.main_folder.get_current_path(), img_path)
            rel_thumb_path = ThumbUtils.get_rel_thumb_path(small_img_path)
            coll_name = MainUtils.get_coll_name(self.main_folder.get_current_path(), img_path)
            values = {
                ClmNames.SHORT_SRC: short_img_path,
                ClmNames.SHORT_HASH: rel_thumb_path,
                ClmNames.SIZE: size,
                ClmNames.BIRTH: birth,
                ClmNames.MOD: mod,
                ClmNames.RESOL: "",
                ClmNames.COLL: coll_name,
                ClmNames.FAV: 0,
                ClmNames.BRAND: self.main_folder.name
            }
            stmt = sqlalchemy.insert(THUMBS).values(**values) 
            try:
                conn.execute(stmt)
            # overflow error бывает прозникает когда пишет
            # python integer too large to insert db
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
                MainUtils.print_error()
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                MainUtils.print_error()
                conn.rollback()
                break
        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()

        if len(self.new_items) > 0:
            self.reload_gui.emit()


class ScanerSignals(QObject):
    finished_ = pyqtSignal()
    progress_text = pyqtSignal(str)
    reload_gui = pyqtSignal()


class ScanerTask(URunnable):
    short_timer = 15000
    long_timer = JsonData.scaner_minutes * 60 * 1000

    def __init__(self):
        """
        Сигналы: finished_, progress_text(str), reload_gui, remove_all_win(MainWin)
        """
        super().__init__()
        self.signals_ = ScanerSignals()
        self.pause_flag = False
        self.user_canceled_scan = False

    def task(self):
        main_folders = [
            i
            for i in MainFolder.list_
            if i.is_available()
        ]

        for i in main_folders:
            print("scaner started", i.name)
            self.main_folder_scan(i)
            gc.collect()
            print("scaner finished", i.name)
            
        try:
            self.signals_.finished_.emit()
        except RuntimeError as e:
            ...

    def main_folder_scan(self, main_folder: MainFolder):
        main_folder_remover = MainFolderRemover()
        main_folder_remover.progress_text.connect(lambda text: self.signals_.progress_text.emit(text))
        main_folder_remover.run()

        coll_folder = main_folder.is_available()
        if not coll_folder:
            print(main_folder.name, "coll folder not avaiable")
            return

        conn = Dbase.engine.connect()
        text = f"{main_folder.name}: ищу обновления"
        self.signals_.progress_text.emit(text)
        args = (main_folder, self.task_state, conn)
        finder_dirs = DirsLoader.finder_dirs(*args)
        db_dirs = DirsLoader.db_dirs(*args)
        conn.close()
        if not finder_dirs or not self.task_state.should_run():
            print(main_folder.name, "no finder dirs")
            return

        args = (finder_dirs, db_dirs)
        new_dirs = DirsCompator.get_add_to_db_dirs(*args)
        del_dirs = DirsCompator.get_rm_from_db_dirs(*args)

        conn = Dbase.engine.connect()
        text = f"{main_folder.name}: ищу изображения"
        self.signals_.progress_text.emit(text)
        args = (new_dirs, main_folder, self.task_state, conn)
        finder_images = ImgLoader.finder_images(*args)
        db_images = ImgLoader.db_images(*args)
        conn.close()
        if not finder_images or not self.task_state.should_run():
            print(main_folder.name, "no finder images")
            return
        

        args = (finder_images, db_images)
        img_compator = ImgCompator(*args)
        del_images, new_images = img_compator.run()

        inspector = Inspector(del_images, main_folder)
        is_remove_all = inspector.is_remove_all()
        if is_remove_all:
            print("scaner > обнаружена попытка массового удаления фотографий")
            print("в папке:", main_folder.name, main_folder.get_current_path())
            return

        text = f"Обновляю: {len(del_images) + len(new_images)}"
        self.signals_.progress_text.emit(text)
        args = (del_images, new_images, main_folder, self.task_state)
        hashdir_updater = HashdirUpdater(*args)
        del_images, new_images = hashdir_updater.run()

        db_updater = DbUpdater(del_images, new_images, main_folder)
        db_updater.run()

        conn = Dbase.engine.connect()
        args = (conn, main_folder, del_dirs, new_dirs)
        DirsUpdater.remove_db_dirs(*args)
        DirsUpdater.add_new_dirs(*args)
        conn.close()

        self.signals_.progress_text.emit("")
        if del_images or new_images:
            self.signals_.reload_gui.emit()

        print("del dirs", del_dirs)
        print("new dirs", new_dirs)
        print("del images", del_images)
        print("new images", new_images)


# добавление изображений работает
# удаление не работает
# TestScan.start()