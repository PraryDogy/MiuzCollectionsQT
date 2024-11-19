import os
from collections import defaultdict
from datetime import datetime

import sqlalchemy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap

from cfg import GRID_LIMIT, NAME_ALL_COLLS, NAME_FAVS, Dynamic, JsonData
from database import THUMBS, Dbase
from lng import Lng
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
                mod = f"{Lng.months[str(mod.month)]} {mod.year}"

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

        if JsonData.curr_coll == NAME_FAVS:

            q = q.where(
                THUMBS.c.fav == 1
                )

        elif JsonData.curr_coll != NAME_ALL_COLLS:

            q = q.where(
                THUMBS.c.coll == JsonData.curr_coll
                )

        if Dynamic.search_widget_text:

            text = Dynamic.search_widget_text.strip().replace("\n", "")
            q = q.where(
                THUMBS.c.src.ilike(f"%{text}%")
                )

        filter_values_ = set(
            i.get("value")
            for i in (
                *JsonData.custom_filters,
                JsonData.system_filter
                )
            )
        
        # если ВСЕ фильтры включены или выключены, это будет равняться
        # отсутствию фильтрации
        # в ином случае выполняется фильтрация
        if len(filter_values_) > 1:

            and_filters = []

            for filter in JsonData.custom_filters:
                if filter.get("value"):
                    t = self.get_template(filter.get("real"))

                    and_filters.append(
                        THUMBS.c.src.ilike(t)
                        )

            if JsonData.system_filter.get("value"):

                texts = [
                    self.get_template(i.get("real"))
                    for i in JsonData.custom_filters
                    ]
                
                stmts = [
                    THUMBS.c.src.not_ilike(i)
                    for i in texts
                    ]
                
                and_filters.append(
                    sqlalchemy.and_(*stmts)
                    )

            # пример полного запроса: включен product и other фильтры:
            # остальной запрос БД > ГДЕ
            # ИЛИ src содержит product
            # ИЛИ src НЕ содержит product И src НЕ содержит model
            q = q.where(
                sqlalchemy.or_(*and_filters)
                )

        if any((Dynamic.date_start, Dynamic.date_end)):
            t = self.combine_dates()
            q = q.where(THUMBS.c.mod > t[0])
            q = q.where(THUMBS.c.mod < t[1])

        return q
    
    def get_template(self, text: str) -> str:
        return "%" + os.sep + text + os.sep + "%"

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
