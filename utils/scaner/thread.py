import os
import traceback
from collections import defaultdict
from time import sleep
from typing import Dict, List, Literal

import sqlalchemy
from PyQt5.QtCore import QThread, pyqtSignal
from sqlalchemy.orm import Query

from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app, utils_signals_app

from ..image_utils import BytesThumb, UndefBytesThumb
from ..main_utils import MainUtils


class Shared:
    flag = True


class Migrate:
    def __init__(self):
        sess = Dbase.get_session()

        if cnf.old_coll_folder is None or cnf.coll_folder == cnf.old_coll_folder:
            return
        
        try:
            q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
            res = sess.execute(q).fetchall()
        except Exception as e:
            print("migrate load all rows err", e)
            return
        
        if len(res) == 0:
            return

        new_res = [
            (res_id, src.replace(cnf.old_coll_folder, cnf.coll_folder))
            for res_id, src in res
            ]
        
        for res_id, src in new_res:
            q = (
                sqlalchemy.update(ThumbsMd)
                .values({"src": src})
                .filter(ThumbsMd.id==res_id)
                )
            sess.execute(q)

        try:
            sess.commit()
        except Exception as e:
            print("migrate commit err", e)

        sess.close()
        cnf.old_coll_folder = None
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()
        utils_signals_app.migrate_finished.emit()


class TrashRemover:
    def __init__(self):
        coll_folder = os.sep + cnf.coll_folder.strip(os.sep) + os.sep

        session = Dbase.get_session()

        q = (sqlalchemy.select(ThumbsMd.src)
            .filter(ThumbsMd.src.not_like(f"%{coll_folder}%")))

        try:
            trash_img = session.execute(q).first()
        
        except Exception as e:
            print(e)
            return

        if trash_img:

            q = (sqlalchemy.delete(ThumbsMd)
                .filter(ThumbsMd.src.not_like(f"%{coll_folder}%")))

            try:
                session.execute(q)
                session.commit()
            except Exception as e:
                print(e)
                return
            finally:
                session.close()


class DubFinder:
    def __init__(self):
        q = sqlalchemy.select(ThumbsMd.id, ThumbsMd.src)
        conn = Dbase.get_session()
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


class FinderImages(dict):
    def __init__(self):
        super().__init__()

        try:
            self.run()

        except (OSError, FileNotFoundError):
            print(traceback.format_exc())
            Shared.flag = False

        if not self:
            Shared.flag = False

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
        step_value = 60 if ln_colls == 0 else 60 / ln_colls

        for collection_walk in collections:
            try:
                gui_signals_app.progressbar_value.emit(step_value)
            except Exception as e:
                print(e)

            for root, _, files in os.walk(top=collection_walk):

                if not Shared.flag:
                    return

                for file in files:

                    if not os.path.exists(cnf.coll_folder):
                        Shared.flag = False
                        return

                    if file.endswith((".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG")):
                        
                        src = os.path.join(root, file)
                        file_stats = os.stat(path=src)

                        self[src] = (
                            int(file_stats.st_size),
                            int(file_stats.st_birthtime),
                            int(file_stats.st_mtime)
                            )

                    elif file.endswith((".tiff", ".TIFF", ".psd", ".PSD", ".psb", ".PSB", ".tif", ".TIF")):
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

            if not Shared.flag:
                return

            finder_stats = finder_images.get(db_src)

            if not finder_stats:
                self["delete"][db_src] = db_stats

        for finder_src, finder_stats in finder_images.items():

            if not Shared.flag:
                return

            db_stats = db_images.get(finder_src)

            if not db_stats:
                self["insert"][finder_src] = finder_stats

            if db_stats and finder_stats != db_stats:
                self["update"][finder_src] = finder_stats


class UpdateDb:
    def __init__(self, images: dict):
        super().__init__()

        try:
            gui_signals_app.progressbar_value.emit(70)
            gui_signals_app.progressbar_del_photos.emit()
        except RuntimeError:
            pass

        if images["delete"]:
            self.delete_db(images["delete"])

        try:
            gui_signals_app.progressbar_value.emit(80)
            gui_signals_app.progressbar_add_photos.emit()
        except RuntimeError:
            pass

        if images["insert"]:
            self.insert_db(images["insert"])

        try:
            gui_signals_app.progressbar_value.emit(90)
        except RuntimeError:
            pass

        if images["update"]:
            self.update_db(images["update"])

    def create_values(self, data: Dict[str, tuple]) -> List[Dict]:
        values = []

        for src, (size, created, modified) in data.items():

            if not Shared.flag:
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
                Shared.flag = False
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

    def insert_db(self, images: dict):
        limit: int = 10
        data_keys: list = list(images.keys())

        chunks: List[Dict[str, tuple]]
        chunks = [
            {key: images[key] for key in data_keys[i:i + limit]}
            for i in range(0, len(images), limit)
            ]

        for chunk in chunks:
            chunk: Dict[str, tuple]
            values: List[Dict] = self.create_values(chunk)

            if not Shared.flag:
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

    def update_db(self, images: dict):
        limit: int = 10
        data_keys: list = list(images.keys())

        chunks: List[Dict[str, tuple]]
        chunks = [
            {key: images[key] for key in data_keys[i:i + limit]}
            for i in range(0, len(images), limit)
            ]

        for chunk in chunks:
            chunk: Dict[str, tuple]
            values: List[Dict] = self.create_values(chunk)

            if not Shared.flag:
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

    def delete_db(self, images: dict):
        queries = List[Query]
        queries = [
            sqlalchemy.delete(ThumbsMd).where(ThumbsMd.src==i)
            for i in images.keys()
            ]

        limit: int = 200
        chunks: List[List]
        chunks = [
            queries[i:i+limit]
            for i in range(0, len(queries), limit)
            ]

        for chunk in chunks:
            chunk: List[Query]

            if not Shared.flag:
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


class Scaner(object):
    def __init__(self):
        super().__init__()

        try:
            Shared.flag = True

            try:
                gui_signals_app.progressbar_show.emit()
            except RuntimeError:
                pass

            self.migrate = Migrate()

            finder_images = FinderImages()
            db_images = DbImages()

            if not finder_images:
                return

            images = ComparedImages(finder_images, db_images)
            self.update_db = UpdateDb(images=images)

            self.trash_remover = TrashRemover()
            self.dub_finder = DubFinder()

            Dbase.vacuum()
            Dbase.cleanup_engine()

            Shared.flag = True

            try:
                gui_signals_app.progressbar_hide.emit()
                gui_signals_app.reload_menu.emit()
                gui_signals_app.reload_thumbnails.emit()
            except RuntimeError:
                pass

        except Exception:

            try:
                gui_signals_app.progressbar_hide.emit()
            except RuntimeError:
                pass

            print(traceback.format_exc())


class ScanerThread(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        self.scaner = Scaner()
        self.finished.emit()
