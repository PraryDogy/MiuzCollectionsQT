import os

import sqlalchemy

from cfg import JsonData
from database import THUMBS, Dbase

# JsonData.init()
# Dbase.init()

# src = "/Users/Morkowik/Desktop/Evgeny/sample images/small_images/image-licorice.jpg"

# conn = Dbase.engine.connect()
# q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.src)
# res: list[tuple[int, str]] = conn.execute(q).fetchall()

# for id, src in res:
#     new_src = src.replace(JsonData.coll_folder, "")
#     q = sqlalchemy.update(THUMBS).values(src=new_src).where(THUMBS.c.id == id)
#     conn.execute(q)
# conn.commit()


src = "/Users/Morkowik/Desktop/Evgeny/sample images/big_images/2022-04-20 13-32-22.jpg"

from utils.main_utils import ImageUtils

img = ImageUtils.read_image(src)