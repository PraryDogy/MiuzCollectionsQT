import os

import sqlalchemy
import json
from cfg import DB_FILE, JsonData, APP_SUPPORT_DIR
from database import THUMBS, Dbase
from utils.main_utils import ImageUtils, MainUtils


# class Data_:
#     data = []


# def images_to_data():
#     JsonData.init()
#     Dbase.create_engine()
#     conn = Dbase.engine.connect()

#     q = sqlalchemy.select(THUMBS)
#     res = conn.execute(q).fetchall()
#     conn.close()

#     for id_, bytes_img, src, size, created, mod, coll in res:
        
#         image_array = ImageUtils.bytes_to_image_array(bytes_img)
#         hash_path = MainUtils.get_hash_path(src)

#         new_data = (src, hash_path, size, created, mod, coll)
#         Data_.data.append(new_data)

#         MainUtils.write_image_hash(hash_path, image_array)

#     return new_data


# images_to_data()
# with open(os.path.join(APP_SUPPORT_DIR, "data.json"), "r") as file:
#     new_data = json.load(file)


# METADATA = sqlalchemy.MetaData()

# THUMBS = sqlalchemy.Table(
#     "thumbs", METADATA,
#     sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
#     sqlalchemy.Column("src", sqlalchemy.Text, unique=True),
#     sqlalchemy.Column("hash_path", sqlalchemy.Text),
#     sqlalchemy.Column("size", sqlalchemy.Integer, comment="Размер"),
#     sqlalchemy.Column("created", sqlalchemy.Integer, comment="Дата созд."),
#     sqlalchemy.Column("mod", sqlalchemy.Integer, comment="Дата изм."),
#     sqlalchemy.Column("coll", sqlalchemy.Text, comment="Коллекция"),
#     )

# Dbase.create_engine()
# conn = Dbase.engine.connect()

# for src, hash_path, size, created, mod, coll in new_data:
#     values ={
#         "src": src,
#         "hash_path": hash_path,
#         "size": size,
#         "created": created,
#         "mod": mod,
#         "coll": coll
#         }
#     q = sqlalchemy.insert(THUMBS).values(**values)
#     conn.execute(q)
# conn.commit()