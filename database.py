import os

import sqlalchemy

from cfg import Static
from utils.utils import Utils

METADATA = sqlalchemy.MetaData()

class ClmNames:
    ID = "id"
    SHORT_SRC = "short_src"
    SHORT_HASH = "short_hash"
    SIZE = "size"
    BIRTH = "birth"
    MOD = "mod"
    RESOL = "resol"
    COLL = "coll"
    FAV = "fav"
    BRAND = "brand"


THUMBS = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column(ClmNames.ID, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmNames.SHORT_SRC, sqlalchemy.Text),
    sqlalchemy.Column(ClmNames.SHORT_HASH, sqlalchemy.Text),
    sqlalchemy.Column(ClmNames.SIZE, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.BIRTH, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.MOD, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.RESOL, sqlalchemy.Text),
    sqlalchemy.Column(ClmNames.COLL, sqlalchemy.Text),
    sqlalchemy.Column(ClmNames.FAV, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.BRAND, sqlalchemy.Text),
)

DIRS = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column(ClmNames.ID, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmNames.SHORT_SRC, sqlalchemy.Text),
    sqlalchemy.Column(ClmNames.MOD, sqlalchemy.Integer),
    sqlalchemy.Column(ClmNames.BRAND, sqlalchemy.Text),
)

class Dbase:
    engine: sqlalchemy.Engine = None
    _timeout = 15
    _echo = False
    _same_thread = False
    WAL_ = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        cls.create_engine()
        cls.toggle_wal(False)

    @classmethod
    def create_engine(cls):
        if os.path.exists(Static.DB_FILE):
            cls.engine = sqlalchemy.create_engine(
                f"sqlite:///{Static.DB_FILE}",
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
            Utils.print_error(e)
            return False
        
    @classmethod
    def toggle_wal(cls, value: bool):
        with cls.engine.connect() as conn:
            if value:
                conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
                cls.WAL_ = True
            else:
                conn.execute(sqlalchemy.text("PRAGMA journal_mode=DELETE"))
                cls.WAL_ = False

    @classmethod
    def vacuum(cls):
        conn = cls.engine.connect()
        conn.execute(sqlalchemy.text("VACUUM"))
        conn.commit()
