import os

import sqlalchemy

from cfg import JsonData, Static

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

        tables = [THUMBS]
        check_tables = cls.check_tables(tables)

        if not check_tables:

            JsonData.copy_db_file()
            JsonData.copy_hashdir()

            t = "пользовательская ДБ не прошла проверку"
            print(t)

            cls.init()
            return

        cls.toggle_wal(False)

        return

        print(
            f"database init",
            f"ehco: {cls._echo}",
            f"check same thread: {cls._same_thread}",
            f"timeout: {cls._timeout}",
            f"wal: {cls.WAL_}",
            sep=", "
            )

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
