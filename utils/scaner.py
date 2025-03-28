import gc
import os
from time import sleep

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from brands import Brand
from cfg import JsonData, Static, ThumbData
from database import CLMN_NAMES, THUMBS, Dbase
from lang import Lang
from signals import SignalsApp

from .utils import URunnable, UThreadPool, Utils


class ScanerTools:
    current_brand: Brand
    avaiable_brands: list[Brand] = []
    can_scan: bool = True

    @classmethod
    def progressbar_text(cls, text: str):
        try:
            SignalsApp.instance.progressbar_text.emit(text)
        except RuntimeError as e:
            pass

    @classmethod
    def reload_gui(cls):
        if cls.can_scan:
            try:
                SignalsApp.instance.menu_left_cmd.emit("reload")
                SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
            except RuntimeError as e:
                Utils.print_err(error=e)


class FinderImages:

    def run(self) -> list[tuple[str, int, int, int]] | None:
        """Основной метод для поиска изображений в коллекциях."""
        collections = self.get_collections()
        if collections:
            return self.process_collections(collections)
        else:
            return None

    def get_collections(self) -> list[str]:
        """Получает список коллекций, исключая остановленные."""
        collections = []

        try:
            coll_folder = ScanerTools.current_brand.coll_folder_path
            stop_colls = ScanerTools.current_brand.stop_colls

            for item in os.listdir(coll_folder):
                item_path = os.path.join(coll_folder, item)
                if os.path.isdir(item_path) and item not in stop_colls:
                    collections.append(item_path)

        except FileNotFoundError:
            ...

        return collections

    def process_collections(
            self,
            collections: list[str]
    ) -> list[tuple[str, int, int, int]]:

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
        brand = ScanerTools.current_brand.name.capitalize()
        collection_name = Lang.collection
        return f"{brand}: {collection_name.lower()} {current} {Lang.from_} {total}"

    def walk_collection(self, coll: str) -> list[tuple[str, int, int, int]]:
        """Рекурсивно обходит директорию и находит изображения."""
        finder_images = []
        stack = []
        stack.append(coll)

        while stack:
            current_dir = stack.pop()

            with os.scandir(current_dir) as entries:

                for entry in entries:

                    # нельзя удалять
                    # это прервет FinderImages, но не остальные классы
                    if not ScanerTools.can_scan:
                        return finder_images

                    if entry.is_dir():
                        stack.append(entry.path)

                    elif entry.name.endswith(Static.IMG_EXT):
                        finder_images.append(self.get_file_data(entry))

        return finder_images

    def get_file_data(self, entry: os.DirEntry) -> tuple[str, int, int, int]:
        """Получает данные файла."""
        stats = entry.stat()
        return (
            entry.path,
            int(stats.st_size),
            int(stats.st_birthtime),
            int(stats.st_mtime),
        )


class DbImages:

    def run(self) -> dict[str, tuple[str, int, int, int]]:
        ScanerTools.progressbar_text("")
        conn = Dbase.engine.connect()

        q = sqlalchemy.select(
            THUMBS.c.short_hash,
            THUMBS.c.short_src,
            THUMBS.c.size,
            THUMBS.c.birth,
            THUMBS.c.mod
            )
        
        q = q.where(THUMBS.c.brand == ScanerTools.current_brand.name)

        # не забываем относительный путь к изображению преобразовать в полный
        # для сравнения с finder_items
        res = conn.execute(q).fetchall()
        conn.close()
        coll_folder = ScanerTools.current_brand.coll_folder_path

        return {
            short_hash: (
                Utils.get_full_src(coll_folder, short_src),
                size,
                birth,
                mod
            )
            for short_hash, short_src, size, birth, mod in res
        }


class Compator:

    def run(
            self,
            finder_images: list[tuple[str, int, int, int]],
            db_images: dict[str, tuple[str, int, int, int]]
    ):

        del_items: list[str] = []
        ins_items: list[tuple[str, int, int, int]] = []

        for short_hash, db_item in db_images.items():
            if not db_item in finder_images:
                del_items.append(short_hash)

        db_values = list(db_images.values())

        for finder_item in finder_images:
            if not finder_item in db_values:
                ins_items.append(finder_item)

        return (del_items, ins_items)


class DbUpdater:
    sleep_count: float = 0.1

    def __init__(self, del_items: list[str], ins_items: list[tuple[str, int, int, int]]):

        super().__init__()

        values = self.get_values(*["" for i in range(0, 6)])
        values = list(values.keys())
        assert CLMN_NAMES == values

        self.del_db(del_items=del_items)
        self.del_images(del_items=del_items)

        queries = self.create_queries(ins_items=ins_items)
        self.insert_db(queries=queries)
        self.insert_images(queries=queries)

    def del_db(self, del_items: list[str]):
        conn = Dbase.engine.connect()

        for short_hash in del_items:

            # нельзя удалять
            # если удалить этот флаг, то когда флаг будет false,
            # произойдет массовое удаление из БД
            # так как FinderItems прерван данным флагом
            # то есть Compator при сравнении с БД посчитает,
            # что из Finder было удалено множество изображений
            # и удалит их из БД
            if not ScanerTools.can_scan:
                return
        
            q = sqlalchemy.delete(THUMBS)
            q = q.where(THUMBS.c.short_hash==short_hash)

            try:
                conn.execute(q)

            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
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

    def del_images(self, del_items: list[str]):

        total = len(del_items)

        for x, short_hash in enumerate(del_items, start=1):

            # не удалять
            if not ScanerTools.can_scan:
                return

            full_hash = Utils.get_full_hash(short_hash)

            if os.path.exists(full_hash):

                self.progressbar_text(text=Lang.deleting, x=x, total=total)
                os.remove(full_hash)
                sleep(self.sleep_count)

        if total > 0:
            ScanerTools.reload_gui()

    def get_small_img(self, src: str) -> tuple[ndarray, str] | tuple[None, None]:

        array_img_src = Utils.read_image(src)
        array_img = Utils.fit_to_thumb(array_img_src, ThumbData.DB_PIXMAP_SIZE)

        del array_img_src
        gc.collect()

        if array_img is not None:
            h_, w_ = array_img.shape[:2]
            resol = f"{w_}x{h_}"
            return (array_img, resol)

        else:
            return (None, None)

    def get_values(self, full_src, full_hash, size, birth, mod, resol):
        coll_folder = ScanerTools.current_brand.coll_folder_path
        return {
            "short_src": Utils.get_short_src(coll_folder, full_src),
            "short_hash": Utils.get_short_hash(full_hash),
            "size": size,
            "birth": birth,
            "mod": mod,
            "resol": resol,
            "coll": Utils.get_coll_name(coll_folder, full_src),
            "fav": 0,
            "brand": ScanerTools.current_brand.name
        }

    def create_queries(self, ins_items: list[tuple[str, int, int, int]]):

        res: dict[sqlalchemy.Insert, tuple[str, ndarray]] = {}

        for full_src, size, birth, mod in ins_items:

            # не удалять
            if not ScanerTools.can_scan:
                return

            small_img, resol = self.get_small_img(full_src)

            if small_img is not None:

                full_hash = Utils.create_full_hash(full_src)

                values = self.get_values(
                    full_src=full_src,
                    full_hash=full_hash,
                    size=size,
                    birth=birth, 
                    mod=mod,
                    resol=resol
                )

                stmt = sqlalchemy.insert(THUMBS).values(**values) 
                res[stmt] = (full_hash, small_img)

            else:
                continue

        return res

    def insert_db(self, queries: dict[sqlalchemy.Insert, tuple[str, ndarray]]):
        conn = Dbase.engine.connect()

        if queries is None:
            ScanerTools.can_scan = False
            return

        for query in queries.keys():

            # не удалять
            if not ScanerTools.can_scan:
                return

            try:
                conn.execute(query)

            # overflow error бывает прозникает когда пишет
            # python integer too large to insert db
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
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

    def insert_images(self, queries: dict[sqlalchemy.Insert, tuple[str, ndarray]]):

        if queries is None:
            ScanerTools.can_scan = False
            return

        total = len(queries)

        for x, (full_hash, img_array) in enumerate(queries.values(), start=1):

            # не удалять
            if not ScanerTools.can_scan:
                return

            self.progressbar_text(text=Lang.adding, x=x, total=total)
            Utils.write_image_hash(full_hash, img_array)
            sleep(self.sleep_count)

        if total > 0:
            ScanerTools.reload_gui()

    def progressbar_text(self, text: str, x: int, total: int):
        """
        text: `Lang.adding`, `Lang.deleting`
        x: item of `enumerate`
        total: `len`
        """

        brand = ScanerTools.current_brand.name.capitalize()
        t = f"{brand}: {text.lower()} {x} {Lang.from_} {total}"
        ScanerTools.progressbar_text(t)


class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class ScanerThread(URunnable):

    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):
        for brand in ScanerTools.avaiable_brands:
            ScanerTools.current_brand = brand
            self.brand_scan()
            print("scaner started", brand.name)

    def brand_scan(self):
        ScanerTools.can_scan = True
        finder_images = FinderImages()
        finder_images = finder_images.run()

        if finder_images is not None:
        
            db_images = DbImages()
            db_images = db_images.run()

            compator = Compator()
            del_items, ins_items = compator.run(
                finder_images=finder_images,
                db_images=db_images
            )

            DbUpdater(
                del_items=del_items,
                ins_items=ins_items
            )

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

        self.wait_sec = 30000
        self.scaner_thread = None

    def start(self):
        self.wait_timer.stop()

        if self.scaner_thread:
            print("prev scan not finished, wait", self.wait_sec//1000, "sec")
            self.wait_timer.start(self.wait_sec)
            return

        ScanerTools.avaiable_brands.clear()
        ScanerTools.current_brand = None
        
        for brand in Brand.brands_list:
            coll_folder = Utils.get_brand_coll_folder(brand=brand)
            if coll_folder:
                brand.coll_folder_path = coll_folder
                ScanerTools.avaiable_brands.append(brand)

        if not ScanerTools.avaiable_brands:
            print("scaner no smb, wait", self.wait_sec//1000, "sec")
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
        # return
        cls.app.start()

    @classmethod
    def stop(cls):
        # return
        cls.app.stop()