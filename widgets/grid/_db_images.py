import os
from collections import defaultdict
from datetime import datetime

import sqlalchemy
from numpy import ndarray
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap

from cfg import Dynamic, Static
from database import THUMBS, Dbase
from filters import Filter
from lang import Lang
from main_folder import MainFolder
from utils.tasks import URunnable
from utils.main import Utils


class DbImage:
    __slots__ = ["pixmap", "rel_img_path", "coll_name", "fav"]
    def __init__(self, pixmap: QPixmap, rel_img_path: str, coll: str, fav: int):
        self.pixmap = pixmap
        self.rel_img_path = rel_img_path
        self.coll_name = coll
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

    def task(self):

        conn = Dbase.engine.connect()
        stmt = self.get_stmt()
        res: list[tuple[str, str, int, str, int]] = conn.execute(stmt).fetchall()        
        conn.close()

        self.create_dict(res)

    def create_dict(
            self,
            res: list[tuple[str, str, int, str, int]]
            ) -> dict[str, list[DbImage]] | dict:

        thumbs_dict = defaultdict(list[DbImage])

        if len(Dynamic.types) == 1:
            exts_ = Dynamic.types[0]
        else:
            exts_ = Static.ext_all

        if not res:
            self.signals_.finished_.emit(thumbs_dict)
            return

        for rel_img_path, rel_thumb_path, mod, coll, fav in res:

            if not rel_img_path.endswith(exts_):
                continue

            mod = datetime.fromtimestamp(mod).date()
            thumb_path = Utils.get_thumb_path(rel_thumb_path)
            thumb = Utils.read_thumb(thumb_path)

            if isinstance(thumb, ndarray):
                pixmap = Utils.pixmap_from_array(thumb)
            else:
                continue

            if Dynamic.date_start or Dynamic.date_end:
                mod = f"{Dynamic.f_date_start} - {Dynamic.f_date_end}"

            else:
                mod = f"{Lang.months[str(mod.month)]} {mod.year}"

            thumbs_dict[mod].append(DbImage(pixmap, rel_img_path, coll, fav))

        try:
            self.signals_.finished_.emit(thumbs_dict)
        except RuntimeError:
            ...

    def get_stmt(self) -> sqlalchemy.Select:
        q = sqlalchemy.select(
            THUMBS.c.short_src, # rel img path
            THUMBS.c.short_hash, # rel thumb path
            THUMBS.c.mod,
            THUMBS.c.coll,
            THUMBS.c.fav
            )
        
        q = q.limit(Static.GRID_LIMIT).offset(Dynamic.grid_offset)
        q = q.where(THUMBS.c.brand == MainFolder.current.name)

        if Dynamic.resents:
            q = q.order_by(-THUMBS.c.id)
        else:
            q = q.order_by(-THUMBS.c.mod)

        stmt_where: list = []

        if Dynamic.search_widget_text:
            text = Dynamic.search_widget_text.strip().replace("\n", "")
            stmt_where.append(THUMBS.c.short_src.ilike(f"%{text}%"))

            for i in stmt_where:
                q = q.where(i)
                return q

        if Dynamic.curr_coll_name == Static.NAME_FAVS:
            stmt_where.append(THUMBS.c.fav == 1)

        elif Dynamic.curr_coll_name != Static.NAME_ALL_COLLS:
            stmt_where.append(THUMBS.c.coll == Dynamic.curr_coll_name)

        if any((Dynamic.date_start, Dynamic.date_end)):
            t = self.combine_dates()
            stmt_where.append(THUMBS.c.mod > t[0])
            stmt_where.append(THUMBS.c.mod < t[1])

        user_filters, sys_filters = self.group_filters()
    
        or_statements = sqlalchemy.or_(
            *self.build_inclusion_condition(user_filters),
            self.build_exclusion_condition(user_filters, sys_filters)
        )

        stmt_where.append(or_statements)

        for i in stmt_where:
            q = q.where(i)

        return q
    
    def build_exclusion_condition(
            self,
            user_filters: list[Filter],
            sys_filters: list[Filter]
        ) -> sqlalchemy.ColumnElement:
        """
        Формирует SQLAlchemy условие для исключения строк, которые соответствуют
        пользовательским фильтрам, если системный фильтр включён.

        Условия строятся так:
        - Для каждого активного системного фильтра (sys_filter.value == True) создаётся
        группа условий, исключающих строки, соответствующие пользовательским фильтрам.
        - Условия объединяются с помощью OR для всех активных системных фильтров.
        - Внутри каждой группы пользовательские фильтры объединяются с помощью AND.

        Args:
            user_filters (list[Filter]): Список пользовательских фильтров (не системных).
            sys_filters (list[Filter]): Список системных фильтров.

        Returns:
            sqlalchemy.sql.elements.BooleanClauseList:
                Условие для исключения строк, соответствующих пересечению системных
                и пользовательских фильтров.
        """
        conditions = [
            THUMBS.c.short_src.not_ilike(f"%{os.sep}{user_filter.real}{os.sep}%")
            for sys_filter in sys_filters
            for user_filter in user_filters
            if sys_filter.value
        ]
        return sqlalchemy.and_(*conditions)

    def build_inclusion_condition(
            self,
            user_filters: list[Filter]
        ) -> list[sqlalchemy.BinaryExpression[bool]]:
        """
        Формирует SQLAlchemy условие для включения строк, соответствующих
        значениям пользовательских фильтров.

        Условия строятся так:
        - Для каждого активного пользовательского фильтра (filter.value == True)
        создаётся выражение, проверяющее, что `src` содержит значение `filter.real`.
        - Все условия объединяются с помощью OR.

        Args:
            user_filters (list[Filter]): Список пользовательских фильтров.

        Returns:
            sqlalchemy.sql.elements.BooleanClauseList:
                Условие для включения строк, соответствующих хотя бы одному
                из пользовательских фильтров.
        """
        conditions = [
            THUMBS.c.short_src.ilike(f"%{os.sep}{filter.real}{os.sep}%")
            for filter in user_filters
            if filter.value
        ]
        return conditions

    def group_filters(self) -> tuple[list[Filter], list[Filter]]:
        """
        Разделяет фильтры на пользовательские и системные.

        Фильтры классифицируются на основе значения их атрибута `.system`:
        - Если `.system == True`, фильтр добавляется в список системных
        фильтров (`sys_filters`).
        - Если `.system == False`, фильтр добавляется в список пользовательских
        фильтров (`user_filters`).

        Returns:
            tuple[list[Filter], list[Filter]]:
                - user_filters: Список пользовательских фильтров.
                - sys_filters: Список системных фильтров.
        """
        user_filters: list[Filter] = []
        sys_filters: list[Filter] = []

        for i in Filter.filters_list:
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
