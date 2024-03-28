from typing import Dict, List, Query
import traceback
import sqlalchemy

class FinderImages: ...
class DbImages: ...
class ComparedImages: ...
class Manager: ...
class BytesThumb: ...
class MainUtils: ...
class UndefBytesThumb: ...
class ThumbsMd: ...
class Dbase: ...
gui_signals_app = ...
utils_signals_app = ...


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