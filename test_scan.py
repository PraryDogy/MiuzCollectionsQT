import os
from time import time

import sqlalchemy
from cfg import Static

from cfg import JsonData
from system.database import DIRS, THUMBS, ClmNames, Dbase
from system.main_folder import MainFolder
from system.utils import MainUtils


class DirsLoader:

    @classmethod
    def load_finder_dirs(cls, main_folder: MainFolder) -> list:
        """
        Возвращает:
        - [(относительный путь к директории, дата изменения), ...]
        """
        dirs = []
        stack = [main_folder.curr_path]

        while stack:
            current = stack.pop()
            with os.scandir(current) as it:
                for entry in it:
                    if entry.is_dir():
                        stack.append(entry.path)
                        rel_path = MainUtils.get_rel_path(main_folder.curr_path, entry.path)
                        dirs.append((rel_path, int(entry.stat().st_mtime)))
        return dirs

    @classmethod
    def load_db_dirs(cls, conn: sqlalchemy.Connection, main_folder: MainFolder) -> list:
        """
        Возвращает:
        - [(относительный путь к директории, дата изменения), ...]
        """
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod)
        q = q.where(DIRS.c.brand == main_folder.name)
        res = conn.execute(q).fetchall()
        return [(short_src, mod) for short_src, mod in res]


class DirsCompator:
    @classmethod
    def get_removed_dirs(cls, finder_dirs: list, db_dirs: list) -> list :
        """
        Параметры:
        - finder_dirs: [(относительный путь к директории, дата изменения), ...]
        - db_dirs: [(относительный путь к директории, дата изменения), ...]

        Возвращает те директории, которых нет в finder_dirs, но есть в db_dirs:
        - [(относительный путь к директории, дата изменения), ...]
        """
        return [
            (rel_dir_path, mod)
            for rel_dir_path, mod in db_dirs
            if (rel_dir_path, mod) not in finder_dirs
        ]

    @classmethod
    def get_new_dirs(cls, finder_dirs: list, db_dirs: list) -> list:
        """
        Параметры:
        - finder_dirs: [(относительный путь к директории, дата изменения), ...]
        - db_dirs: [(относительный путь к директории, дата изменения), ...]

        Возвращает те директории, которых нет в db_dirs, но есть в finder_dirs:
        - [(относительный путь к директории, дата изменения), ...]
        """
        return [
            (rel_dir_path, mod)
            for (rel_dir_path, mod) in finder_dirs
            if (rel_dir_path, mod) not in db_dirs
        ]


class DirsUpdater:
    @classmethod
    def remove_db_dirs(cls, conn: sqlalchemy.Connection, del_dirs: list, main_folder: MainFolder):
        """
        Параметры:
        - del_dirs: [(относительный путь к директории, дата изменения), ...]

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
    def add_new_dirs(cls, conn: sqlalchemy.Connection, new_dirs: list, main_folder: MainFolder):
        """
        Параметры:
        - new_dirs: [(относительный путь к директории, дата изменения), ...]

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


class ImagesLoader:

    @classmethod
    def load_finder_images(cls, new_dirs: list, main_folder: MainFolder) -> list:
        """
        Параметры:
        - new_dirs: [(rel_dir_path, mod_time), ...]

        Возвращает изображения в указанных директориях:
        - finder_images: [(rel_img_path, size, birth_time, mod_time), ...]    
        """
        finder_images = []
        for rel_dir_path, mod in new_dirs:
            abs_dir_path = MainUtils.get_abs_path(main_folder.curr_path, rel_dir_path)
            for i in os.scandir(abs_dir_path):
                if i.path.endswith(Static.ext_all):
                    try:
                        rel_img_path = MainUtils.get_rel_path(main_folder.curr_path, i.path)
                        stats = os.stat(i.path)
                        size = stats.st_size
                        birth = stats.st_birthtime
                        mod = stats.st_mtime
                        finder_images.append((rel_img_path, size, birth, mod))
                    except Exception as e:
                        MainUtils.print_error()
                        continue
        return finder_images

    @classmethod
    def load_db_images(cls, new_dirs: list, main_folder: MainFolder, conn: sqlalchemy.Connection):
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


class ImagesCompator:

    @classmethod
    def get_removed_images(cls, finder_images: list, db_images: list) -> list:
        """
        Параметры:
        - finder_images: [(относительный путь к изображению, дата изменения), ...]
        - db_dirs: [(относительный путь к изображению, дата изменения), ...]

        Возвращает те изображения, которых нет в finder_dirs, но есть в db_dirs:
        - [(относительный путь к изображению, дата изменения), ...]
        """
        return [
            (rel_img_path, mod)
            for rel_img_path, mod in db_images
            if (rel_img_path, mod) not in finder_images
        ]
    
    @classmethod
    def get_new_images(cls, finder_images: list, db_images: list) -> list:
        """
        Параметры:
        - finder_images: [(относительный путь к изображению, дата изменения), ...]
        - db_dirs: [(относительный путь к изображению, дата изменения), ...]

        Возвращает те изображения, которых нет в db_dirs, но есть в finder_dirs:
        - [(относительный путь к изображению, дата изменения), ...]
        """
        return [
            (rel_img_path, mod)
            for rel_img_path, mod in finder_images
            if (rel_img_path, mod) not in db_images
        ]


MainFolder.set_default_main_folders()
Dbase.create_engine()
conn = Dbase.engine.connect()
JsonData.init()

for main_folder in MainFolder.list_:
    coll_folder = main_folder.is_available()
    if main_folder:

        finder_dirs = DirsLoader.load_finder_dirs(main_folder.current_path)
        if finder_dirs:
            db_dirs = DirsLoader.load_db_dirs(conn, main_folder.name)
            removed_dirs = DirsLoader.get_removed_dirs(finder_dirs, db_dirs)
            new_dirs = DirsLoader.get_new_dirs(finder_dirs, db_dirs)

conn.close()