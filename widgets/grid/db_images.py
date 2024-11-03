import os
from collections import defaultdict
from datetime import datetime

import sqlalchemy

from cfg import ALL_COLLS, Dynamic, JsonData
from database import Dbase, THUMBS
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

        thumbs_dict = defaultdict(list[DbImage])

        for img, src, modified, coll in res:

            # создаем полный путь из относительного из ДБ
            src = JsonData.coll_folder + src
            modified = datetime.fromtimestamp(modified).date()

            if Dynamic.date_start or Dynamic.date_end:
                modified = f"{Dynamic.date_start_text} - {Dynamic.date_end_text}"
            else:
                modified = f"{Dynamic.lng.months[str(modified.month)]} {modified.year}"

            thumbs_dict[modified].append(DbImage(img, src, coll))

        return thumbs_dict

    def _stamp_dates(self) -> tuple[datetime, datetime]:
        start = datetime.combine(Dynamic.date_start, datetime.min.time())
        end = datetime.combine(Dynamic.date_end, datetime.max.time().replace(microsecond=0))
        return datetime.timestamp(start), datetime.timestamp(end)

    def _get_stmt(self):
        q = sqlalchemy.select(
            THUMBS.c.img150,
            THUMBS.c.src,
            THUMBS.c.modified,
            THUMBS.c.collection
            )

        if Dynamic.search_widget_text:
            search = Dynamic.search_widget_text.replace("\n", "").strip()
            q = q.where(THUMBS.c.src.like(f"%{search}%"))

        if JsonData.curr_coll != ALL_COLLS:
            q = q.where(THUMBS.c.collection == JsonData.curr_coll)

        filters = [
            THUMBS.c.src.like(f"%/{true_name}/%") 
            for code_name, true_name in JsonData.cust_fltr_names.items()
            if JsonData.cust_fltr_vals[code_name]
        ]

        other_filter = [
            THUMBS.c.src.not_like(f"%/{true_name}/%") 
            for code_name, true_name in JsonData.cust_fltr_names.items() 
            if JsonData.sys_fltr_vals["other"]
            ]

        if all((filters, other_filter)):
            filters = sqlalchemy.or_(*filters)
            other_filter = sqlalchemy.and_(*other_filter)
            q = q.where(sqlalchemy.or_(filters, other_filter))
        elif filters:
            q = q.where(sqlalchemy.or_(*filters))
        elif other_filter:
            q = q.where(sqlalchemy.and_(*other_filter))

        if any((Dynamic.date_start, Dynamic.date_end)):
            t = self._stamp_dates()
            q = q.where(THUMBS.c.modified > t[0])
            q = q.where(THUMBS.c.modified < t[1])

        q = q.limit(Dynamic.current_photo_limit)
        q = q.order_by(-THUMBS.c.modified)
        return q
