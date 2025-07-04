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
        - new_dirs: [(относительный путь к директории, дата изменения), ...]

        Возвращает изображения в указанных директориях:
        - finder_images: [(относительный путь к директории, дата изменения), ...]
        """
        finder_images = []
        for rel_dir_path, mod in new_dirs:
            abs_dir_path = MainUtils.get_abs_path(main_folder.curr_path, rel_dir_path)
            for i in os.scandir(abs_dir_path):
                if i.path.endswith(Static.ext_all):
                    try:
                        rel_img_path = MainUtils.get_rel_path(main_folder.curr_path, i.path)
                        mod = os.stat(i.path).st_mtime
                        finder_images.append((rel_img_path, mod))
                    except Exception as e:
                        MainUtils.print_error()
                        continue
        return finder_images











coll_folder = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready"
src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/52 Florance"


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

#             # это нужно будет делать в самом конце, когда уже просканены 
#             # изображения
#             if del_dirs:
#                 Dirs.execute_del_dirs(conn, del_dirs, main_folder.name)
#                 print("del dirs", del_dirs)

#             if new_dirs:
#                 Dirs.execute_new_dirs(conn, new_dirs, main_folder.name)
#                 print("new dirs", new_dirs)

#         break

# a = Images.get_db_images(conn, "/42 Amalia/1 IMG", "miuz")


conn.close()