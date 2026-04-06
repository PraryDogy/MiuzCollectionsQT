import os
import traceback
from typing import Literal

import sqlalchemy
from sqlalchemy.exc import IntegrityError, OperationalError

from cfg import Static
from system.utils import Utils

METADATA = sqlalchemy.MetaData()


class ClmnNames:
    id: Literal["id"] = "id"
    rel_item_path: Literal["наст. имя: short_src"] = "short_src"
    rel_thumb_path: Literal["наст. имя: short_hash"] = "short_hash"
    size: Literal["size"] = "size"
    birth: Literal["birth: упразднено, неверно отобр. на smb дисках"] = "birth"
    mod: Literal["mod"] = "mod"
    root: Literal["наст. имя: resol, теперь это dirname"] = "resol"
    coll: Literal["coll: упразднено"] = "coll"
    fav: Literal["fav"] = "fav"
    mf_alias: Literal["наст. имя: brand"] = "brand"


_table_thumbs = sqlalchemy.Table(
    "thumbs", METADATA,
    sqlalchemy.Column(ClmnNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmnNames.rel_item_path, sqlalchemy.Text),
    sqlalchemy.Column(ClmnNames.rel_thumb_path, sqlalchemy.Text),
    sqlalchemy.Column(ClmnNames.size, sqlalchemy.Integer),
    sqlalchemy.Column(ClmnNames.birth, sqlalchemy.Integer),
    sqlalchemy.Column(ClmnNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ClmnNames.root, sqlalchemy.Text),
    sqlalchemy.Column(ClmnNames.coll, sqlalchemy.Text),
    sqlalchemy.Column(ClmnNames.fav, sqlalchemy.Integer),
    sqlalchemy.Column(ClmnNames.mf_alias, sqlalchemy.Text),
)


_table_dirs = sqlalchemy.Table(
    "dirs", METADATA,
    sqlalchemy.Column(ClmnNames.id, sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(ClmnNames.rel_item_path, sqlalchemy.Text),
    sqlalchemy.Column(ClmnNames.mod, sqlalchemy.Integer),
    sqlalchemy.Column(ClmnNames.mf_alias, sqlalchemy.Text),
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
    root = _table_thumbs.c.resol
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
    main_engine: sqlalchemy.Engine = None
    _timeout = 5
    _echo = False
    _same_thread = False
    WAL_ = None

    @classmethod
    def init(cls) -> sqlalchemy.Engine:
        Dbase.main_engine = cls.create_engine()
        cls.toggle_wal(False)

    @classmethod
    def create_engine(cls):
        if os.path.exists(Static.external_db):
            engine = sqlalchemy.create_engine(
                f"sqlite:///{Static.external_db}",
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
        conn = Dbase.main_engine.connect()
        if value:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
            cls.WAL_ = True
        else:
            conn.execute(sqlalchemy.text("PRAGMA journal_mode=DELETE"))
            cls.WAL_ = False
        conn.close()

    @classmethod
    def vacuum(cls):
        conn = cls.main_engine.connect()

        try:
            conn.execute(sqlalchemy.text("VACUUM"))
            conn.commit()
        except Exception as e:
            Utils.print_error()

        conn.close()

    @classmethod
    def set_root(cls):
        with Dbase.create_engine().begin() as conn:
            stmt = sqlalchemy.select(Thumbs.table)
            values = [
                dict(i)
                for i in conn.execute(stmt).mappings()
            ]
            if not values:
                return
            ok_values = []
            for row in values:
                try:
                    row[ClmnNames.root] = os.path.dirname(
                        row[ClmnNames.rel_item_path]
                    )
                    row.pop(ClmnNames.id)
                    ok_values.append(row)
                except Exception as e:
                    print(traceback.format_exc())
                    continue
            del_table = sqlalchemy.delete(Thumbs.table)
            conn.execute(del_table)
            stmt = sqlalchemy.insert(Thumbs.table)
            if ok_values:
                conn.execute(stmt, ok_values)
                    
    @classmethod
    def set_short_hash_not_unique(cls):
        old_table = "thumbs"
        new_table = "thumbs_new"

        drop_new_sql = f"DROP TABLE IF EXISTS {new_table};"

        create_table_sql = f"""
            CREATE TABLE {new_table} (
                {ClmnNames.id} INTEGER PRIMARY KEY,
                {ClmnNames.rel_item_path} TEXT,
                {ClmnNames.rel_thumb_path} TEXT,
                {ClmnNames.size} INTEGER,
                {ClmnNames.birth} INTEGER,
                {ClmnNames.mod} INTEGER,
                {ClmnNames.root} TEXT,
                {ClmnNames.coll} TEXT,
                {ClmnNames.fav} INTEGER,
                {ClmnNames.mf_alias} TEXT
            );
        """
        copy_data_sql = f"""
            INSERT OR IGNORE INTO {new_table}
            SELECT * FROM {old_table};
        """

        drop_old_sql = f"""
            DROP TABLE {old_table};
        """

        rename_sql = f"""
            ALTER TABLE {new_table} RENAME TO {old_table};
        """

        engine = cls.create_engine()

        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(drop_new_sql))
            conn.execute(sqlalchemy.text(create_table_sql))
            conn.execute(sqlalchemy.text(copy_data_sql))
            conn.execute(sqlalchemy.text(drop_old_sql))
            conn.execute(sqlalchemy.text(rename_sql))