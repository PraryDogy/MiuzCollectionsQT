import sqlalchemy

from cfg import DB_FILE, JsonData

METADATA = sqlalchemy.MetaData()

THUMBS = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("src", sqlalchemy.Text, unique=True),
    sqlalchemy.Column("hash_path", sqlalchemy.Text, comment="Путь к маленькой картинке"),
    sqlalchemy.Column("size", sqlalchemy.Integer, comment="Размер"),
    sqlalchemy.Column("birth", sqlalchemy.Integer, comment="Дата созд."),
    sqlalchemy.Column("mod", sqlalchemy.Integer, comment="Дата изм."),
    sqlalchemy.Column("resol", sqlalchemy.TEXT, comment="1920x1080"),
    sqlalchemy.Column("coll", sqlalchemy.Text, comment="Имя коллекции"),
    )


class Dbase:
    engine: sqlalchemy.Engine = None
    _timeout = 15
    _echo = False
    _same_thread = False

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        cls.create_engine()

        tables = [THUMBS]
        check_tables = cls.check_tables(tables)

        if not check_tables:
            JsonData.copy_db_file()
            JsonData.copy_hashdir()
            cls.init()
            return

        # cls.enable_wal()
        cls.disable_wal()

    @classmethod
    def create_engine(cls):
        cls.engine = sqlalchemy.create_engine(
            f"sqlite:///{DB_FILE}",
            echo=cls._echo,
            connect_args={
                "check_same_thread": cls._same_thread,
                "timeout": cls._timeout
                }
                )
        
        print(
            f"database",
            f"ehco: {cls._echo}",
            f"check same thread: {cls._same_thread}",
            f"timeout: {cls._timeout}",
            sep="\n"
            )

    @classmethod
    def enable_wal(cls):
        with cls.engine.connect() as conn:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
        print("wal enabled")

    @classmethod
    def disable_wal(cls):
        with cls.engine.connect() as conn:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=DELETE"))
        print("wal disabled")

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
