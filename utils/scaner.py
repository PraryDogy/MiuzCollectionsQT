import os
from time import sleep

import numpy as np
import sqlalchemy
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from sqlalchemy import Connection, Delete, Insert, Update

from cfg import IMG_EXT, PIXMAP_SIZE_MAX, PSD_TIFF, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp

from .main_utils import ImageUtils, MainUtils, MyThread


class ScanerUtils:
    can_scan = True
    stmt_max_count = 15
    sleep_ = 0.2

    @classmethod
    def progressbar_value(cls, value: int):
        try:
            SignalsApp.all.progressbar_set_value.emit(value)
        except RuntimeError as e:
            MainUtils.print_err(parent=cls, error=e)

    @classmethod
    def conn_get(cls):
        return Dbase.engine.connect()
    
    @classmethod
    def conn_commit(cls, conn: Connection):

        if cls.can_scan:
            conn.commit()

            try:
                SignalsApp.all.reload_menu_left.emit()
                SignalsApp.all.grid_thumbnails_cmd.emit("reload")
            except RuntimeError as e:
                MainUtils.print_err(parent=cls, error=e)

    @classmethod
    def conn_close(cls, conn: Connection):
        conn.close()


class ImageItem:
    __slots__ = ["size", "created", "mod"]
    def __init__(self, size: int, created: int, mod: int):
        self.size = size
        self.created = created
        self.mod = mod


class FinderImages:
    def __init__(self):
        super().__init__()

    def get(self) -> dict[str, ImageItem]:
        finder_images: dict[str, ImageItem] = {}

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
                # if walked is None:
                    # print(collection)
                    # print(walked)
                    # continue
                finder_images.update(walked)
            except TypeError as e:
                MainUtils.print_err(parent=self, error=e)
                continue

        return finder_images

    def walk_collection(self, collection: str) -> dict[str, ImageItem]:
        finder_images: dict[str, ImageItem] = {}

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
                        finder_images[src] = item

        return finder_images
    
    def get_image_item(self, src: str) -> ImageItem:
        try:
            stats = os.stat(path=src)
            return ImageItem(stats.st_size, stats.st_birthtime, stats.st_mtime)
        except FileNotFoundError as e:
            MainUtils.print_err(parent=self, error=e)
            return None


class DbImages:
    def __init__(self):
        super().__init__()

    def get(self) -> dict[str, ImageItem]:
        conn = ScanerUtils.conn_get()
        q = sqlalchemy.select(THUMBS.c.src, THUMBS.c.size, THUMBS.c.created, THUMBS.c.mod)
        try:
            res = conn.execute(q).fetchall()
            # не забываем относительный путь ДБ преобразовать в полный
            return {
                JsonData.coll_folder + src: ImageItem(size, created, mod)
                for src, size, created, mod in res
                }
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            ScanerUtils.conn_close(conn)
            return {}


class ComparedResult:
    def __init__(self):
        self.ins_items: dict[str, ImageItem] = {}
        self.upd_items: dict[str, ImageItem] = {}
        self.del_items : dict[str, ImageItem]= {}


class ImageCompator:
    def __init__(self, finder_images: dict[str, ImageItem], db_images: dict[str, ImageItem]):
        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def get_result(self) -> ComparedResult:
        result = ComparedResult()

        for db_src, db_item in self.db_images.items():

            if not ScanerUtils.can_scan:
                return result

            in_finder = self.finder_images.get(db_src)

            if not in_finder:
                result.del_items[db_src] = db_item

        for finder_src, finder_item in self.finder_images.items():

            if not ScanerUtils.can_scan:
                return result

            in_db = self.db_images.get(finder_src)

            if not in_db:
                result.ins_items[finder_src] = finder_item

            elif not (finder_item.size, finder_item.mod) == (in_db.size, in_db.mod):
                result.upd_items[finder_src] = finder_item

        return result


class DbUpdater:
    def __init__(self, compared_result: ComparedResult):
        super().__init__()
        self.res = compared_result
        self.flag_del = "delete"
        self.flag_ins = "insert"
        self.flag_upd = "update"

    def start(self):
        ScanerUtils.progressbar_value(70)
        self.modify_db(compared_items=self.res.del_items, flag=self.flag_del)
        ScanerUtils.progressbar_value(80)
        self.modify_db(compared_items=self.res.ins_items, flag=self.flag_ins)
        ScanerUtils.progressbar_value(90)
        self.modify_db(compared_items=self.res.upd_items, flag=self.flag_upd)

    def get_bytes_img(
            self,
            flag: str,
            src: str
            ) -> bytes | None:

        if flag == self.flag_del:
            return None

        else:
            array_img = ImageUtils.read_image(src)

            if isinstance(array_img, np.ndarray):
                array_img = ImageUtils.resize_max_aspect_ratio(array_img, PIXMAP_SIZE_MAX)

                if src.endswith(PSD_TIFF):
                    array_img = ImageUtils.array_color(array_img, "BGR")

                return ImageUtils.image_array_to_bytes(array_img)

            else:
                return None
  
    def get_stmt(
            self,
            flag: str,
            bytes_img: bytes,
            src: str,
            image_item: ImageItem
            ) -> Delete | Insert | Update:
        
        # преобразуем полный путь в относительный для работы с ДБ
        src = src.replace(JsonData.coll_folder, "")

        if flag == self.flag_del:
            return sqlalchemy.delete(THUMBS).where(THUMBS.c.src==src)

        values = {
                "img": bytes_img,
                "src": src,
                "size": image_item.size,
                "created": image_item.created,
                "mod": image_item.mod,
                "coll": MainUtils.get_coll_name(src),
                }
        
        if flag == self.flag_ins:
            return sqlalchemy.insert(THUMBS).values(**values) 
           
        else:
            return sqlalchemy.update(THUMBS).values(**values).where(THUMBS.c.src==src)

    def modify_db(self, compared_items: dict[str, ImageItem], flag: str):
        stmt_count = 0
        conn = ScanerUtils.conn_get()

        for src, image_item in compared_items.items():

            if not ScanerUtils.can_scan:
                return

            bytes_img = self.get_bytes_img(flag=flag, src=src)
            stmt = self.get_stmt(flag=flag, bytes_img=bytes_img, src=src, image_item=image_item)

            if flag == self.flag_del:
                conn.execute(stmt)

            elif bytes_img is not None:
                conn.execute(stmt)

            else:
                print("scaner > updater > byte img is None", src)
                continue

            stmt_count += 1

            if stmt_count == ScanerUtils.stmt_max_count:
                stmt_count = 0

                ScanerUtils.conn_commit(conn)
                sleep(ScanerUtils.sleep_)
                conn = ScanerUtils.conn_get()
        
        if stmt_count != 0:
            ScanerUtils.conn_commit(conn)
        ScanerUtils.conn_close(conn)


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
            db_updater.start()

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

        if not MainUtils.smb_check():
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
        return
        cls.app.start()

    @classmethod
    def stop(cls):
        return
        cls.app.stop()