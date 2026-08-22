import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Queue
from time import sleep

import sqlalchemy
from typing_extensions import Literal

from cfg import Static
from system.database import Dbase, Dirs, Thumbs
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import BaseProcessWorker
from system.shared_utils import ImgUtils
from system.utils import Utils


class NewScanerWorker(BaseProcessWorker):
    def __init__(self, target: callable, args: tuple):
        self.process_queue = Queue()
        self.response_queue = Queue()
        super().__init__(target, (*args, self.process_queue, self.response_queue))


@dataclass(slots=True)
class BaseScanerItem:
    mf: Mf
    engine: sqlalchemy.Engine
    process_queue: Queue
    response_queue: Queue
    lng_index: int
    total_count: int
    current_count: int
    scaner_type: Literal["forced", "base"]


import os
from pathlib import Path

class MfScaner:
    def __init__(self, scaner_item: BaseScanerItem):
        super().__init__()
        self.scaner_item = scaner_item
        # Превращаем в словарь {abs_path: db_mod_time} для быстрого O(1) поиска


        self.non_exist_dirs = []
        self.changed_dirs = []
        self.new_dirs = []

        self.non_exist_images = []
        self.changed_images = []
        self.new_images = []

        self.db_dirs = dict(self.get_db_dirs())
        self.scan_and_sync()

    def get_db_dirs(self):
        stmt = (
            sqlalchemy.select(Dirs.rel_dir_path, Dirs.mod)
            .where(Dirs.mf_alias == self.scaner_item.mf.mf_alias)
        )
        with self.scaner_item.engine.connect() as conn:
            result = conn.execute(stmt)
        mf_path = self.scaner_item.mf.mf_paths[0]
        return [
            (Utils.add_mf_path(mf_path, rel_dir_path), mod)
            for rel_dir_path, mod in result
        ]

    def scan_and_sync(self):
        # records_to_delete = []
        # records_to_insert = []
        
        # Шаг 1: Проверяем существующие в БД директории
        for dir_path, db_mod_time in self.db_dirs.items():
            if not os.path.exists(dir_path):
                # Если папка была удалена физически
                # records_to_delete.append(dir_path)
                self.non_exist_dirs.append(dir_path)
                continue
                
            # Получаем фактическое время из Finder (файловой системы)
            fs_mod_time = int(os.path.getmtime(dir_path))
            
            if fs_mod_time != db_mod_time:
                # Директория изменилась -> пойдет под пересоздание
                self.non_exist_dirs.append(dir_path)
                self.new_dirs.append((dir_path, fs_mod_time))
                
                # Шаг 2: Ищем причину (новые вложенные папки)
                # Так как папка изменилась, сканируем её уровень на наличие подпапок
                self._collect_nested_new_dirs(dir_path)

    def _collect_nested_new_dirs(self, parent_dir: str):
        """Рекурсивно обходит только те папки, которых вообще нет в БД."""
        try:
            iterator = os.scandir(parent_dir)
        except PermissionError:
            return
        return
        for entry in iterator:
            if entry.is_dir():
                child_path = entry.path
                if child_path not in self.db_dirs:
                    fs_mod_time = int(entry.stat().st_mtime)
                    records_to_insert.append((child_path, fs_mod_time))
                    self._collect_nested_new_dirs(child_path, records_to_insert)


class NewScanerProcess:

    @staticmethod
    def start(mf_list: list[Mf], lng_index: int, queue: Queue, response_queue: Queue):
        engine = Dbase.create_engine()
        for i in mf_list:
            scaner_item = BaseScanerItem(
                mf=i,
                engine=engine,
                process_queue=queue,
                response_queue=response_queue,
                lng_index=lng_index,
                total_count=0,
                current_count=0,
                scaner_type="base"
            )
            scaner = MfScaner(scaner_item)
