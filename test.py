from database import Dbase, ThumbsMd
import sqlalchemy


src = "/Volumes/Shares-1/Collections/0 Other/1 IMG/2020-02-12 20-44-30 (B,Radius4,Smoothing1).jpg"
Dbase.create_engine()
conn =  Dbase.engine.connect()

q = sqlalchemy.update(ThumbsMd).where(ThumbsMd.src == src)
q = q.values(
    {
        "img150": b"",
        "src": src,
        "size": 0,
        "created": 0,
        "modified": 0,
        "collection": "test"
    }
)
conn.execute(q)
conn.commit()