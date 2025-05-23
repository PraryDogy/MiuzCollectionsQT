import gc
import os
from time import sleep

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from main_folders import MainFolder
from cfg import JsonData, Static, ThumbData
from database import THUMBS, Dbase, ClmNames
from lang import Lang
from signals import SignalsApp

from .utils import URunnable, UThreadPool, Utils


class ScanerTools:
    current_main_folder: MainFolder
    avaiable_main_folders: list[MainFolder] = []
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
                Utils.print_error(e)


class FinderImages:
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder

    def run(self) -> list[tuple[str, int, int, int]] | None:
        """Основной метод для поиска изображений в коллекциях."""
        collections = self.get_collections()
        if collections:
            return self.process_collections(collections)
        else:
            return None

    def get_collections(self) -> list[str]:
        collections = []

        try:
            for item in os.scandir(self.main_folder.get_current_path()):
                if item.is_dir():
                    if item.name not in self.main_folder.stop_list:
                        collections.append(item.path)

            # Добавляем корневую папку в конец списка коллекций (подпапок),
            # чтобы сканер мог найти изображения как в корневой папке,
            # так и в подпапках. Например:
            # - .../root/img.jpg — изображение в корневой папке
            # - .../root/collection/img.jpg — изображение в подпапке
            collections.append(self.main_folder.get_current_path())

        except FileNotFoundError:
            ...

        return collections

    def process_collections(self, collections: list[str]) -> list[tuple[str, int, int, int]]:
        finder_images = []
        total_collections = len(collections)

        for index, collection in enumerate(collections[:-1], start=1):
            
            progress_text = self.get_progress_text(index, total_collections)
            ScanerTools.progressbar_text(progress_text)

            try:
                walked_images = self.walk_collection(collection)
                finder_images.extend(walked_images)

            except TypeError as e:
                Utils.print_error(e)

        # Сканируем корневую папку без рекурсии в подпапки,
        # чтобы найти изображения непосредственно в корневой папке.
        # В функции get_collections корневая папка добавляется в конец списка коллекций.
        for i in os.scandir(collections[-1]):
            if i.name.endswith(Static.IMG_EXT):
                try:
                    file_data = self.get_file_data(entry=i)
                    finder_images.append(file_data)
                except OSError as e:
                    print("scaner > FinderImages > get file data", e)
                    continue

        return finder_images

    def get_progress_text(self, current: int, total: int) -> str:
        """Формирует текст для прогресс-бара."""
        main_folder = self.main_folder.name.capitalize()
        collection_name = Lang.collection
        return f"{main_folder}: {collection_name.lower()} {current} {Lang.from_} {total}"

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
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder

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
        
        q = q.where(THUMBS.c.brand == self.main_folder.name)

        # не забываем относительный путь к изображению преобразовать в полный
        # для сравнения с finder_items
        res = conn.execute(q).fetchall()
        conn.close()
        coll_folder = self.main_folder.get_current_path()

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

    def run(self, finder_images: list, db_images: dict):

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
                Utils.print_error(e)
                conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                Utils.print_error(e)
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

                try:
                    self.progressbar_text(text=Lang.deleting, x=x, total=total)
                    os.remove(full_hash)
                    folder = os.path.dirname(full_hash)
                    if not os.listdir(folder):
                        os.rmdir(folder)
                    sleep(self.sleep_count)
                except Exception as e:
                    Utils.print_error(e)
                    continue

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
        coll_folder = ScanerTools.current_main_folder.current_path
        return {
            ClmNames.SHORT_SRC: Utils.get_short_src(coll_folder, full_src),
            ClmNames.SHORT_HASH: Utils.get_short_hash(full_hash),
            ClmNames.SIZE: size,
            ClmNames.BIRTH: birth,
            ClmNames.MOD: mod,
            ClmNames.RESOL: resol,
            ClmNames.COLL: Utils.get_coll_name(coll_folder, full_src),
            ClmNames.FAV: 0,
            ClmNames.BRAND: ScanerTools.current_main_folder.name
        }

    def create_queries(self, ins_items: list[tuple[str, int, int, int]]):

        res: dict[sqlalchemy.Insert, tuple[str, ndarray]] = {}
        total = len(ins_items)

        for x, (full_src, size, birth, mod) in enumerate(ins_items, start=1):

            # не удалять
            if not ScanerTools.can_scan:
                return

            self.progressbar_text(text=Lang.adding, x=x, total=total)
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
                Utils.print_error(e)
                conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                Utils.print_error(e)
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

        for full_hash, img_array in queries.values():

            # не удалять
            if not ScanerTools.can_scan:
                return

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

        main_folder = ScanerTools.current_main_folder.name.capitalize()
        t = f"{main_folder}: {text.lower()} {x} {Lang.from_} {total}"
        ScanerTools.progressbar_text(t)


class MainFolderRemover:
    """Удаляет изображения из hashdir и записи БД, если MainFolder больше не в списке"""

    @classmethod
    def run(cls):
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(THUMBS.c.brand).distinct()
        res = conn.execute(q).fetchall()
        db_main_folders = [
            i[0]
            for i in res
        ]
        app_main_folders = [
            i.name
            for i in MainFolder.list_
        ]
        removed_main_folders = [
            i
            for i in db_main_folders
            if i not in app_main_folders
        ]

        for i in removed_main_folders:
            rows = cls.get_rows(main_folder_name=i, conn=conn)
            cls.remove_images(rows=rows)
            cls.remove_rows(rows=rows, conn=conn)
    
    @classmethod
    def get_rows(cls, main_folder_name: str, conn: sqlalchemy.Connection):
        q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.short_hash)
        q = q.where(THUMBS.c.brand == main_folder_name)
        res = conn.execute(q).fetchall()
        res = [
            (id_, Utils.get_full_hash(short_hash=short_hash))
            for id_, short_hash in res
        ]
        return res
    
    @classmethod
    def remove_images(cls, rows: list[tuple[int, str]]):
        total = len(rows)

        for x, (id_, image_path) in enumerate(rows):
            try:
                os.remove(image_path)
                folder = os.path.dirname(image_path)
                if not os.listdir(folder):
                    os.rmdir(folder)
                t = f"{Lang.deleting}: {x} {Lang.from_} {total}"
                ScanerTools.progressbar_text(text=t)
            except Exception as e:
                Utils.print_error(e)
                continue

    @classmethod
    def remove_rows(cls, rows: list[tuple[int, str]], conn: sqlalchemy.Connection):
        for id_, image_path in rows:
            q = sqlalchemy.delete(THUMBS)
            q = q.where(THUMBS.c.id == id_)

            try:
                conn.execute(q)
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
                Utils.print_error(e)
                conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                Utils.print_error(e)
                conn.rollback()
                conn.close()
                return None
            
        conn.commit()
        conn.close()

class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class ScanerThread(URunnable):

    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):
        for main_folder in MainFolder.list_:
            if main_folder.is_avaiable():
                self.main_folder_scan(main_folder)
                print("scaner started", main_folder.name)

    def main_folder_scan(self, main_folder: MainFolder):
        ScanerTools.can_scan = True
        MainFolderRemover.run()
        finder_images = FinderImages(main_folder)
        finder_images = finder_images.run()

        if finder_images is not None:
        
            db_images = DbImages(main_folder)
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

        avaibility = False

        for main_folder in MainFolder.list_:
            main_folder.set_current_path()
            if main_folder.is_avaiable():
                avaibility = True
    
        if not avaibility:
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
        cls.app.start()

    @classmethod
    def stop(cls):
        cls.app.stop()