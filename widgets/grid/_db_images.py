import os
from collections import defaultdict
from datetime import datetime

import sqlalchemy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap

from cfg import (GRID_LIMIT, NAME_ALL_COLLS, NAME_FAVS, Dynamic, Filter,
                 JsonData)
from database import THUMBS, Dbase
from lang import Lang
from utils.utils import URunnable, Utils


class DbImage:
    __slots__ = ["pixmap", "short_src", "coll", "fav"]
    def __init__(self, pixmap: QPixmap, short_src: str, coll: str, fav: int):
        self.pixmap = pixmap
        self.short_src = short_src
        self.coll = coll
        self.fav = fav


class WorkerSignals(QObject):
    finished_ = pyqtSignal(dict)


class DbImages(URunnable):
    def __init__(self):
        """
        returns
        ```
        {1 june 2024: [DbImage, ...], ...}
        {1 june 2024 - 1 august 2024: [DbImage, ...], ...}
        ```
        """
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):

        conn = Dbase.engine.connect()
        stmt = self._get_stmt()
        res: list[tuple[str, str, int, str, int]] = conn.execute(stmt).fetchall()        
        conn.close()

        self.create_dict(res)

    def create_dict(
            self,
            res: list[tuple[str, str, int, str, int]]
            ) -> dict[str, list[DbImage]] | dict:
        
        res = res[-(GRID_LIMIT):]

        thumbs_dict = defaultdict(list[DbImage])

        if not res:
            self.signals_.finished_.emit(thumbs_dict)
            return

        for short_src, hash_path, mod, coll, fav in res:

            mod = datetime.fromtimestamp(mod).date()
            array_img = Utils.read_image_hash(hash_path)

            if array_img is None:
                print("db images > create dict > can't load image")
                self.signals_.finished_.emit(thumbs_dict)
                return

            else:
                pixmap = Utils.pixmap_from_array(array_img)

            if Dynamic.date_start or Dynamic.date_end:
                mod = f"{Dynamic.date_start_text} - {Dynamic.date_end_text}"

            else:
                mod = f"{Lang.months[str(mod.month)]} {mod.year}"

            thumbs_dict[mod].append(DbImage(pixmap, short_src, coll, fav))

        self.signals_.finished_.emit(thumbs_dict)

    def _get_stmt(self) -> sqlalchemy.Select:
        q = sqlalchemy.select(
            THUMBS.c.src,
            THUMBS.c.hash_path,
            THUMBS.c.mod,
            THUMBS.c.coll,
            THUMBS.c.fav
            )
        
        q = q.limit(GRID_LIMIT).offset(Dynamic.grid_offset)
        q = q.order_by(-THUMBS.c.mod)

        stmt_where: list = []

        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt_where.append(THUMBS.c.src.ilike(f"%{text}%"))

            for i in stmt_where:
                q = q.where(i)
                return q

        if JsonData.curr_coll == NAME_FAVS:
            stmt_where.append(THUMBS.c.fav == 1)

        elif JsonData.curr_coll != NAME_ALL_COLLS:
            stmt_where.append(THUMBS.c.coll == JsonData.curr_coll)

        if any((Dynamic.date_start, Dynamic.date_end)):
            t = self.combine_dates()
            stmt_where.append(THUMBS.c.mod > t[0])
            stmt_where.append(THUMBS.c.mod < t[1])

        user_filters, sys_filters = self.group_filters()
        stmt_where.append(self.user_filter_or(user_filters))
        stmt_where.append(self.sys_filter_or(user_filters, sys_filters))

        for i in stmt_where:
            q = q.where(i)

        return q
    
    def sys_filter_or(self, user_filters: list[Filter], sys_filters: list[Filter]):
        conditions = [
            THUMBS.c.src.not_ilike(f"%{os.sep}{user_filter.real}{os.sep}%")
            for sys_filter in sys_filters
            for user_filter in user_filters
            if sys_filter.value
        ]
        return sqlalchemy.or_(sqlalchemy.and_(*conditions))

    def user_filter_or(self, user_filters: list[Filter]):
        conditions = [
            THUMBS.c.src.ilike(f"%{os.sep}{filter.real}{os.sep}%")
            for filter in user_filters
            if filter.value
        ]
        return sqlalchemy.or_(*conditions)

    def group_filters(self) -> tuple[list[Filter], list[Filter]]:
        user_filters: list[Filter] = []
        sys_filters: list[Filter] = []

        for i in Filter.filters:
            if i.system:
                sys_filters.append(i)
            else:
                user_filters.append(i)
        return user_filters, sys_filters

    def combine_dates(self) -> tuple[datetime, datetime]:
        start = datetime.combine(
            Dynamic.date_start,
            datetime.min.time()
            )

        end = datetime.combine(
            Dynamic.date_end,
            datetime.max.time().replace(microsecond=0)
            )

        return datetime.timestamp(start), datetime.timestamp(end)
