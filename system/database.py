import os
from typing import Literal

import sqlalchemy

from cfg import Static
from system.utils import Utils

METADATA = sqlalchemy.MetaData()


class ColumnNames:
    id: Literal["id"] = "id"
    short_src: Literal["short_src"] = "short_src"
    short_hash: Literal["short_hash"] = "short_hash"
    size: Literal["size"] = "size"
    birth: Literal["birth"] = "birth"
    mod: Literal["mod"] = "mod"
    resol: Literal["resol"] = "resol"
    coll: Literal["coll"] = "coll"
    fav: Literal["fav"] = "fav"
    brand: Literal["brand"] = "brand"


_table_thumbs = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column(ColumnNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ColumnNames.short_src, sqlalchemy.Text),
    sqlalchemy.Column(ColumnNames.short_hash, sqlalchemy.Text),
    sqlalchemy.Column(ColumnNames.size, sqlalchemy.Integer),
    sqlalchemy.Column(ColumnNames.birth, sqlalchemy.Integer),
    sqlalchemy.Column(ColumnNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ColumnNames.resol, sqlalchemy.Text),
    sqlalchemy.Column(ColumnNames.coll, sqlalchemy.Text),
    sqlalchemy.Column(ColumnNames.fav, sqlalchemy.Integer),
    sqlalchemy.Column(ColumnNames.brand, sqlalchemy.Text),
)


_table_dirs = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column(ColumnNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ColumnNames.short_src, sqlalchemy.Text),
    sqlalchemy.Column(ColumnNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ColumnNames.brand, sqlalchemy.Text),
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
    resol = _table_thumbs.c.resol
    coll = _table_thumbs.c.coll
    fav = _table_thumbs.c.fav
    mf_alias = _table_thumbs.c.brand


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
    engine: sqlalchemy.Engine = None
    _timeout = 5
    _echo = False
    _same_thread = False
    WAL_ = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        cls.engine = cls.create_engine()
        cls.toggle_wal(False)

    @classmethod
    def create_engine(cls):
        if os.path.exists(Static.app_support_db):
            engine = sqlalchemy.create_engine(
                f"sqlite:///{Static.app_support_db}",
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
        conn = cls.engine.connect()
        if value:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
            cls.WAL_ = True
        else:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=DELETE"))
            cls.WAL_ = False
        conn.close()

    @classmethod
    def vacuum(cls):
        conn = cls.engine.connect()

        try:
            conn.execute(sqlalchemy.text("VACUUM"))
            conn.commit()
        except Exception as e:
            Utils.print_error()

        conn.close()
