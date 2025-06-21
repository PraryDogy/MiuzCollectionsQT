import os
from time import time

import sqlalchemy
from sqlalchemy import func

from cfg import JsonData
from database import DIRS, THUMBS, ClmNames, Dbase
from main_folder import MainFolder, miuz, panacea
from utils.main import Utils


class Dirs:

    @classmethod
    def get_finder_dirs(cls, main_folder_path: str):
        dirs: list[tuple[str, int]] = []
        stack = [main_folder_path]

        while stack:
            current = stack.pop()
            for i in os.scandir(current):
                if i.is_dir():
                    stack.append(i.path)
                    dirs.append(
                        (
                            Utils.get_short_img_path(main_folder_path, i.path),
                            int(i.stat().st_mtime)
                        )
                    )

        return dirs

    @classmethod
    def get_db_dirs(cls, conn: sqlalchemy.Connection, main_folder_name: str):
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod)
        q = q.where(DIRS.c.brand==main_folder_name)
        res = conn.execute(q).fetchall()
        return [
            (short_src, mod)
            for short_src, mod in res
        ]
    
    @classmethod
    def get_removed_dirs(cls, finder_dirs: list, db_dirs: list):
        del_dirs = []

        for short_src, mod in db_dirs:
            if (short_src, mod) not in finder_dirs:
                del_dirs.append((short_src, mod))

        return del_dirs

    @classmethod
    def get_new_dirs(cls, finder_dirs: dict, db_dirs: dict):
        new_dirs = []

        for i in finder_dirs:
            if i not in db_dirs:
                new_dirs.append(i)

        return new_dirs
    
    @classmethod
    def execute_del_dirs(cls, conn: sqlalchemy.Connection, del_dirs: list, main_folder_name: str):
        for short_src, mod in del_dirs:
            q = sqlalchemy.delete(DIRS)
            q = q.where(DIRS.c.short_src == short_src)
            q = q.where(DIRS.c.brand == main_folder_name)

            try:
                conn.execute(q)
            except Exception as e:
                Utils.print_error(e)
                conn.rollback()
                continue
        
        try:
            conn.commit()
        except Exception as e:
            Utils.print_error(e)
            conn.rollback()

    @classmethod
    def execute_new_dirs(cls, conn: sqlalchemy.Connection, new_dirs: list, main_folder_name: str):
        for short_src, mod in new_dirs:

            values = {
                ClmNames.SHORT_SRC: short_src,
                ClmNames.MOD: mod,
                ClmNames.BRAND: main_folder_name
            }


            q = sqlalchemy.insert(DIRS).values(**values)

            try:
                conn.execute(q)
            except Exception as e:
                Utils.print_error(e)
                conn.rollback()
                continue
        
        try:
            conn.commit()
        except Exception as e:
            Utils.print_error(e)
            conn.rollback()


class Images:
    def __init__(self, conn: sqlalchemy.Connection, short_src: str, main_folder: MainFolder):
        super().__init__()
        self.conn = conn
        self.short_src = short_src
        self.main_folder = main_folder

    def get_db_images(self):
        """
        Загружает изображения, соответствующие директории,
        исключая поддиректории
        """
        sep_count = self.short_src.count(os.sep) + 1
        no_sep = func.replace(THUMBS.c.short_src, "/", "")
        sep_count_expr = (func.length(THUMBS.c.short_src) - func.length(no_sep))

        stmt = sqlalchemy.select(
            THUMBS.c.short_hash,
            THUMBS.c.short_src,
            THUMBS.c.size,
            THUMBS.c.birth,
            THUMBS.c.mod
            )
        
        stmt = stmt.where(
            THUMBS.c.short_src.like(f"{self.short_src}/%"),
            sep_count_expr == sep_count,
            THUMBS.c.brand == self.main_folder.name
        )

        return conn.execute(stmt).fetchall()
    
    def get_finder_images(self):
        finder_images = []

        for i in os.scandir(self.main_folder.get_current_path()):
            ...


    def get_file_data(self, entry: os.DirEntry) -> tuple[str, int, int, int]:
        """Получает данные файла."""
        stats = entry.stat()
        return (
            entry.path,
            int(stats.st_size),
            int(stats.st_birthtime),
            int(stats.st_mtime),
        )


coll_folder = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready"
src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/52 Florance"


MainFolder.list_.append(miuz)
MainFolder.list_.append(panacea)
MainFolder.current = MainFolder.list_[0]

Dbase.create_engine()
conn = Dbase.engine.connect()
JsonData.init()

for main_folder in MainFolder.list_:
    coll_folder = main_folder.check_avaiability()
    if main_folder.is_avaiable():
        finder_dirs = Dirs.get_finder_dirs(main_folder.current_path)
        if finder_dirs:
            db_dirs = Dirs.get_db_dirs(conn, main_folder.name)
            removed_dirs = Dirs.get_removed_dirs(finder_dirs, db_dirs)
            new_dirs = Dirs.get_new_dirs(finder_dirs, db_dirs)

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