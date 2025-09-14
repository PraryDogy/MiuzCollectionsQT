from system.database import Dbase, THUMBS
import sqlalchemy


Dbase.init()
q = sqlalchemy.select(THUMBS.c.short_src)
q = q.where()