import os
import shutil

import sqlalchemy

from cfg import DB_FILE

METADATA = sqlalchemy.MetaData()

THUMBS = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("src", sqlalchemy.Text, unique=True),
    sqlalchemy.Column("hash_path", sqlalchemy.Text),
    sqlalchemy.Column("size", sqlalchemy.Integer, comment="Размер"),
    sqlalchemy.Column("created", sqlalchemy.Integer, comment="Дата созд."),
    sqlalchemy.Column("mod", sqlalchemy.Integer, comment="Дата изм."),
    sqlalchemy.Column("coll", sqlalchemy.Text, comment="Коллекция"),
    )


class Dbase:
    engine: sqlalchemy.Engine = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        cls.create_engine()

        tables = [THUMBS]
        check_tables = cls.check_tables(tables)

        if not check_tables:
            cls.copy_db_file()
            cls.create_engine()

        cls.enable_wal()

    @classmethod
    def create_engine(cls):
        cls.engine = sqlalchemy.create_engine(
            f"sqlite:///{DB_FILE}",
            echo=False,
            connect_args={
                "check_same_thread": False,
                "timeout": 15
                }
                )

    @classmethod
    def enable_wal(cls):
        with cls.engine.connect() as conn:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
        print("database > wal enabled")

    @classmethod
    def vacuum(cls):
        conn = cls.engine.connect()
        conn.execute(sqlalchemy.text("VACUUM"))
        conn.commit()

    @classmethod
    def check_tables(cls, tables: list):
        inspector = sqlalchemy.inspect(cls.engine)

        db_tables = inspector.get_table_names()
        res: bool = (list(i.name for i in tables) == db_tables)

        if not res:
            print("Несоответствие в имени таблицы и/или в количестве таблиц")
            return False

        for table in tables:
            clmns = list(clmn.name for clmn in table.columns)
            db_clmns = list(clmn.get("name") for clmn in inspector.get_columns(table.name))
            res = bool(db_clmns == clmns)

            if not res:
                print(f"Несоответствие имени столбца в {table.name}")
                return False
            
        return True

    @classmethod
    def copy_db_file(cls):
        print("Копирую новую предустановленную БД")
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

        shutil.copyfile(src="db.db", dst=DB_FILE)