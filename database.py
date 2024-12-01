import os
import shutil

import sqlalchemy
from PyQt5.QtWidgets import QApplication

from cfg import JsonData, Static
from utils.utils import Utils

METADATA = sqlalchemy.MetaData()

THUMBS = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("short_src", sqlalchemy.Text),
    sqlalchemy.Column("short_hash", sqlalchemy.Text, comment="Путь к маленькой картинке"),
    sqlalchemy.Column("size", sqlalchemy.Integer, comment="Размер"),
    sqlalchemy.Column("birth", sqlalchemy.Integer, comment="Дата созд."),
    sqlalchemy.Column("mod", sqlalchemy.Integer, comment="Дата изм."),
    sqlalchemy.Column("resol", sqlalchemy.TEXT, comment="1920x1080"),
    sqlalchemy.Column("coll", sqlalchemy.Text, comment="Имя коллекции"),
    sqlalchemy.Column("fav", sqlalchemy.Integer, comment="1 is fav else 0"),
    sqlalchemy.Column("brand", sqlalchemy.TEXT, comment="miuz, panacea"),
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
