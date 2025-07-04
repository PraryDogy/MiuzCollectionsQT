from system.database import THUMBS, Dbase
import sqlalchemy
from system.utils import MainUtils

Dbase.create_engine()
conn = Dbase.engine.connect()


src = '/0 Other/1 IMG'

q = sqlalchemy.select(THUMBS.c.short_src)
q = q.where(THUMBS.c.short_src.ilike(f"{src}/%"))
q = q.where(THUMBS.c.short_src.not_ilike(f"{src}/%/%"))

res = conn.execute(q).scalars()

for i in res:
    if "коробки" in i:
        print(i)