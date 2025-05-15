import os

import sqlalchemy

from cfg import Static

METADATA = sqlalchemy.MetaData()

class ThumbColumns:
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
    sqlalchemy.Column(ThumbColumns.ID, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ThumbColumns.SHORT_SRC, sqlalchemy.Text),
    sqlalchemy.Column(ThumbColumns.SHORT_HASH, sqlalchemy.Text, comment="Путь к маленькой картинке"),
    sqlalchemy.Column(ThumbColumns.SIZE, sqlalchemy.Integer, comment="Размер"),
    sqlalchemy.Column(ThumbColumns.BIRTH, sqlalchemy.Integer, comment="Дата созд."),
    sqlalchemy.Column(ThumbColumns.MOD, sqlalchemy.Integer, comment="Дата изм."),
    sqlalchemy.Column(ThumbColumns.RESOL, sqlalchemy.Text, comment="1920x1080"),
    sqlalchemy.Column(ThumbColumns.COLL, sqlalchemy.Text, comment="Имя коллекции"),
    sqlalchemy.Column(ThumbColumns.FAV, sqlalchemy.Integer, comment="1 is fav else 0"),
    sqlalchemy.Column(ThumbColumns.BRAND, sqlalchemy.Text, comment="miuz, panacea"),
)

DIRS = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column(ThumbColumns.ID, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ThumbColumns.SHORT_SRC, sqlalchemy.Text),
    sqlalchemy.Column(ThumbColumns.MOD, sqlalchemy.Integer),
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
        else:
            t = "Нет пользовательского файла DB_FILE"
            raise Exception(t)
        
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
