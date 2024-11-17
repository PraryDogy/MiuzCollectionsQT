import os
from time import sleep

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from cfg import IMG_EXT, PIXMAP_SIZE_MAX, PSD_TIFF, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp

from .utils import URunnable, UThreadPool, Utils


class ScanerUtils:
    can_scan = True

    @classmethod
    def progressbar_value(cls, value: int):
        try:
            SignalsApp.all_.progressbar_set_value.emit(value)
        except RuntimeError as e:
            Utils.print_err(error=e)

    @classmethod
    def reload_gui(cls):
        if cls.can_scan:
            try:
                SignalsApp.all_.reload_menu_left.emit()
                SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
            except RuntimeError as e:
                Utils.print_err(error=e)


class FinderImages:
    def __init__(self):
        super().__init__()

    def get(self) -> list[tuple[str, int, int, int]]:
        finder_images: list[tuple[str, int, int, int]] = []

        collections = [
            os.path.join(JsonData.coll_folder, i)
            for i in os.listdir(JsonData.coll_folder)
            if os.path.isdir(os.path.join(JsonData.coll_folder, i))
            and
            i not in JsonData.stop_colls
            ]

        if not collections:
            collections = [JsonData.coll_folder]
            step_value = 60
        else:
            step_value = round(60 / len(collections))

        step_value_temp = 0

        for collection in collections:
            
            step_value_temp += step_value
            ScanerUtils.progressbar_value(step_value_temp)

            try:
                walked = self.walk_collection(collection)
                finder_images.extend(walked)
            except TypeError as e:
                Utils.print_err(error=e)
                continue
        return finder_images

    def walk_collection(self, collection: str) -> list[tuple[str, int, int, int]]:
        finder_images: list[tuple[str, int, int, int]] = []

        for root, _, files in os.walk(collection):

            if not ScanerUtils.can_scan:
                return finder_images

            for file in files:

                if not os.path.exists(JsonData.coll_folder):
                    ScanerUtils.can_scan = False
                    return finder_images

                if file.endswith(IMG_EXT):
                    src = os.path.join(root, file)
                    item = self.get_image_item(src)
                    if item:
                        finder_images.append(item)

        return finder_images
    
    def get_image_item(self, src: str) -> list[tuple[str, int, int, int]]:
        try:
            stats = os.stat(path=src)
            return (src, stats.st_size, stats.st_birthtime, stats.st_mtime)
        except FileNotFoundError as e:
            Utils.print_err(error=e)
            return None


class DbImages:
    def __init__(self):
        super().__init__()

    def get(self) -> dict[str, tuple[str, int, int, int]]:
        conn = Dbase.engine.connect()

        q = sqlalchemy.select(
            THUMBS.c.hash_path,
            THUMBS.c.src,
            THUMBS.c.size,
            THUMBS.c.birth,
            THUMBS.c.mod
            )

        # не забываем относительный путь ДБ преобразовать в полный
        res = conn.execute(q).fetchall()
        conn.close()

        return {
            hash_path: (JsonData.coll_folder + src, size, birth, mod)
            for hash_path, src, size, birth, mod in res
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
        for hash_path, db_item in self._db_images.items():

            if not ScanerUtils.can_scan:
                return

            if not db_item in self._finder_images:
                self.del_items.append(hash_path)

        _db_images = list(self._db_images.values())

        for finder_item in self._finder_images:

            if not ScanerUtils.can_scan:
                return

            if not finder_item in _db_images:
                self.ins_items.append(finder_item)


class DbUpdater:
    stmt_max_count = 15
    sleep_ = 0.0

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
        ScanerUtils.progressbar_value(70)
        self.del_db()
        ScanerUtils.progressbar_value(90)
        self.insert_db()

    def del_db(self):
        conn = Dbase.engine.connect()

        for hash_path in self.del_items:
            q = sqlalchemy.delete(THUMBS).where(THUMBS.c.hash_path==hash_path)

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

        for hash_path in self.del_items:
            try:
                os.remove(hash_path)
            except Exception as e:
                Utils.print_err(error=e)

        if self.del_items:
            ScanerUtils.reload_gui()

    def get_small_img(self, src: str) -> tuple[ndarray, str] | None:
        array_img = Utils.read_image(src)

        if array_img is not None:

            h_, w_ = array_img.shape[:2]
            resol = f"{w_}x{h_}"

            array_img = Utils.fit_to_thumb(array_img, PIXMAP_SIZE_MAX)

            if src.endswith(PSD_TIFF):
                array_img = Utils.array_color(array_img, "BGR")

            if array_img is not None:
                return (array_img, resol)

            else:
                return (None, None)
        
        else:
            return (None, None)

    def insert_db(self):
        insert_count = 0
        counter = 0
        ln = len(self.ins_items)

        for src, size, birth, mod in self.ins_items:

            if not ScanerUtils.can_scan:
                return
            
            print(f"{counter} из {ln}")
            counter += 1

            small_img, resol = self.get_small_img(src)

            if small_img is not None:
                hash_path = Utils.get_hash_path(src)

                values = {
                    "src": src.replace(JsonData.coll_folder, ""),
                    "hash_path": hash_path,
                    "size": size,
                    "birth": birth,
                    "mod": mod,
                    "resol": resol,
                    "coll": Utils.get_coll_name(src),
                    "fav": 0
                    }

                stmt = sqlalchemy.insert(THUMBS).values(**values) 
                self.insert_queries.append(stmt)

                self.hash_images.append((hash_path, small_img))

                insert_count += 1

            else:
                continue

            if insert_count == DbUpdater.stmt_max_count:
                insert_count = 0
                self.insert_cmd()
                sleep(DbUpdater.sleep_)
                self.insert_queries.clear()
                self.hash_images.clear()

        self.insert_cmd()

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

        for hash_path, img_array in self.hash_images:
            Utils.write_image_hash(hash_path, img_array)

        if self.hash_images:
            ScanerUtils.reload_gui()


class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class ScanerThread(URunnable):

    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):

        ScanerUtils.can_scan = True

        finder_images = FinderImages()
        finder_images = finder_images.get()

        if finder_images:
        
            db_images = DbImages()
            db_images = db_images.get()

            compator = Compator(finder_images, db_images)
            compator.get_result()

            db_updater = DbUpdater(compator.del_items, compator.ins_items)
            db_updater.run()

        self.signals_.finished_.emit()
    

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

        if not Utils.smb_check():
            print("scaner no smb, wait", self.wait_sec//1000, "sec")
            self.wait_timer.start(self.wait_sec)

        elif self.scaner_thread:
            print("prev scan not finished, wait", self.wait_sec//1000, "sec")
            self.wait_timer.start(self.wait_sec)

        else:
            print("scaner started")
            self.scaner_thread = ScanerThread()
            self.scaner_thread.signals_.finished_.connect(self.after_scan)
            UThreadPool.pool.start(self.scaner_thread)

    def stop(self):
        print("scaner manualy stoped.")
        ScanerUtils.can_scan = False
        self.wait_timer.stop()

    def after_scan(self):
        print("scaner finished, new scan in", JsonData.scaner_minutes, "minutes")
        self.scaner_thread = None
        self.wait_timer.start(JsonData.scaner_minutes * 60 * 1000)
        Dbase.vacuum()
        ScanerUtils.progressbar_value(100)


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