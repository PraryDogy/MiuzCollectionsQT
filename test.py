import os

import sqlalchemy

from cfg import DB_FILE, JsonData
from database import THUMBS, Dbase
from utils.main_utils import ImageUtils, MainUtils

METADATA = sqlalchemy.MetaData()    


class Data_:
    data = []


def new_thumbs():
    return sqlalchemy.Table(
        "thumbs", METADATA,
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column("src", sqlalchemy.Text, unique=True),
        sqlalchemy.Column("hash_path", sqlalchemy.Text),
        sqlalchemy.Column("size", sqlalchemy.Integer, comment="Размер"),
        sqlalchemy.Column("created", sqlalchemy.Integer, comment="Дата созд."),
        sqlalchemy.Column("mod", sqlalchemy.Integer, comment="Дата изм."),
        sqlalchemy.Column("coll", sqlalchemy.Text, comment="Коллекция"),
        )


def images_to_data():
    JsonData.init()
    Dbase.create_engine()
    conn = Dbase.engine.connect()

    q = sqlalchemy.select(THUMBS)
    res = conn.execute(q).fetchall()
    conn.close()

    for id_, bytes_img, src, size, created, mod, coll in res:
        
        image_array = ImageUtils.bytes_to_image_array(bytes_img)
        hash_path = MainUtils.get_hash_path(src)

        new_data = (src, hash_path, size, created, mod, coll)
        Data_.data.append(new_data)

        MainUtils.write_image_hash(hash_path, image_array)


def create_new_db():
    os.remove(DB_FILE)
    Dbase.create_engine()
    new_thumbs_ = new_thumbs()
    METADATA.create_all(bind=Dbase.engine)

    conn = Dbase.engine.connect()
    
    for src, hash_path, size, created, mod, coll in Data_.data:
        values_ = {
            "src": src,
            "hash_path": hash_path,
            "size": size,
            "created": created,
            "mod": mod,
            "coll": coll
            }
        
        q = sqlalchemy.insert(THUMBS).values(**values_)
        conn.execute(q)

    conn.commit()
    conn.close()


# images_to_data()
# create_new_db()