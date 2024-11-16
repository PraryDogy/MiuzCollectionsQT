from collections import defaultdict
from datetime import datetime

import sqlalchemy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap

from cfg import ALL_COLLS, FAVS, Dynamic, JsonData
from database import THUMBS, Dbase
from utils.utils import URunnable, UThreadPool, Utils


class DbImage:
    __slots__ = ["pixmap", "src", "coll", "fav"]
    def __init__(self, pixmap: QPixmap, src: str, coll: str, fav: int):
        self.pixmap = pixmap
        self.src = src
        self.coll = coll
        self.fav = fav


class WorkerSignals(QObject):
    finished_ = pyqtSignal(list)


class LoadDbTask(URunnable):
    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    def run(self):
        conn = Dbase.engine.connect()
        stmt = self._get_stmt()
        res: list[tuple[str, str, int, str, int]] = conn.execute(stmt).fetchall()        
        conn.close()
        self.signals_.finished_.emit(res)

    def _get_stmt(self) -> sqlalchemy.Select:
        q = sqlalchemy.select(
            THUMBS.c.src,
            THUMBS.c.hash_path,
            THUMBS.c.mod,
            THUMBS.c.coll,
            THUMBS.c.fav
            )

        q = q.limit(Dynamic.current_photo_limit)
        q = q.order_by(-THUMBS.c.mod)

        if JsonData.curr_coll == FAVS:
            q = q.where(THUMBS.c.fav == 1)

        elif JsonData.curr_coll != ALL_COLLS:
            q = q.where(THUMBS.c.coll == JsonData.curr_coll)

        if Dynamic.search_widget_text:
            search = Dynamic.search_widget_text.replace("\n", "").strip()
            q = q.where(THUMBS.c.src.like(f"%{search}%"))

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
            q = q.where(THUMBS.c.mod > t[0])
            q = q.where(THUMBS.c.mod < t[1])

        return q

    def _stamp_dates(self) -> tuple[datetime, datetime]:
        start = datetime.combine(Dynamic.date_start, datetime.min.time())
        end = datetime.combine(Dynamic.date_end, datetime.max.time().replace(microsecond=0))
        return datetime.timestamp(start), datetime.timestamp(end)


class DbImages(QObject):
    finished_ = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def get(self):
        self.create_task()

    def create_task(self):
        self.task_ = LoadDbTask()
        self.task_.signals_.finished_.connect(self.create_dict)
        UThreadPool.pool.start(self.task_)

    def create_dict(
            self,
            res: list[tuple[str, str, int, str, int]]
            ) -> dict[str, list[DbImage]] | dict:

        thumbs_dict = defaultdict(list[DbImage])

        if not res:
            return  {}

        for src, hash_path, mod, coll, fav in res:

            # создаем полный путь из относительного из ДБ
            src = JsonData.coll_folder + src
            mod = datetime.fromtimestamp(mod).date()
            array_img = Utils.read_image_hash(hash_path)

            if array_img is None:
                print("db images > create dict > can't load image")
                return thumbs_dict

            else:
                pixmap = Utils.pixmap_from_array(array_img)

            if Dynamic.date_start or Dynamic.date_end:
                mod = f"{Dynamic.date_start_text} - {Dynamic.date_end_text}"

            else:
                mod = f"{Dynamic.lng.months[str(mod.month)]} {mod.year}"

            thumbs_dict[mod].append(DbImage(pixmap, src, coll, fav))

        self.finished_.emit(thumbs_dict)
