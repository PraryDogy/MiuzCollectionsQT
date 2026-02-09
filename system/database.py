import os
from typing import Literal

import sqlalchemy
from cfg import Static
from system.utils import Utils

METADATA = sqlalchemy.MetaData()


class ClmNames:
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


THUMBS_TABLE = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column(ClmNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmNames.short_src, sqlalchemy.Text, comment="относительный путь к изображению"),
    sqlalchemy.Column(ClmNames.short_hash, sqlalchemy.Text, comment="относительный путь к миниатюре"),
    sqlalchemy.Column(ClmNames.size, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.birth, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.resol, sqlalchemy.Text, comment="более не используется"),
    sqlalchemy.Column(ClmNames.coll, sqlalchemy.Text, comment="более не используется"),
    sqlalchemy.Column(ClmNames.fav, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.brand, sqlalchemy.Text, comment="Mf.alias (смотри system > main_folder)"),
)


class Thumbs:
    id = THUMBS_TABLE.c.id
    rel_img_path = THUMBS_TABLE.c.short_src
    rel_thumb_path = THUMBS_TABLE.c.short_hash
    size = THUMBS_TABLE.c.size
    birth = THUMBS_TABLE.c.birth
    mod = THUMBS_TABLE.c.mod
    resol = THUMBS_TABLE.c.resol
    coll = THUMBS_TABLE.c.coll
    fav = THUMBS_TABLE.c.fav
    mf_alias = THUMBS_TABLE.c.brand


DIRS = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column(ClmNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmNames.short_src, sqlalchemy.Text, comment="относительный путь к директории"),
    sqlalchemy.Column(ClmNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.brand, sqlalchemy.Text, comment="Mf.name (смотри system > main_folder)"),
)






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
