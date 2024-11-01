import os
from time import sleep

import sqlalchemy
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from sqlalchemy import Connection

from cfg import DB_SIZE, IMG_EXT, PSD_TIFF, cnf
from database import Dbase, ThumbsMd
from signals import signals_app

from .image_utils import ImageUtils
from .main_utils import MainUtils


class ScanerUtils:
    can_scan = True
    counter = 15
    sleep_ = 0.2

    @classmethod
    def progressbar_value(cls, value: int):
        try:
            signals_app.progressbar_value.emit(value)
        except RuntimeError as e:
            MainUtils.print_err(parent=cls, error=e)

    @classmethod
    def reload_gui(cls):
        signals_app.reload_menu.emit()
        signals_app.reload_thumbnails.emit()

    @classmethod
    def conn_get(cls):
        return Dbase.engine.connect()
    
    @classmethod
    def conn_commit_(cls, conn: Connection):
        conn.commit()

    def conn_close(cls, conn: Connection):
        conn.close()


class Migrate:
    def start(self):
        conn = ScanerUtils.conn_get()

        q = sqlalchemy.select(ThumbsMd.src, ThumbsMd.collection)
        res: tuple[str, str] = conn.execute(q).first()

        if res:
            img_src, coll_name = res
        else:
            print("Migrate > can'l load row > no collection folder in db > it's ok")
            return
    
        old_coll_folder = img_src.split(os.sep + coll_name + os.sep)[0]

        if cnf.coll_folder == old_coll_folder:
            return
                
        q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
        res = conn.execute(q).fetchall()
        
        if len(res) == 0:
            return

        new_res = [
            (res_id, src.replace(old_coll_folder, cnf.coll_folder))
            for res_id, src in res
            ]
        
        for res_id, src in new_res:
            q = (
                sqlalchemy.update(ThumbsMd)
                .values({"src": src})
                .filter(ThumbsMd.id==res_id)
                )
            conn.execute(q)

        ScanerUtils.conn_commit_(conn)
        ScanerUtils.conn_close(conn)
        ScanerUtils.reload_gui()


class TrashRemover:

    def start(self):

        coll_folder = os.sep + cnf.coll_folder.strip(os.sep) + os.sep
        conn = ScanerUtils.conn_get()

        q = (sqlalchemy.select(ThumbsMd.src).where(ThumbsMd.src.not_like(f"%{coll_folder}%")))
        trash_img = conn.execute(q).scalar() or None

        if trash_img:
            q = (sqlalchemy.delete(ThumbsMd).where(ThumbsMd.src.not_like(f"%{coll_folder}%")))
            conn.execute(q)
            ScanerUtils.conn_commit_(conn)
            ScanerUtils.conn_close(conn)


class ImageItem:
    __slots__ = ["size", "created", "modified"]
    def __init__(self, size: int, created: int, modified: int):
        self.size = size
        self.created = created
        self.modified = modified


class FinderImages:
    def __init__(self):
        super().__init__()

    def get(self) -> dict[str, ImageItem]:
        finder_images: dict[str, ImageItem] = {}

        collections = [
            os.path.join(cnf.coll_folder, i)
            for i in os.listdir(cnf.coll_folder)
            if os.path.isdir(os.path.join(cnf.coll_folder, i))
            and
            i not in cnf.stop_colls
            ]

        if not collections:
            collections = [cnf.coll_folder]

        ln_colls = len(collections)
        step_value = int(60 if ln_colls == 0 else 60 / ln_colls)

        for collection in collections:

            ScanerUtils.progressbar_value(step_value)

            try:
                finder_images.update(self.walk_collection(collection))
            except TypeError as e:
                MainUtils.print_err(parent=self, error=e)
                continue

        return finder_images

    def walk_collection(self, collection: str) -> dict[str, ImageItem]:
        finder_images: dict[str, ImageItem] = {}

        for root, _, files in os.walk(collection):

            if not ScanerUtils.can_scan:
                return

            for file in files:

                if not os.path.exists(cnf.coll_folder):
                    ScanerUtils.can_scan = False
                    return

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
        q = sqlalchemy.select(ThumbsMd.src, ThumbsMd.size, ThumbsMd.created, ThumbsMd.modified)
        try:
            res = conn.execute(q).fetchall()
            return {
                src: ImageItem(size, created, modified)
                for src, size, created, modified in res
                }
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            ScanerUtils.conn_close(conn)
            return {}


class ComparedResult:
    def __init__(self):
        self.insert_items: dict[str, ImageItem] = {}
        self.update_items: dict[str, ImageItem] = {}
        self.delete_items : dict[str, ImageItem]= {}


class ImageCompator:
    def __init__(self, finder_images: dict[str, ImageItem], db_images: dict[str, ImageItem]):
        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def get_result(self) -> ComparedResult:
        result = ComparedResult()

        for db_src, db_item in self.db_images.items():

            if not ScanerUtils.can_scan:
                return

            in_finder = self.finder_images.get(db_src)

            if not in_finder:
                result.delete_items[db_src] = db_item

        for finder_src, finder_item in self.finder_images.items():

            if not ScanerUtils.can_scan:
                return

            in_db = self.db_images.get(finder_src)

            if not in_db:
                result.insert_items[finder_src] = finder_item

            elif not (finder_item.size, finder_item.modified) == (in_db.size, in_db.modified):
                result.update_items[finder_src] = finder_item

        return result


class DbUpdater:
    def __init__(self, compared_result: ComparedResult):
        super().__init__()
        self.res = compared_result

    def start(self):
        ScanerUtils.progressbar_value(70)

        if self.res.delete_items:
            self.delete_db()

        ScanerUtils.progressbar_value(80)

        if self.res.insert_items:
            self.insert_db()

        ScanerUtils.progressbar_value(90)

        if self.res.update_items:
            self.update_db()

    def create_db_img(self, src: str) -> bytes | None:
        array_img = ImageUtils.read_image(src)

        if array_img is None:
            return None
        
        array_img = ImageUtils.resize_max_aspect_ratio(array_img, DB_SIZE)

        if src.endswith(PSD_TIFF):
            array_img = ImageUtils.array_bgr_to_rgb(array_img)

        return ImageUtils.image_array_to_bytes(array_img)
    
    def get_insert_stmt(self, bytes_img: bytes, src: str, image_item: ImageItem):
        values = {
                "img150": bytes_img,
                "src": src,
                "size": image_item.size,
                "created": image_item.created,
                "modified": image_item.modified,
                "collection": MainUtils.get_coll_name(src),
                }

        return sqlalchemy.insert(ThumbsMd).values(values)
    
    def get_update_stmt(self, bytes_img: bytes, src: str, image_item: ImageItem):
        values = {
                "img150": bytes_img,
                "size": image_item.size,
                "created": image_item.created,
                "modified": image_item.modified,
                "collection": MainUtils.get_coll_name(src),
                }

        return sqlalchemy.update(ThumbsMd).values(values).where(ThumbsMd.src==src)
    
    def get_delete_stmt(self, src: str):
        return sqlalchemy.delete(ThumbsMd).where(ThumbsMd.src==src)

    def insert_db(self):
        counter = 0
        conn = ScanerUtils.conn_get()

        for src, image_item in self.res.insert_items.items():

            if not ScanerUtils.can_scan:
                return

            bytes_img = self.create_db_img(src)

            if not bytes_img:
                continue

            stmt = self.get_insert_stmt(bytes_img, src, image_item)
            conn.execute(stmt)

            counter += 1

            if counter == ScanerUtils.counter:
                counter = 0

                ScanerUtils.conn_commit_(conn)
                ScanerUtils.reload_gui()
                sleep(ScanerUtils.sleep_)
                conn = ScanerUtils.conn_get()

        if counter != 0:
            ScanerUtils.conn_commit_(conn)
        ScanerUtils.conn_close(conn)

    def update_db(self):
        counter = 0
        conn = ScanerUtils.conn_get()

        for src, image_item in self.res.update_items.items():

            if not ScanerUtils.can_scan:
                return

            bytes_img = self.create_db_img(src)

            if not bytes_img:
                continue

            stmt = self.get_update_stmt(bytes_img, src, image_item)
            conn.execute(stmt)

            counter += 1

            if counter == ScanerUtils.counter:
                counter = 0

                ScanerUtils.conn_commit_(conn)
                ScanerUtils.reload_gui()
                sleep(ScanerUtils.sleep_)
                conn = ScanerUtils.conn_get()
        
        if counter != 0:
            ScanerUtils.conn_commit_(conn)
        ScanerUtils.conn_close(conn)

    def delete_db(self):
        counter = 0
        conn = ScanerUtils.conn_get()

        for src, img_data in self.res.delete_items.items():

            if not ScanerUtils.can_scan:
                return

            stmt =  self.get_delete_stmt(src)
            conn.execute(stmt)

            counter += 1

            if counter == ScanerUtils.counter:
                counter = 0

                ScanerUtils.conn_commit_(conn)
                ScanerUtils.reload_gui()
                sleep(ScanerUtils.sleep_)
                conn = ScanerUtils.conn_get()

        if counter != 0:
            ScanerUtils.conn_commit_(conn)
        ScanerUtils.conn_close(conn)


class ScanerThread(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        self.scaner = self.start_scan()
        self.finished.emit()
    
    def start_scan(self):
        ScanerUtils.can_scan = True

        try:
            signals_app.progressbar_show.emit()
        except RuntimeError as e:
            MainUtils.print_err(parent=self, error=e)

        migrate = Migrate()
        migrate.start()

        finder_images = FinderImages()
        finder_images = finder_images.get()

        if finder_images:
        
            db_images = DbImages()
            db_images = db_images.get()

            image_compator = ImageCompator(finder_images, db_images)
            compared_res = image_compator.get_result()

            db_updater = DbUpdater(compared_res)
            db_updater.start()

        try:
            trash_remover = TrashRemover()
            trash_remover.start()
        except Exception as e:
            MainUtils.print_err(parent=trash_remover, error=e)

        Dbase.vacuum()
        ScanerUtils.can_scan = True

        try:
            signals_app.progressbar_hide.emit()
            ScanerUtils.reload_gui()
        except RuntimeError as e:
            MainUtils.print_err(parent=self, error=e)


class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()
        signals_app.scaner_start.connect(self.prepare_thread)
        signals_app.scaner_stop.connect(self.stop_thread)

        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.prepare_thread)

        self.scaner_thread = None

    def prepare_thread(self):
        self.wait_timer.stop()

        if not MainUtils.smb_check():
            print("scaner no smb")
            self.wait_timer.start(15000)

        elif self.scaner_thread:
            print("scaner wait prev scaner finished")
            self.wait_timer.start(15000)

        else:
            print("scaner started")
            self.start_thread()

    def start_thread(self):
        self.scaner_thread = ScanerThread()
        self.scaner_thread.finished.connect(self.finalize_scan)
        self.scaner_thread.start()

    def stop_thread(self):
        print("scaner manualy stoped from signals_app. You need emit scaner start signal")
        ScanerUtils.can_scan = False
        self.wait_timer.stop()

    def finalize_scan(self):
        print("scaner finished")
        try:
            self.scaner_thread.quit()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

        self.scaner_thread = None
        self.wait_timer.start(cnf.scaner_minutes * 60 * 1000)

