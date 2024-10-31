import os
from collections import defaultdict
from typing import Literal

import sqlalchemy
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal

from cfg import IMG_EXT, PSD_TIFF, cnf
from database import Dbase, ThumbsMd
from signals import signals_app

from .image_utils import ImageUtils
from .main_utils import MainUtils


class Shared:
    flag = True


class Migrate:
    def start(self):
        conn = Dbase.engine.connect()

        try:
            q = sqlalchemy.select(ThumbsMd.src, ThumbsMd.collection)
            img_src, coll_name = conn.execute(q).first()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            return
        
        try:
            img_src: str
            old_coll_folder = img_src.split(os.sep + coll_name + os.sep)[0]
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            return

        if cnf.coll_folder == old_coll_folder:
            return
                
        try:
            q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
            res = conn.execute(q).fetchall()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            return
        
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

        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

        conn.close()
        signals_app.reload_menu.emit()
        signals_app.reload_thumbnails.emit()
        signals_app.migrate_finished.emit()


class TrashRemover:
    def start(self):
        coll_folder = os.sep + cnf.coll_folder.strip(os.sep) + os.sep

        conn = Dbase.engine.connect()

        q = (sqlalchemy.select(ThumbsMd.src)
            .filter(ThumbsMd.src.not_like(f"%{coll_folder}%")))

        try:
            trash_img = conn.execute(q).first()
        
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            return

        if trash_img:

            q = (sqlalchemy.delete(ThumbsMd)
                .filter(ThumbsMd.src.not_like(f"%{coll_folder}%")))

            try:
                conn.execute(q)
                conn.commit()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)
                return
            finally:
                conn.close()


class DubFinder:
    def start(self):
        q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
        conn = Dbase.engine.connect()
        res = conn.execute(q).fetchall()

        dubs = defaultdict(list)

        for res_id, res_src in res:
            dubs[res_src].append(res_id)

        dubs = [
            x
            for k, v in dubs.items()
            for x in v[1:]
            if len(v) > 1
            ]

        if dubs:
            values = [
                sqlalchemy.delete(ThumbsMd).filter(ThumbsMd.id==dub_id)
                for dub_id in dubs
                ]

            for i in values:
                conn.execute(i)

            conn.commit()
            conn.close()


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
            and i not in cnf.stop_colls
            ]

        if not collections:
            collections = [cnf.coll_folder]

        ln_colls = len(collections)
        step_value = 60 if ln_colls == 0 else 60 / ln_colls

        for collection in collections:

            try:
                signals_app.progressbar_value.emit(step_value)
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            finder_images.update(self.walk_collection(collection))

        return finder_images


    def walk_collection(self, collection: str) -> dict[str, ImageItem]:

        finder_images: dict[str, ImageItem] = {}

        for root, _, files in os.walk(collection):

            if not Shared.flag:
                return

            for file in files:

                if not os.path.exists(cnf.coll_folder):
                    Shared.flag = False
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
        except (FileNotFoundError) as e:
            MainUtils.print_err(parent=self, error=e)
            return None


class DbImages:
    def __init__(self):
        super().__init__()

    def get(self) -> dict[str, ImageItem]:
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(ThumbsMd.src, ThumbsMd.size, ThumbsMd.created, ThumbsMd.modified)
        try:
            res = conn.execute(q).fetchall()
            return {
                src: ImageItem(size, created, modified)
                for src, size, created, modified in res
                }
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            conn.close()
            return {}


class ComparedResult:
    def __init__(self):
        self.insert: dict[str, ImageItem] = {}
        self.update: dict[str, ImageItem] = {}
        self.delete : dict[str, ImageItem]= {}


class CompareImages:
    def __init__(self, finder_images: dict[str, ImageItem], db_images: dict[str, ImageItem]):
        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def get_result(self) -> ComparedResult:

        compared_result = ComparedResult()

        for db_src, db_item in self.db_images.items():

            if not Shared.flag:
                return

            finder_item = self.finder_images.get(db_src)

            if not finder_item:
                compared_result.delete[db_src] = db_item

        for finder_src, finder_item in self.finder_images.items():

            if not Shared.flag:
                return

            db_item = self.db_images.get(finder_src)
            b = (finder_item.size, finder_item.modified) == (db_item.size, db_item.modified)

            if not db_item:
                compared_result.insert[finder_src] = finder_item

            if db_item and not b:
                compared_result.update[finder_src] = finder_item

        return compared_result


class DbUpdater:
    def __init__(self, compared_result: ComparedResult):
        super().__init__()
        self.compared_result = compared_result

    def start(self):

        self.progressbar_value(70)

        if self.compared_result.delete:
            self.delete_db()

        self.progressbar_value(80)

        if self.compared_result.insert:
            self.insert_db()

        self.progressbar_value(90)

        if self.compared_result.update:
            self.update_db()

    def progressbar_value(self, value):
        try:
            signals_app.progressbar_value.emit(90)
        except RuntimeError as e:
            MainUtils.print_err(parent=self, error=e)

    def insert_db(self):
        counter = 0
        conn = Dbase.engine.connect()

        for src, img_data in self.compared_result.insert.items():

            if not Shared.flag:
                return

            size, created, modified = img_data
            array_img = ImageUtils.read_image(src)

            if array_img is None:     
                continue

            array_img = ImageUtils.resize_min_aspect_ratio(array_img, cnf.THUMBSIZE)

            if src.endswith(PSD_TIFF):
                array_img = ImageUtils.array_bgr_to_rgb(array_img)

            bytes_img = ImageUtils.image_array_to_bytes(array_img)

            values = {
                    "img150": bytes_img,
                    "src": src,
                    "size": size,
                    "created": created,
                    "modified": modified,
                    "collection": MainUtils.get_coll_name(src),
                    }

            stmt =  sqlalchemy.insert(ThumbsMd).values(values)
            conn.execute(stmt)

            counter += 1

            if counter == 10:
                counter = 0
                conn.commit()
                conn = Dbase.engine.connect()
                signals_app.reload_thumbnails.emit()
                signals_app.reload_menu.emit()

        if counter != 0:
            conn.commit()
        conn.close()

    def update_db(self):
        counter = 0
        conn = Dbase.engine.connect()

        for src, img_data in self.compared_result.update.items():

            if not Shared.flag:
                return

            size, created, modified = img_data
            array_img = ImageUtils.read_image(src)

            if array_img is None:
                continue

            array_img = ImageUtils.resize_min_aspect_ratio(array_img, cnf.THUMBSIZE)

            if src.endswith(PSD_TIFF):
                array_img = ImageUtils.array_bgr_to_rgb(array_img)

            bytes_img = ImageUtils.image_array_to_bytes(array_img)

            values = {
                    "img150": bytes_img,
                    "size": size,
                    "created": created,
                    "modified": modified,
                    "collection": MainUtils.get_coll_name(src),
                    }

            stmt =  sqlalchemy.update(ThumbsMd).values(values).where(ThumbsMd.src==src)
            conn.execute(stmt)

            counter += 1

            if counter == 10:
                counter = 0
                conn.commit()
                conn = Dbase.engine.connect()
                signals_app.reload_thumbnails.emit()
                signals_app.reload_menu.emit()
        
        if counter != 0:
            conn.commit()
        conn.close()

    def delete_db(self):
        counter = 0
        conn = Dbase.engine.connect()

        for src, img_data in self.compared_result.delete.items():

            if not Shared.flag:
                return

            stmt =  sqlalchemy.delete(ThumbsMd).where(ThumbsMd.src==src)
            conn.execute(stmt)

            counter += 1

            if counter == 10:
                counter = 0
                conn.commit()
                conn = Dbase.engine.connect()
                signals_app.reload_thumbnails.emit()
                signals_app.reload_menu.emit()

        if counter != 0:
            conn.commit()
        conn.close()


class ScanerThread(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        self.scaner = self.start_scan()
        self.finished.emit()
    
    def start_scan(self):
        try:
            Shared.flag = True

            try:
                signals_app.progressbar_show.emit()
            except RuntimeError as e:
                MainUtils.print_err(parent=self, error=e)

            migrate = Migrate()
            migrate.start()

            finder_images = FinderImages()
            finder_images = finder_images.get()

            db_images = DbImages()
            db_images = db_images.get()

            if not finder_images:
                return

            compared_res = CompareImages(finder_images, db_images)
            compared_res = compared_res.get_result()

            db_updater = DbUpdater(compared_result=compared_res)
            db_updater.start()

            trash_remover = TrashRemover()
            trash_remover.start()
            dub_finder = DubFinder()
            dub_finder.start()

            Dbase.vacuum()

            Shared.flag = True

            try:
                signals_app.progressbar_hide.emit()
                signals_app.reload_menu.emit()
                signals_app.reload_thumbnails.emit()
            except RuntimeError as e:
                MainUtils.print_err(parent=self, error=e)

        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

            try:
                signals_app.progressbar_hide.emit()
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
        Shared.flag = False
        self.wait_timer.stop()

    def finalize_scan(self):
        try:
            self.scaner_thread.quit()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

        self.scaner_thread = None
        self.wait_timer.start(cnf.scaner_minutes * 60 * 1000)

