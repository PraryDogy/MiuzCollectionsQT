import os
from time import time

import sqlalchemy

from database import DIRS, Dbase, ThumbColumns
from utils.utils import Utils


class Dirs:

    @classmethod
    def get_dirs(cls, coll_folder: str, dir: str):
        dirs: dict[str, int] = {}
        stack = [dir]

        while stack:
            current = stack.pop()
            for i in os.scandir(current):
                if i.is_dir():
                    dirs[Utils.get_short_src(coll_folder, i.path)] =  int(i.stat().st_mtime)
                    stack.append(i)

        return dirs

    @classmethod
    def get_db_dirs(cls):
        Dbase.create_engine()
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(DIRS.c.short_src, DIRS.c.mod)
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
                ThumbColumns.SHORT_SRC: short_src,
                ThumbColumns.MOD: mod
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

dirs = Dirs.get_dirs(coll_folder, src)
db_dirs = Dirs.get_db_dirs()
# del_dirs = Dirs.get_del_dirs(dirs, db_dirs)
# new_dirs = Dirs.get_new_dirs(dirs, del_dirs)
# Dirs.execute_del_dirs(conn, del_dirs)


print(dirs)
print(db_dirs)


# if new_dirs:
    # print(new_dirs)
    # Dirs.execute_new_dirs(conn, new_dirs)

conn.close()