import gc
import os

import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, pyqtSignal

from cfg import JsonData, Static, ThumbData
from system.database import DIRS, THUMBS, ClmNames, Dbase
from system.lang import Lang
from system.main_folder import MainFolder
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


class Inspector:
    def __init__(self, del_items: list, main_folder: MainFolder):
        """
        del_items: [rel thumb path, ...]

        Этот класс выполняет проверку безопасности перед удалением данных.
        Метод is_remove_all() инициирует сравнение между количеством записей
        в БД и количеством удаляемых миниатюр, связанных с MainFolder.

        Если количество удаляемых элементов совпадает с количеством записей в базе,
        это может свидетельствовать о потенциальной ошибке в логике сканера,
        приводящей к попытке удалить все данные, связанные с MainFolder.
        В таком случае, операция считается подозрительной и может быть заблокирована
        как мера предосторожности.
        """
        super().__init__()
        self.del_items = del_items
        self.main_folder = main_folder
    
    def is_remove_all(self):
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(sqlalchemy.func.count())
        q = q.where(THUMBS.c.brand == self.main_folder.name)
        result = conn.execute(q).scalar()
        conn.close()
        if len(self.del_items) == result and len(self.del_items) != 0:
            return True
        return None


class MainFolderRemover:
    def __init__(self):
        """
        Запуск: run()   
        Сигналы: progress_text(str)

        Сверяет список экземпляров класса MainFolder в бд (THUMBS.c.brand)     
        со списком MainFolder в приложении.     
        Удаляет весь контент MainFolder, если MainFolder больще нет в бд:   
        - изображения thumbs из hashdir в ApplicationSupport    
        - записи в базе данных

        Вызови run для работы
        """
        super().__init__()
        self.conn = Dbase.engine.connect()

    def run(self):
        q = sqlalchemy.select(THUMBS.c.brand).distinct()
        db_main_folders = self.conn.execute(q).scalars().all()
        app_main_folders = [i.name for i in MainFolder.list_]
        del_main_folders = [i for i in db_main_folders if i not in app_main_folders]
        for i in del_main_folders:
            rows = self.get_rows(i)
            self.remove_images(rows)
            self.remove_rows(rows)
        self.conn.close()
        
    def get_rows(self, main_folder_name):
        q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.short_hash) #rel thumb path
        q = q.where(THUMBS.c.brand == main_folder_name)
        res = self.conn.execute(q).fetchall()
        res = [
            (id_, ThumbUtils.get_thumb_path(rel_thumb_path))
            for id_, rel_thumb_path in res
        ]
        return res

    def remove_images(self, rows: list):
        """
        rows: [(row id int, thumb path), ...]
        """
        total = len(rows)
        for x, (id_, image_path) in enumerate(rows):
            try:
                t = f"{Lang.deleting}: {x} {Lang.from_} {total}"
                self.progress_text.emit(t)

                if os.path.exists(image_path):
                    os.remove(image_path)
                folder = os.path.dirname(image_path)
                if os.path.exists(folder) and not os.listdir(folder):
                    os.rmdir(folder)

            except Exception as e:
                MainUtils.print_error()
                continue

    def remove_rows(self, rows: list):
        """
        rows: [(row id int, thumb path), ...]
        """
        for id_, thumb_path in rows:
            q = sqlalchemy.delete(THUMBS)
            q = q.where(THUMBS.c.id == id_)

            try:
                self.conn.execute(q)
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
                MainUtils.print_error()
                self.conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                MainUtils.print_error()
                self.conn.rollback()
                break
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            MainUtils.print_error()
