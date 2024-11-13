import os
from time import sleep

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from cfg import IMG_EXT, PIXMAP_SIZE_MAX, PSD_TIFF, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp

from .main_utils import Utils, MyThread


class ScanerUtils:
    can_scan = True

    @classmethod
    def progressbar_value(cls, value: int):
        try:
            SignalsApp.all.progressbar_set_value.emit(value)
        except RuntimeError as e:
            Utils.print_err(parent=cls, error=e)

    @classmethod
    def conn_commit(cls, conn: sqlalchemy.Connection):

        if cls.can_scan:

            try:
                conn.commit()
            except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.OperationalError) as e:
                Utils.print_err(parent=cls, error=e)
                conn.rollback()
                return

            try:
                SignalsApp.all.reload_menu_left.emit()
                SignalsApp.all.grid_thumbnails_cmd.emit("reload")
            except RuntimeError as e:
                Utils.print_err(parent=cls, error=e)


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
                Utils.print_err(parent=self, error=e)
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
            Utils.print_err(parent=self, error=e)
            return None


class DbImages:
    def __init__(self):
        super().__init__()

    def get(self) -> list[tuple[str, int, int, int]]:
        conn = Dbase.engine.connect()

        q = sqlalchemy.select(THUMBS.c.src, THUMBS.c.size, THUMBS.c.created, THUMBS.c.mod)

        try:
            # не забываем относительный путь ДБ преобразовать в полный
            res = conn.execute(q).fetchall()
            res = [
                (JsonData.coll_folder + src, size, created, mod)
                for src, size, created, mod in res
                ]

        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.IntegrityError) as e:
            Utils.print_err(parent=self, error=e)
            conn.rollback()
            res = []

        conn.close()
        return res


class ComparedResult:
    def __init__(self):
        self.ins_items: list[tuple[str, int, int, int]] = []
        self.del_items : list[tuple[str, int, int, int]] = []


class ImageCompator:
    def __init__(
            self,
            finder_images: list[tuple[str, int, int, int]],
            db_images: list[tuple[str, int, int, int]]
            ):

        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def get_result(self) -> ComparedResult:
        result = ComparedResult()

        for db_item in self.db_images:

            if not ScanerUtils.can_scan:
                return result

            if not db_item in self.finder_images:
                result.del_items.append(db_item)

        for finder_item in self.finder_images:

            if not ScanerUtils.can_scan:
                return result

            if not finder_item in self.db_images:
                result.ins_items.append(finder_item)

        return result


class DbUpdater:
    stmt_max_count = 15
    sleep_ = 0.2

    def __init__(self, compared_result: ComparedResult):
        super().__init__()
        self.compared_result = compared_result

        self.insert_queries: list[sqlalchemy.Insert] = []
        self.hash_images: list[tuple[str, ndarray]] = []

    def run(self):
        ScanerUtils.progressbar_value(70)
        self.del_db()
        ScanerUtils.progressbar_value(90)
        self.insert_db()

    def del_db(self):
        conn = Dbase.engine.connect()
        ok_ = True

        for src, size, created, mod in self.compared_result.del_items:
            q = sqlalchemy.delete(THUMBS).where(THUMBS.c.src==src)
            try:
                conn.execute(q)
            except sqlalchemy.exc.IntegrityError as e:
                Utils.print_err(parent=self, error=e)
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                Utils.print_err(parent=self, error=e)
                conn.rollback()
                conn.close()
                ok_ = False
                break
            
        if ok_:
            for src, size, created, mod in self.compared_result.del_items:
                os.remove(src)

            ScanerUtils.conn_commit(conn)
            conn.close()

    def get_small_img(self, src: str) -> ndarray | None:
        array_img = Utils.read_image(src)
        array_img = Utils.resize_max_aspect_ratio(array_img, PIXMAP_SIZE_MAX)

        if src.endswith(PSD_TIFF):
            array_img = Utils.array_color(array_img, "BGR")
        return array_img

    def get_stmt(self, src: str, size, created, mod, hash_path: str) -> sqlalchemy.Insert:
        
        # преобразуем полный путь в относительный для работы с ДБ
        src = src.replace(JsonData.coll_folder, "")

        values = {
                "src": src,
                "hash_path": hash_path,
                "size": size,
                "created": created,
                "mod": mod,
                "coll": Utils.get_coll_name(src),
                }

        return sqlalchemy.insert(THUMBS).values(**values) 

    def insert_db(self):
        insert_count = 0

        for src, size, created, mod in self.compared_result.ins_items:

            if not ScanerUtils.can_scan:
                return

            small_img = self.get_small_img(src)
            hash_path = Utils.get_hash_path(src)
            stmt = self.get_stmt(src, size, created, mod, hash_path)

            if small_img is not None:
                self.hash_images.append((hash_path, small_img))
                self.insert_queries.append(stmt)
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
        # итерация по инсертам вставка в дб
        # если все ок то записываем фотки

        conn = Dbase.engine.connect()
        ok_ = True

        for query in self.insert_queries:
            try:
                conn.execute(query)
            except sqlalchemy.exc.IntegrityError as e:
                Utils.print_err(parent=self, error=e)
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                Utils.print_err(parent=self, error=e)
                conn.rollback()
                conn.close()
                ok_ = False
                break
            
        if ok_:
            for hash_path, img_array in self.hash_images:
                Utils.write_image_hash(hash_path, img_array)

            ScanerUtils.conn_commit(conn)
            conn.close()


class ScanerThread(MyThread):
    _finished = pyqtSignal()

    def __init__(self):
        super().__init__(parent=None)

    def run(self):

        ScanerUtils.can_scan = True

        finder_images = FinderImages()
        finder_images = finder_images.get()

        if finder_images:
        
            db_images = DbImages()
            db_images = db_images.get()

            image_compator = ImageCompator(finder_images, db_images)
            compared_res = image_compator.get_result()

            db_updater = DbUpdater(compared_res)
            db_updater.run()

        self._finished.emit()
        self.remove_threads()
    

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
            self.scaner_thread._finished.connect(self.after_scan)
            self.scaner_thread.start()

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