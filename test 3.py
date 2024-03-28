import sqlalchemy
from database import Dbase, ThumbsMd
from collections import defaultdict


class DubFinder:
    def __init__(self):
        q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
        conn = Dbase.get_session()
        res = conn.execute(q).fetchall()

        dubs = defaultdict(list)

        for res_id, res_src in res:
            dubs[res_src].append(res_id)

        dubs = [
            x
            for k, v in dubs.items()
            for x in v[1:]
            if len(v) > 1
            ]

        if dubs:
            values = [
                sqlalchemy.delete(ThumbsMd).filter(ThumbsMd.id==dub_id)
                for dub_id in dubs
                ]

            for i in values:
                conn.execute(i)

            conn.commit()
            conn.close()
            