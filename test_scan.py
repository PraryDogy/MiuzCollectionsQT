import os
from time import time

import sqlalchemy

from cfg import JsonData
from database import DIRS, THUMBS, ClmNames, Dbase
from main_folders import MainFolder, miuz, panacea
from utils.utils import Utils


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
                            Utils.get_short_src(main_folder_path, i.path),
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
    def get_del_dirs(cls, finder_dirs: list, db_dirs: list):
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
    @classmethod
    def get_images_dir(cls, conn: sqlalchemy.Connection, short_src: str, main_folder_name: str):
        """
        Загружает изображения, соответствующие директории
        """

        stmt = sqlalchemy.select(THUMBS.c.short_src)
        stmt = stmt.where(THUMBS.c.short_src.like(f"{short_src}/%"))
        # stmt = stmt.where(sqlalchemy.not_(THUMBS.c.short_src.like(f"{short_src}/%/%")))
        stmt = stmt.where(THUMBS.c.brand == main_folder_name)
        return conn.execute(stmt).fetchall()


coll_folder = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready"
src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/52 Florance"


MainFolder.list_.append(miuz)
MainFolder.list_.append(panacea)
MainFolder.current = MainFolder.list_[0]

Dbase.create_engine()
conn = Dbase.engine.connect()
JsonData.init()

# for main_folder in MainFolder.list_[1:]:
#     coll_folder = main_folder.set_current_path()
#     if main_folder.is_avaiable():
#         finder_dirs = Dirs.get_finder_dirs(main_folder.current_path)
#         if finder_dirs:
#             db_dirs = Dirs.get_db_dirs(conn, main_folder.name)
#             del_dirs = Dirs.get_del_dirs(finder_dirs, db_dirs)
#             new_dirs = Dirs.get_new_dirs(finder_dirs, db_dirs)



#             # это нужно будет делать в самом конце, когда уже просканены 
#             # изображения
#             if del_dirs:
#                 Dirs.execute_del_dirs(conn, del_dirs, main_folder.name)
#                 print("del dirs", del_dirs)

#             if new_dirs:
#                 Dirs.execute_new_dirs(conn, new_dirs, main_folder.name)
#                 print("new dirs", new_dirs)

#         break

a = Images.get_images_dir(conn, "/42 Amalia", "panacea")


for i in a:
    print(i)

conn.close()