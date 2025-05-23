import os
from time import time

import sqlalchemy

from cfg import JsonData
from database import DIRS, Dbase, ClmNames
from utils.utils import Utils
from main_folders import MainFolder

class Dirs:

    @classmethod
    def get_dirs(cls, main_folder_path: str):
        dirs: dict[str, int] = {}
        stack = [main_folder_path]

        while stack:
            current = stack.pop()
            for i in os.scandir(current):
                if i.is_dir():
                    dirs[Utils.get_short_src(coll_folder, i.path)] =  int(i.stat().st_mtime)
                    stack.append(i)

        return dirs

    @classmethod
    def get_db_dirs(cls, conn: sqlalchemy.Connection, main_folder_name: str):
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod)
        q = q.where(DIRS.c.brand==main_folder_name)
        res = conn.execute(q).fetchall()
        return {
            short_src: mod
            for short_src, mod in res
        }
    
    @classmethod
    def get_del_dirs(cls, dirs: dict, db_dirs: dict):
        del_dirs = []

        for short_src, mod in db_dirs.items():
            
            if short_src not in dirs:
                ...

        return del_dirs

    @classmethod
    def get_new_dirs(cls, dirs: dict, db_dirs: dict):
        new_dirs = []

        for i in dirs:
            if i not in db_dirs:
                new_dirs.append(i)

        return new_dirs
    
    @classmethod
    def execute_del_dirs(cls, conn: sqlalchemy.Connection, del_dirs):
        for short_src, mod in del_dirs:
            q = sqlalchemy.delete(Dirs).where(Dirs.c.short_src == short_src)

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
    def execute_new_dirs(cls, conn: sqlalchemy.Connection, del_dirs):
        for short_src, mod in del_dirs:

            values = {
                ClmNames.SHORT_SRC: short_src,
                ClmNames.MOD: mod
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

coll_folder = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready"
src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/52 Florance"

Dbase.create_engine()
conn = Dbase.engine.connect()
JsonData.init()

for main_folder in MainFolder.list_:
    coll_folder = Utils.get_main_folder_path(main_folder)
    main_folder.set_current_path(coll_folder)
    finder_dirs = Dirs.get_dirs(main_folder.current_path)
    db_dirs = Dirs.get_db_dirs(conn, main_folder.name)
    print(db_dirs)

conn.close()