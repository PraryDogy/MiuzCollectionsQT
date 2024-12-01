import os
from time import sleep

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from cfg import Static, JsonData
from database import THUMBS, Dbase
from lang import Lang
from signals import SignalsApp

from .utils import URunnable, UThreadPool, Utils


class Brand:
    all_: list["Brand"] = []
    curr: "Brand" = None
    __slots__ = ["name", "ind", "collfolder"]

    def __init__(self, name: str, ind: int, collfolder: str):
        super().__init__()
        self.name = name
        self.ind = ind
        self.collfolder = collfolder


class ScanerTools:
    can_scan: bool = True
    sleep_count: float = 0.1

    @classmethod
    def progressbar_text(cls, text: str):
        try:
            SignalsApp.all_.progressbar_text.emit(text)
        except RuntimeError as e:
            pass
            # Utils.print_err(error=e)

    @classmethod
    def reload_gui(cls):
        if cls.can_scan:
            try:
                SignalsApp.all_.menu_left_cmd.emit("reload")
                SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
            except RuntimeError as e:
                Utils.print_err(error=e)


import os
from typing import List, Tuple

class FinderImages:
    def __init__(self):
        super().__init__()

    def get(self) -> List[Tuple[str, int, int, int]]:
        """Основной метод для поиска изображений в коллекциях."""
        collections = self.get_collections()
        finder_images = self.process_collections(collections)
        return finder_images

    def get_collections(self) -> List[str]:
        """Получает список коллекций, исключая остановленные."""
        collections = []

        for item in os.listdir(Brand.curr.collfolder):

            coll_path = os.path.join(Brand.curr.collfolder, item)

            if os.path.isdir(coll_path):

                if item not in JsonData.stopcolls[Brand.curr.ind]:
                    collections.append(coll_path)

        return collections

    def process_collections(self, collections: List[str]) -> List[Tuple[str, int, int, int]]:
        """Обрабатывает список коллекций и находит изображения."""
        finder_images = []
        total_collections = len(collections)

        for index, collection in enumerate(collections, start=1):

            progress_text = self.get_progress_text(index, total_collections)
            ScanerTools.progressbar_text(progress_text)

            try:
                walked_images = self.walk_collection(collection)
                finder_images.extend(walked_images)

            except TypeError as e:
                Utils.print_err(error=e)

        return finder_images

    def get_progress_text(self, current: int, total: int) -> str:
        """Формирует текст для прогресс-бара."""
        brand = Brand.curr.name.capitalize()
        collection_name = Lang.collection
        return f"{brand}: {collection_name.lower()} {current} {Lang.from_} {total}"

    def walk_collection(self, collection: str) -> List[Tuple[str, int, int, int]]:
        """Рекурсивно обходит директорию и находит изображения."""
        finder_images = []
        stack = [collection]

        while stack:
            current_dir = stack.pop()

            with os.scandir(current_dir) as entries:
                for entry in entries:
                    if not ScanerTools.can_scan:
                        return finder_images

                    if entry.is_dir():
                        stack.append(entry.path)
                    elif entry.name.endswith(Static.IMG_EXT):
                        finder_images.append(self.get_file_data(entry))

        return finder_images

    def get_file_data(self, entry: os.DirEntry) -> Tuple[str, int, int, int]:
        """Получает данные файла."""
        stats = entry.stat()
        return (
            entry.path,
            stats.st_size,
            stats.st_birthtime,
            stats.st_mtime,
        )


class DbImages:
    def __init__(self):
        super().__init__()
        t = f"{Brand.curr.name.capitalize()}: {Lang.preparing}"
        ScanerTools.progressbar_text(t)

    def get(self) -> dict[str, tuple[str, int, int, int]]:
        conn = Dbase.engine.connect()

        q = sqlalchemy.select(
            THUMBS.c.short_hash,
            THUMBS.c.short_src,
            THUMBS.c.size,
            THUMBS.c.birth,
            THUMBS.c.mod
            )
        
        q = q.where(THUMBS.c.brand == Brand.curr.name)

        # не забываем относительный путь ДБ преобразовать в полный
        res = conn.execute(q).fetchall()
        conn.close()

        return {
            short_hash_path: (
                Utils.get_full_src(Brand.curr.collfolder, short_src),
                size,
                birth,
                mod
            )
            for short_hash_path, short_src, size, birth, mod in res
            }


class Compator:
    def __init__(
            self,
            finder_images: list[tuple[str, int, int, int]],
            db_images: dict[str, tuple[str, int, int, int]]
            ):

        super().__init__()
        self._finder_images = finder_images
        self._db_images = db_images

        self.del_items: list[str] = []
        self.ins_items: list[tuple[str, int, int, int]] = []

    def get_result(self):
        for short_hash_path, db_item in self._db_images.items():

            if not db_item in self._finder_images:
                self.del_items.append(short_hash_path)

        _db_images = list(self._db_images.values())

        for finder_item in self._finder_images:

            if not finder_item in _db_images:
                self.ins_items.append(finder_item)


class DbUpdater:
    def __init__(
            self,
            del_items: list[str],
            ins_items: list[tuple[str, int, int, int]]
            ):

        super().__init__()
        self.del_items = del_items
        self.ins_items = ins_items

        self.insert_queries: list[sqlalchemy.Insert] = []
        self.hash_images: list[tuple[str, ndarray]] = []

    def run(self):
        self.del_db()
        self.insert_db()
        self.insert_cmd()

    def del_db(self):
        conn = Dbase.engine.connect()
        ln_ = len(self.del_items)

        for x, short_hash_path in enumerate(self.del_items, start=1):
            q = sqlalchemy.delete(THUMBS)
            q = q.where(THUMBS.c.short_hash==short_hash_path)

            try:
                conn.execute(q)

            except sqlalchemy.exc.IntegrityError as e:
                Utils.print_err(error=e)
                conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                Utils.print_err(error=e)
                conn.rollback()
                conn.close()
                return None

        conn.commit()
        conn.close()

        for short_hash_path in self.del_items:

            full_hash_path = Utils.get_full_hash_path(short_hash_path)

            if os.path.exists(full_hash_path):

                brand = Brand.curr.name.capitalize()
                deleting: str = Lang.deleting
                t = f"{brand}: {deleting.lower()} {x} {Lang.from_} {ln_}"
                ScanerTools.progressbar_text(t)

                os.remove(full_hash_path)
                sleep(ScanerTools.sleep_count)


        if self.del_items:
            ScanerTools.reload_gui()

    def get_small_img(self, src: str) -> tuple[ndarray, str] | None:
        array_img = Utils.read_image(src)

        if array_img is not None:

            h_, w_ = array_img.shape[:2]
            resol = f"{w_}x{h_}"

            array_img = Utils.fit_to_thumb(array_img, Static.PIXMAP_SIZE_MAX)

            if src.endswith(Static.LAYERS_EXT):
                array_img = Utils.array_color(array_img, "BGR")

            if array_img is not None:
                return (array_img, resol)

            else:
                return (None, None)
        
        else:
            return (None, None)

    def insert_db(self):
        insert_count = 0
        # counter = 0

        for full_src, size, birth, mod in self.ins_items:

            if not ScanerTools.can_scan:
                return
            
            # counter += 1

            small_img, resol = self.get_small_img(full_src)

            if small_img is not None:

                full_hash_path = Utils.create_full_hash_path(full_src)

                values = {
                    "short_src": Utils.get_short_src(Brand.curr.collfolder, full_src),
                    "short_hash": Utils.get_short_hash_path(full_hash_path),
                    "size": size,
                    "birth": birth,
                    "mod": mod,
                    "resol": resol,
                    "coll": Utils.get_coll_name(Brand.curr.collfolder, full_src),
                    "fav": 0,
                    "brand": Brand.curr.name
                    }

                stmt = sqlalchemy.insert(THUMBS).values(**values) 
                self.insert_queries.append(stmt)
                self.hash_images.append((full_hash_path, small_img))

                # insert_count += 1

            else:
                continue

    def insert_cmd(self):
        conn = Dbase.engine.connect()

        for query in self.insert_queries:

            try:
                conn.execute(query)

            except sqlalchemy.exc.IntegrityError as e:
                Utils.print_err(error=e)
                conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                Utils.print_err(error=e)
                conn.rollback()
                conn.close()
                return None
            
        conn.commit()
        conn.close()

        ln_ = len(self.hash_images)

        for x, (full_hash_path, img_array) in enumerate(self.hash_images, start=1):

            brand = Brand.curr.name.capitalize()
            adding: str = Lang.adding
            t = f"{brand}: {adding.lower()} {x} {Lang.from_} {ln_}"
            ScanerTools.progressbar_text(t)
            sleep(ScanerTools.sleep_count)

            Utils.write_image_hash(full_hash_path, img_array)

        if self.hash_images:
            ScanerTools.reload_gui()


class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class ScanerThread(URunnable):

    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):

        for brand in Brand.all_:
            Brand.curr = brand

            self.brand_scan()
            print("scaner started", Brand.curr.name)

    def brand_scan(self):

        ScanerTools.can_scan = True

        finder_images = FinderImages()
        finder_images = finder_images.get()

        if finder_images:
        
            db_images = DbImages()
            db_images = db_images.get()

            compator = Compator(
                finder_images=finder_images,
                db_images=db_images
            )
            compator.get_result()

            db_updater = DbUpdater(
                del_items=compator.del_items,
                ins_items=compator.ins_items
            )
            db_updater.run()

        try:
            self.signals_.finished_.emit()
        except RuntimeError:
            pass
    

class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()

        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.start)

        self.wait_sec = 15000
        self.scaner_thread = None

    def start(self):
        self.wait_timer.stop()

        Brand.all_.clear()
        Brand.curr = None

        for brand_name in Static.BRANDS:

            brand_ind  = Static.BRANDS.index(brand_name)
            coll_folder = Utils.get_coll_folder(brand_ind=brand_ind)

            if coll_folder:

                Brand.all_.append(
                    Brand(
                        name=brand_name,
                        ind=brand_ind,
                        collfolder=coll_folder
                    )
                )

        if not Brand.all_:

            print("scaner no smb, wait", self.wait_sec//1000, "sec")
            self.wait_timer.start(self.wait_sec)

        elif self.scaner_thread:
            print("prev scan not finished, wait", self.wait_sec//1000, "sec")
            self.wait_timer.start(self.wait_sec)

        else:
            self.scaner_thread = ScanerThread()
            self.scaner_thread.signals_.finished_.connect(self.after_scan)
            UThreadPool.pool.start(self.scaner_thread)

    def stop(self):
        print("scaner manualy stoped.")
        ScanerTools.can_scan = False
        self.wait_timer.stop()

    def after_scan(self):
        print("scaner finished, new scan in", JsonData.scaner_minutes, "minutes")
        self.scaner_thread = None
        self.wait_timer.start(JsonData.scaner_minutes * 60 * 1000)
        Dbase.vacuum()
        ScanerTools.progressbar_text("")


class Scaner:
    app: ScanerShedule = None

    @classmethod
    def init(cls):
        cls.app = ScanerShedule()

    @classmethod
    def start(cls):
        cls.app.start()

    @classmethod
    def stop(cls):
        cls.app.stop()