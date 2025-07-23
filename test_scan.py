import os
from time import time

import sqlalchemy

from cfg import JsonData, Static
from system.database import DIRS, THUMBS, ClmNames, Dbase
from system.main_folder import MainFolder
from system.scaner_utils import Compator, DbUpdater, HashdirUpdater, Inspector
from system.utils import MainUtils, TaskState


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
                dirs.append((rel_path, int(entry.stat().st_mtime)))


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
        - [(относительный путь к директории, дата изменения), ...]
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


class Updater:
    @classmethod
    def remove_db_dirs(
        cls,
        conn: sqlalchemy.Connection,
        del_dirs: list,
        main_folder: MainFolder,
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
        new_dirs: list,
        main_folder: MainFolder,
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
        - finder_images: [(rel_img_path, size, birth_time, mod_time), ...]    
        """
        finder_images = []
        main_folder_path = main_folder.get_current_path()


        def process_entry(entry: os.DirEntry):
            rel_img_path = MainUtils.get_rel_path(main_folder_path, entry.path)
            stats = entry.stat()
            size = stats.st_size
            birth = stats.st_birthtime
            mod = stats.st_mtime
            finder_images.append((rel_img_path, size, birth, mod))


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
        - db_images: [(rel_img_path, size, birth_time, mod_time), ...]    
        """
        db_images: list = []
        for rel_dir_path, mod in new_dirs:
            q = sqlalchemy.select(
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
                db_images.extend(res)
            except Exception:
                MainUtils.print_error()
                conn.rollback()
        return db_images


class ImgCompator:

    @classmethod
    def get_rm_from_db_images(cls, finder_images: list, db_images: list) -> list:
        """
        Параметры:
        - finder_images: [(относительный путь к изображению, дата изменения), ...]
        - db_dirs: [(относительный путь к изображению, дата изменения), ...]

        Возвращает те изображения, которых нет в finder_dirs, но есть в db_dirs:
        - [(относительный путь к изображению, дата изменения), ...]
        """
        finder_set = set(finder_images)
        return [
            (rel_img_path, mod)
            for rel_img_path, mod in db_images
            if (rel_img_path, mod) not in finder_set
        ]
    
    @classmethod
    def get_add_to_db_images(cls, finder_images: list, db_images: list) -> list:
        """
        Параметры:
        - finder_images: [(относительный путь к изображению, дата изменения), ...]
        - db_dirs: [(относительный путь к изображению, дата изменения), ...]

        Возвращает те изображения, которых нет в db_dirs, но есть в finder_dirs:
        - [(относительный путь к изображению, дата изменения), ...]
        """
        db_set = set(db_images)
        return [
            (rel_img_path, mod)
            for rel_img_path, mod in finder_images
            if (rel_img_path, mod) not in db_set
        ]



class TestScan:

    @classmethod
    def start():
        MainFolder.set_default_main_folders()
        Dbase.create_engine()
        conn = Dbase.engine.connect()
        JsonData.init()
        task_state = TaskState()

        for main_folder in MainFolder.list_:
            coll_folder = main_folder.is_available()
            if not coll_folder:
                return

            args = (main_folder, task_state, conn)
            finder_dirs = DirsLoader.finder_dirs(*args)
            if not finder_dirs or not task_state.should_run():
                return

            db_dirs = DirsLoader.db_dirs(*args)

            args = (finder_dirs, db_dirs)
            new_dirs = DirsCompator.get_add_to_db_dirs(*args)
            del_dirs = DirsCompator.get_rm_from_db_dirs(*args)

            args = (new_dirs, main_folder, task_state, conn)
            finder_images = ImgLoader.finder_images(*args)
            if not finder_images or not task_state.should_run():
                return
            
            db_images = ImgLoader.db_images(args)
            
            args = (finder_images, db_images)
            new_images = ImgCompator.get_add_to_db_images(*args)
            del_images = ImgCompator.get_rm_from_db_images(*args)

            inspector = Inspector(del_images, main_folder)
            is_remove_all = inspector.is_remove_all()
            if is_remove_all:
                print("scaner > обнаружена попытка массового удаления фотографий")
                print("в папке:", main_folder.name, main_folder.get_current_path())
                return

            # обновляем хэш
            # обновляем бд

            # обновляем бд дирс

            # print("new method", "finder images", len(finder_images), main_folder.name)
            # print("new method", "db images", len(db_images), main_folder.name)


            Updater.remove_db_dirs(conn, del_dirs, main_folder)
            Updater.add_new_dirs(conn, new_dirs, main_folder)


TestScan.start()