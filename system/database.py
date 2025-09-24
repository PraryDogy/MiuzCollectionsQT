import os

import sqlalchemy

from cfg import Static
from system.utils import Utils

METADATA = sqlalchemy.MetaData()

class ClmNames:
    id = "id"
    short_src = "short_src" #relative img path
    short_hash = "short_hash" #relative thumb path
    size = "size"
    birth = "birth"
    mod = "mod"
    resol = "resol" #ignore
    coll = "coll"
    fav = "fav"
    brand = "brand" # Mf name


THUMBS = sqlalchemy.Table(
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
    sqlalchemy.Column(ClmNames.brand, sqlalchemy.Text, comment="Mf.name (смотри system > main_folder)"),
)

DIRS = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column(ClmNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmNames.short_src, sqlalchemy.Text),
    sqlalchemy.Column(ClmNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.brand, sqlalchemy.Text),
)

class Dbase:
    engine: sqlalchemy.Engine = None
    _timeout = 5
    _echo = False
    _same_thread = False
    WAL_ = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        cls.create_engine()
        cls.toggle_wal(False)

    @classmethod
    def create_engine(cls):
        if os.path.exists(Static.APP_SUPPORT_DB):
            cls.engine = sqlalchemy.create_engine(
                f"sqlite:///{Static.APP_SUPPORT_DB}",
                echo=cls._echo,
                connect_args={
                    "check_same_thread": cls._same_thread,
                    "timeout": cls._timeout
                    }
                    )
            METADATA.create_all(cls.engine)

            conn = cls.engine.connect()
            check = cls.check_table(DIRS, conn)
            if not check:
                DIRS.drop(cls.engine)
                METADATA.create_all(cls.engine)

            conn.close()
            
        else:
            t = "Нет пользовательского файла DB_FILE"
            raise Exception(t)
        
    @classmethod
    def check_table(cls, table: sqlalchemy.Table, conn: sqlalchemy.Connection) -> bool:
        try:
            if not cls.engine.dialect.has_table(conn, table.name):
                return False
            q = sqlalchemy.select(table)
            conn.execute(q).first()
            return True
        except Exception as e:
            Utils.print_error()
            return False
        
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
