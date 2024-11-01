import os
from collections import defaultdict
from datetime import datetime

import sqlalchemy

from cfg import cnf
from database import Dbase, ThumbsMd
from utils.main_utils import MainUtils


class DbImage:
    __slots__ = ["img", "src", "coll"]
    def __init__(self, img: bytes, src: str, coll: str):
        self.img = img
        self.src = src
        self.coll = coll


class DbImages:
    def __init__(self):
        super().__init__()

    def get(self) -> dict[str, list[DbImage]]:
        return self._create_dict()

    def _create_dict(self) -> dict[str, list[DbImage]]:
        conn = Dbase.engine.connect()
        stmt = self._get_stmt()

        try:
            res: list[ tuple[bytes, str, int, str] ] = conn.execute(stmt).fetchall()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            conn.close()
            return

        thumbs_dict = defaultdict(lambda: defaultdict(list))

        # for img150, src, modified, coll in res:
        #     modified = datetime.fromtimestamp(modified).strftime("%B %Y")
        #     name, ext = os.path.splitext(src)
        #     thumbs_dict[modified][name].append((img150, coll, ext))

        # thumbs_dict: dict[str, list[DbImage]] = {
        #     date: [
        #         DbImage(img150, name + ext, coll)
        #         for name, exts_list in files_by_name.items()
        #         for img150, coll, ext in sorted(exts_list)
        #         ]
        #     for date, files_by_name in thumbs_dict.items()
        #     }

        thumbs_dict = defaultdict(list[DbImage])

        for img, src, modified, coll in res:
            modified = datetime.fromtimestamp(modified).date()

            if cnf.date_start or cnf.date_end:
                modified = f"{cnf.date_start_text} - {cnf.date_end_text}"
            else:
                modified = f"{cnf.lng.months[str(modified.month)]} {modified.year}"

            thumbs_dict[modified].append(DbImage(img, src, coll))

        return thumbs_dict

    def _stamp_dates(self) -> tuple[datetime, datetime]:
        start = datetime.combine(cnf.date_start, datetime.min.time())
        end = datetime.combine(cnf.date_end, datetime.max.time().replace(microsecond=0))
        return datetime.timestamp(start), datetime.timestamp(end)

    def _get_stmt(self):
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
            t = self._stamp_dates()
            q = q.filter(ThumbsMd.modified > t[0])
            q = q.filter(ThumbsMd.modified < t[1])

        q = q.limit(cnf.current_photo_limit)
        q = q.order_by(-ThumbsMd.modified)
        return q
