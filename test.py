from database import Dbase, THUMBS
import sqlalchemy
from cfg import JsonData, APP_SUPPORT_DIR


JsonData.init()
Dbase.init()

conn = Dbase.engine.connect()

q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.short_hash)
res = conn.execute(q).fetchall()

for id_, hash_path in res:
    values_ = {
        "id": id_,
        "short_hash": hash_path.replace(
            APP_SUPPORT_DIR,
            ""
        )
    }

    q = sqlalchemy.update(THUMBS).where(THUMBS.c.id == id_).values(**values_)
    conn.execute(q)

conn.commit()
conn.close()