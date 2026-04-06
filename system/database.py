import os
import traceback
from typing import Literal

import sqlalchemy
from sqlalchemy.exc import IntegrityError, OperationalError

from cfg import Static
from system.utils import Utils

METADATA = sqlalchemy.MetaData()


_table_thumbs = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("short_src", sqlalchemy.Text),
    sqlalchemy.Column("short_hash", sqlalchemy.Text),
    sqlalchemy.Column("size", sqlalchemy.Integer),
    sqlalchemy.Column("birth", sqlalchemy.Integer),
    sqlalchemy.Column("mod", sqlalchemy.Integer),
    sqlalchemy.Column("resol", sqlalchemy.Text),
    sqlalchemy.Column("coll", sqlalchemy.Text),
    sqlalchemy.Column("fav", sqlalchemy.Integer),
    sqlalchemy.Column("brand", sqlalchemy.Text),
)


class Thumbs:
    """
    Класс-обёртка для колонок таблицы `thumbs` в базе данных.   
    Предоставляет удобный доступ к колонкам через атрибуты класса.
    """
    table = _table_thumbs
    id = _table_thumbs.c.id
    rel_img_path = _table_thumbs.c.short_src
    rel_thumb_path = _table_thumbs.c.short_hash
    size = _table_thumbs.c.size
    birth = _table_thumbs.c.birth
    mod = _table_thumbs.c.mod
    root = _table_thumbs.c.resol
    coll = _table_thumbs.c.coll
    fav = _table_thumbs.c.fav
    mf_alias = _table_thumbs.c.brand


_table_dirs = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("short_src", sqlalchemy.Text),
    sqlalchemy.Column("mod", sqlalchemy.Integer),
    sqlalchemy.Column("brand", sqlalchemy.Text),
)


class Dirs:
    """
    Класс-обёртка для колонок таблицы `dirs` в базе данных.   
    Предоставляет удобный доступ к колонкам через атрибуты класса.
    """
    table = _table_dirs
    id = _table_dirs.c.id
    rel_dir_path = _table_dirs.c.short_src
    mod = _table_dirs.c.mod
    mf_alias = _table_dirs.c.brand


class Dbase:
    main_engine: sqlalchemy.Engine = None
    _timeout = 5
    _echo = False
    _same_thread = False
    WAL_ = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        Dbase.main_engine = cls.create_engine()
        cls.toggle_wal(False)

    @classmethod
    def create_engine(cls):
        if os.path.exists(Static.external_db):
            engine = sqlalchemy.create_engine(
                f"sqlite:///{Static.external_db}",
                echo=cls._echo,
                connect_args={
                    "check_same_thread": cls._same_thread,
                    "timeout": cls._timeout
                    }
                    )
            METADATA.create_all(engine)
            return engine
        else:
            t = "Нет пользовательского файла DB_FILE"
            raise Exception(t)
        
    @classmethod
    def toggle_wal(cls, value: bool):
        conn = Dbase.main_engine.connect()
        if value:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
            cls.WAL_ = True
        else:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=DELETE"))
            cls.WAL_ = False
        conn.close()

    @classmethod
    def vacuum(cls):
        conn = cls.main_engine.connect()

        try:
            conn.execute(sqlalchemy.text("VACUUM"))
            conn.commit()
        except Exception as e:
            Utils.print_error()

        conn.close()