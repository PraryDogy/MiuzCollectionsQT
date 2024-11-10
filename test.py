import os

import sqlalchemy

from cfg import JsonData
from database import THUMBS, Dbase


def new_table():
    METADATA = sqlalchemy.MetaData()

    return sqlalchemy.Table(
        "thumbs", METADATA,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column("img", sqlalchemy.LargeBinary),
        sqlalchemy.Column("src", sqlalchemy.Text, unique=True),
        sqlalchemy.Column("size", sqlalchemy.Integer, comment="Размер"),
        sqlalchemy.Column("created", sqlalchemy.Integer, comment="Дата созд."),
        sqlalchemy.Column("mod", sqlalchemy.Integer, comment="Дата изм."),
        sqlalchemy.Column("coll", sqlalchemy.Text, comment="Коллекция"),
        )


def convert_old_db():
    JsonData.init()
    Dbase.init()
    conn = Dbase.engine.connect()


