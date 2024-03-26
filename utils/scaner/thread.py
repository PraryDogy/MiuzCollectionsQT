import os
import traceback
from abc import ABC, abstractmethod
from time import sleep
from typing import Literal

import sqlalchemy
from PyQt5.QtCore import QThread

from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app, utils_signals_app

from ..image_utils import BytesThumb, UndefBytesThumb
from ..main_utils import MainUtils
from typing import Dict, List
from sqlalchemy.orm import Query

class Manager:
    jpg_exsts = (".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG")
    tiff_exsts = (".tiff", ".TIFF", ".psd", ".PSD", ".psb", ".PSB", ".tif", ".TIF")
    flag = True

    @staticmethod
    def sleep():
        return
        sleep(0.5)


class NonExistCollRemover:
    def __init__(self):
        coll_folder = cnf.coll_folder + os.sep

        q = (sqlalchemy.select(ThumbsMd.src)
            .filter(ThumbsMd.src.not_like(f"%{coll_folder}%")))

        session = Dbase.get_session()
        try:
            trash_img = session.execute(q).first()
        finally:
            session.close()

        if trash_img:

            q = (sqlalchemy.delete(ThumbsMd)
                .filter(ThumbsMd.src.not_like(f"%{coll_folder}%")))

            session = Dbase.get_session()
            try:
                session.execute(q)
                session.commit()
            finally:
                session.close()


class FinderImages(dict):
    def __init__(self):
        super().__init__()

        try:
            self.run()

        except (OSError, FileNotFoundError):
            print(traceback.format_exc())
            utils_signals_app.scaner_err.emit()
            Manager.flag = False

    def run(self):
        gui_signals_app.progressbar_search_photos.emit()

        collections = [
            os.path.join(cnf.coll_folder, i)
            for i in os.listdir(cnf.coll_folder)
            if os.path.isdir(os.path.join(cnf.coll_folder, i))
            and i not in cnf.stop_colls
            ]

        if not collections:
            collections = [cnf.coll_folder]

        ln_colls = len(collections)
        step_value = 50 if ln_colls == 0 else 50 / ln_colls

        for collection_walk in collections:
            gui_signals_app.progressbar_value.emit(step_value)

            if not Manager.flag:
                return

            for root, _, files in os.walk(top=collection_walk):

                if not Manager.flag:
                    return

                for file in files:

                    if not Manager.flag:
                        return

                    if file.endswith(Manager.jpg_exsts):
                        
                        src = os.path.join(root, file)
                        file_stats = os.stat(path=src)

                        self[src] = (
                            int(file_stats.st_size),
                            int(file_stats.st_birthtime),
                            int(file_stats.st_mtime)
                            )

                    elif file.endswith(Manager.tiff_exsts):
                        cnf.tiff_images.add(os.path.join(root, file))


class DbImages(dict):
    def __init__(self):
        super().__init__()
        self.run()

    def run(self) -> dict[Literal["img path: list of ints"]]:
        q = sqlalchemy.select(ThumbsMd.src, ThumbsMd.size, ThumbsMd.created,
                              ThumbsMd.modified)

        session = Dbase.get_session()
        try:
            res = session.execute(q).fetchall()
        finally:
            session.close()

        self.update({i[0]: i[1:] for i in res})


class ComparedImages(dict):
    def __init__(self, finder_images: dict, db_images: dict):

        super().__init__({"insert": {}, "update": {}, "delete": {}})

        for db_src, db_stats in db_images.items():

            if not Manager.flag:
                return

            finder_stats = finder_images.get(db_src)

            if not finder_stats:
                self["delete"][db_src] = db_stats

        for finder_src, finder_stats in finder_images.items():

            if not Manager.flag:
                return

            db_stats = db_images.get(finder_src)

            if not db_stats:
                self["insert"][finder_src] = finder_stats

            if db_stats and finder_stats != db_stats:
                self["update"][finder_src] = finder_stats


class SummaryScan:
    def __init__(self):
        super().__init__()
        finder_images = FinderImages()
        db_images = DbImages()

        if not finder_images:
            return

        self.images = ComparedImages(finder_images, db_images)
        ln_images = len(self.images["insert"]) + len(self.images["update"])
        self.step_value = 50 if ln_images == 0 else 50 / ln_images

        if self.images["delete"]:
            self.delete_db()

        if self.images["update"]:
            self.update_db()

        if self.images["insert"]:
            self.insert_db()

    def create_values(self, data: Dict[str, tuple]) -> List[Dict]:
        values = []

        for src, (size, created, modified) in data.items():
            gui_signals_app.progressbar_value.emit(self.step_value)

            if not Manager.flag:
                return

            try:
                obj = {
                    "img150": BytesThumb(src).getvalue(),
                    "src": src,
                    "size": size,
                    "created": created,
                    "modified": modified,
                    "collection": MainUtils.get_coll_name(src),
                    }

                values.append(obj)

            except FileNotFoundError:
                print(traceback.format_exc())
                utils_signals_app.scaner_err.emit()
                Manager.flag = False
                return

            except Exception as e:
                obj = {"img150": UndefBytesThumb().getvalue(),
                        "src": src,
                        "size": 666,
                        "created": 666,
                        "modified":666,
                        "collection": "Errors",
                        }

                values.append(obj)
        
        return values

    def insert_db(self):
        gui_signals_app.progressbar_add_photos.emit()
        limit: int = 10
        data: dict = self.images["insert"]
        data_keys: list = list(data.keys())

        chunks: List[Dict[str, tuple]]
        chunks = [
            {key: data[key] for key in data_keys[i:i + limit]}
            for i in range(0, len(data), limit)
            if Manager.flag
            ]

        for chunk in chunks:
            chunk: Dict[str, tuple]
            values: List[Dict] = self.create_values(chunk)

            if not Manager.flag:
                return

            if not values:
                return

            queries = List[Query]
            queries = [
                sqlalchemy
                    .insert(ThumbsMd)
                    .values({
                        "img150": i["img150"],
                        "src": i["src"],
                        "size": i["size"],
                        "created": i["created"],
                        "modified": i["modified"],
                        "collection": i["collection"],
                        })
                for i in values
                ]

            try:
                session = Dbase.get_session()

                for query in  queries:
                    session.execute(query)

                session.commit()
                session.close()
                gui_signals_app.reload_thumbnails.emit()
                gui_signals_app.reload_menu.emit()

            except Exception as e:
                print(f"Error occurred: {e}")
                session.rollback()

            finally:
                session.close()

    def update_db(self):
        limit: int = 10
        data: dict = self.images["update"]
        data_keys: list = list(data.keys())

        chunks: List[Dict[str, tuple]]
        chunks = [
            {key: data[key] for key in data_keys[i:i + limit]}
            for i in range(0, len(data), limit)
            if Manager.flag
            ]

        for chunk in chunks:
            chunk: Dict[str, tuple]
            values: List[Dict] = self.create_values(chunk)

            if not Manager.flag:
                return

            if not values:
                return

            queries = List[Query]
            queries = [
                sqlalchemy
                    .update(ThumbsMd)
                    .values({
                        "img150": i["img150"],
                        "size": i["size"],
                        "created": i["created"],
                        "modified": i["modified"]
                        })
                    .where(ThumbsMd.src==i["src"])
                for i in values
                ]

            try:
                session = Dbase.get_session()

                for query in  queries:
                    session.execute(query)

                session.commit()
                session.close()
                gui_signals_app.reload_thumbnails.emit()
                gui_signals_app.reload_menu.emit()

            except Exception as e:
                print(f"Error occurred: {e}")
                session.rollback()

            finally:
                session.close()

    def delete_db(self):
        gui_signals_app.progressbar_del_photos.emit()

        queries = List[Query]
        queries = [
            sqlalchemy.delete(ThumbsMd).where(ThumbsMd.src==i)
            for i in self.images["delete"]
            if Manager.flag
            ]

        limit: int = 200
        chunks: List[List]
        chunks = [
            queries[i:i+limit]
            for i in range(0, len(queries), limit)
            if Manager.flag
            ]

        for chunk in chunks:
            chunk: List[Query]

            if not Manager.flag:
                return

            try:
                session = Dbase.get_session()

                for query in chunk:
                    session.execute(query)

                session.commit()
                session.close()
                gui_signals_app.reload_thumbnails.emit()
                gui_signals_app.reload_menu.emit()

            except Exception as e:
                print(f"Error occurred: {e}")
                session.rollback()

            finally:
                session.close()


class ScanerBaseClass(ABC):
    @abstractmethod
    def scaner_actions(self):
        ...

    @abstractmethod
    def run(self):
        ...


class Scaner(ScanerBaseClass):
    def __init__(self):
        super().__init__()

    def scaner_actions(self):
        Manager.flag = True
        gui_signals_app.progressbar_show.emit()

        SummaryScan()
        NonExistCollRemover()
        Dbase.vacuum()
        Dbase.cleanup_engine()

        Manager.flag = True
        gui_signals_app.progressbar_hide.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

    def run(self):
        try:
            self.scaner_actions()
        except Exception:
            gui_signals_app.progressbar_hide.emit()
            utils_signals_app.scaner_err.emit()
            print(traceback.format_exc())


class ScanerThread(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        self.scaner = Scaner()
        self.scaner.run()
