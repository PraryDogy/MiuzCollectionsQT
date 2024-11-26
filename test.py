from database import Dbase, THUMBS
import sqlalchemy
from cfg import JsonData


JsonData.init()
Dbase.init()

conn = Dbase.engine.connect()

q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.hash_path)
res = conn.execute(q).fetchall()

for id_, hash_path in res:
    values_ = {
        "id": id_,
        "hash_path": hash_path.replace(
            "/Users/Loshkarev/Library/Application Support/MiuzCollectionsQT",
            "/Users/Loshkarev/Library/Application Support/Collections"
        )
    }

    q = sqlalchemy.update(THUMBS).where(THUMBS.c.id == id_).values(**values_)
    conn.execute(q)

conn.commit()
conn.close()