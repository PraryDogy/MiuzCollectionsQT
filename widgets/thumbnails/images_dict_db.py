from collections import defaultdict
from datetime import datetime
from typing import Literal

import sqlalchemy

from cfg import cnf
from database import Dbase, ThumbsMd


class ImagesDictDb(dict):
    def __init__(self) -> dict:
        """
        dict:
            key: "date start - date fin / month year"
            value: [ {"img": img byte_array, "src": img_src, "coll": coll}, ... ]
        """
        super().__init__()
        self.thumbsdict_create()

    def thumbsdict_create(self):
        q = self.create_query()

        session = Dbase.get_session()
        try:
            data = session.execute(q).fetchall()
        finally:
            session.close()

        thumbs_dict = defaultdict(list)

        for img, src, modified, coll in data:
            modified = datetime.fromtimestamp(modified).date()

            if cnf.date_start or cnf.date_end:
                modified = f"{cnf.date_start_text} - {cnf.date_end_text}"
            else:
                modified = f"{cnf.lng.months[str(modified.month)]} {modified.year}"

            thumbs_dict[modified].append({"img": img, "src": src, "coll": coll})

        self.update(thumbs_dict)

    def stamp_dates(self) -> tuple[datetime, datetime]:
        start = datetime.combine(cnf.date_start, datetime.min.time())
        end = datetime.combine(cnf.date_end, datetime.max.time().replace(microsecond=0))
        return datetime.timestamp(start), datetime.timestamp(end)

    def create_query(self):
        q = sqlalchemy.select(
            ThumbsMd.img150,
            ThumbsMd.src,
            ThumbsMd.modified,
            ThumbsMd.collection
            )

        if cnf.search_widget_text:
            search = cnf.search_widget_text.replace("\n", "").strip()
            q = q.filter(ThumbsMd.src.like(f"%{search}%"))

        if cnf.curr_coll != cnf.ALL_COLLS:
            q = q.filter(ThumbsMd.collection == cnf.curr_coll)

        filters = [
            ThumbsMd.src.like(f"%/{true_name}/%") 
            for code_name, true_name in cnf.cust_fltr_names.items()
            if cnf.cust_fltr_vals[code_name]
        ]

        other_filter = [
            ThumbsMd.src.not_like(f"%/{true_name}/%") 
            for code_name, true_name in cnf.cust_fltr_names.items() 
            if cnf.sys_fltr_vals["other"]
            ]

        if all((filters, other_filter)):
            filters = sqlalchemy.or_(*filters)
            other_filter = sqlalchemy.and_(*other_filter)
            q = q.filter(sqlalchemy.or_(filters, other_filter))
        elif filters:
            q = q.filter(sqlalchemy.or_(*filters))
        elif other_filter:
            q = q.filter(sqlalchemy.and_(*other_filter))

        if any((cnf.date_start, cnf.date_end)):
            t = self.stamp_dates()
            q = q.filter(ThumbsMd.modified > t[0])
            q = q.filter(ThumbsMd.modified < t[1])

        q = q.limit(cnf.current_photo_limit)
        q = q.order_by(-ThumbsMd.modified)
        return q
