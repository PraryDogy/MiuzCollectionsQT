import os

import sqlalchemy

from system.database import THUMBS, Dbase, DIRS
from system.utils import ImgUtils, MainUtils, ThumbUtils

# src = '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/0 Other/1 IMG/2025-09-08 15-47-41 (B,R1,S1).psd'
# ImgUtils.read_image(src)

Dbase.init()
conn = Dbase.engine.connect()
stmt = sqlalchemy.select(THUMBS.c.short_src, THUMBS.c.short_hash)
for rel_img_path, rel_thumb_path in conn.execute(stmt):
    abs_thumb_path = ThumbUtils.get_abs_thumb_path(rel_thumb_path)
    if not os.path.exists(abs_thumb_path):
        stmt = sqlalchemy.delete(DIRS).where(
            DIRS.c.short_src == os.path.dirname(rel_img_path)
        )
        conn.execute(stmt)
        stmt = sqlalchemy.delete(THUMBS).where(
            THUMBS.c.short_src == rel_img_path
        )
        conn.execute(stmt)
conn.commit()
conn.close()