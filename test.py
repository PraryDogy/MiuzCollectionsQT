from system.database import Dbase, THUMBS
import sqlalchemy


Dbase.init()
conn = Dbase.engine.connect()
q = (
    sqlalchemy.select(THUMBS.c.id)
    .where(
        THUMBS.c.short_src == None,
        THUMBS.c.short_hash == None
    )
)
res = conn.execute(q).fetchall()

print(res)