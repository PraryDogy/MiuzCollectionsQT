import gc
import os
from time import sleep
import gc
import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from cfg import JsonData, Static, ThumbData
from database import THUMBS, ClmNames, Dbase
from lang import Lang
from main_folder import MainFolder
from signals import SignalsApp
from utils.tasks import URunnable, UThreadPool

from .utils import Utils


class ScanerTools:
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
        collections = self.get_subdirs()
        if collections:
            return self.process_subdirs(collections)
        else:
            return None

    def get_subdirs(self) -> list[str]:
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

    def process_subdirs(self, subdirs: list[str]) -> list[tuple[str, int, int, int]]:
        finder_images = []
        subrirs_count = len(subdirs)

        for index, subdir in enumerate(subdirs[:-1], start=1):
            progress_text = self.get_progress_text(index, subrirs_count)
            ScanerTools.progressbar_text(progress_text)
            try:
                walked_images = self.walk_subdir(subdir)
                finder_images.extend(walked_images)
            except TypeError as e:
                Utils.print_error(e)

        # Сканируем корневую папку без рекурсии в подпапки,
        # чтобы найти изображения непосредственно в корневой папке.
        # В функции get_collections корневая папка добавляется в конец списка коллекций.
        for i in os.scandir(subdirs[-1]):
            if i.name.endswith(Static.ext_all):
                try:
                    file_data = self.get_file_data(i)
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

    def walk_subdir(self, coll: str) -> list[tuple[str, int, int, int]]:
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
                    elif entry.name.endswith(Static.ext_all):
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
            THUMBS.c.short_hash, # relative thumb path
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
        main_folder_path = self.main_folder.get_current_path()
        return {
            rel_thumb_path: (
                Utils.get_img_path(main_folder_path, rel_img_path),
                size,
                birth,
                mod
            )
            for rel_thumb_path, rel_img_path, size, birth, mod in res
        }


class Compator:
    def __init__(self, finder_images: dict, db_images: dict):
        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def run(self):
        finder_set = set(self.finder_images)
        db_values = set(self.db_images.values())
        del_items = [k for k, v in self.db_images.items() if v not in finder_set]
        ins_items = list(finder_set - db_values)
        return del_items, ins_items


class FileUpdater:
    sleep_count = 0.1

    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder):
        """
        Удаляет thumbs из hashdir   
        Добавляет thumbs в hashdir  
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        run() to start  
        """
        super().__init__()
        self.del_items = del_items
        self.new_items = new_items
        self.main_folder = main_folder

    def run(self) -> tuple[list, list]:
        """
        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        """
        del_items = self.run_del_items()
        new_items = self.run_new_items()
        ScanerTools.progressbar_text("")
        return del_items, new_items

    def progressbar_text(self, text: str, x: int, total: int):
        """
        text: `Lang.adding`, `Lang.deleting`
        x: item of `enumerate`
        total: `len`
        """
        main_folder = self.main_folder.name.capitalize()
        t = f"{main_folder}: {text.lower()} {x} {Lang.from_} {total}"
        ScanerTools.progressbar_text(t)

    def run_del_items(self):
        new_del_items = []
        total = len(self.del_items)
        for x, rel_thumb_path in enumerate(self.del_items, start=1):
            if not ScanerTools.can_scan:
                return
            thumb_path = Utils.get_thumb_path(rel_thumb_path)
            if os.path.exists(thumb_path):
                self.progressbar_text(Lang.deleting, x, total)
                try:
                    os.remove(thumb_path)
                    folder = os.path.dirname(thumb_path)
                    if not os.listdir(folder):
                        os.rmdir(folder)
                    new_del_items.append(rel_thumb_path)
                    sleep(self.sleep_count)
                except Exception as e:
                    Utils.print_error(e)
                    continue
        if total > 0:
            ScanerTools.reload_gui()
        return new_del_items

    def create_thumb(self, img_path: str) -> ndarray | None:
        img = Utils.read_image(img_path)
        thumb = Utils.fit_to_thumb(img, ThumbData.DB_PIXMAP_SIZE)
        del img
        gc.collect()
        if isinstance(thumb, ndarray):
            return thumb
        else:
            return None

    def run_new_items(self):
        new_new_items = []
        if self.new_items is None:
            ScanerTools.can_scan = False
            return
        total = len(self.new_items)
        for x, (img_path, size, birth, mod) in enumerate(self.new_items, start=1):
            if not ScanerTools.can_scan:
                return
            self.progressbar_text(Lang.adding, x, total)
            try:
                thumb = self.create_thumb(img_path)
                thumb_path = Utils.create_thumb_path(img_path)
                Utils.write_thumb(thumb_path, thumb)
                new_new_items.append((img_path, size, birth, mod))
                sleep(self.sleep_count)
            except Exception as e:
                Utils.print_error(e)
                continue
        if total > 0:
            ScanerTools.reload_gui()
        return new_new_items


class DbUpdater:
    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder):
        """
        Удаляет записи thumbs из бд   
        Добавляет записи thumbs в бд
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]      
        run() to start  
        """
        super().__init__()
        self.main_folder = main_folder
        self.del_items = del_items
        self.new_items = new_items

    def run(self):
        self.run_del_items()
        self.run_new_items()

    def run_del_items(self):
        conn = Dbase.engine.connect()
        for rel_thumb_path in self.del_items:
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
            q = q.where(THUMBS.c.short_hash==rel_thumb_path)
            q = q.where(THUMBS.c.brand==self.main_folder.name)
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
        try:
            conn.commit()
        except Exception as e:
            Utils.print_error(e)
            conn.rollback()
        conn.close()

    def run_new_items(self):
        conn = Dbase.engine.connect()
        for img_path, size, birth, mod in self.new_items:
            # не удалять
            if not ScanerTools.can_scan:
                return
            small_img_path = Utils.create_thumb_path(img_path)
            short_img_path = Utils.get_rel_img_path(self.main_folder.get_current_path(), img_path)
            rel_thumb_path = Utils.get_rel_thumb_path(small_img_path)
            coll_name = Utils.get_coll_name(self.main_folder.get_current_path(), img_path)
            values = {
                ClmNames.SHORT_SRC: short_img_path,
                ClmNames.SHORT_HASH: rel_thumb_path,
                ClmNames.SIZE: size,
                ClmNames.BIRTH: birth,
                ClmNames.MOD: mod,
                ClmNames.RESOL: "",
                ClmNames.COLL: coll_name,
                ClmNames.FAV: 0,
                ClmNames.BRAND: self.main_folder.name
            }
            stmt = sqlalchemy.insert(THUMBS).values(**values) 
            try:
                conn.execute(stmt)
            # overflow error бывает прозникает когда пишет
            # python integer too large to insert db
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
                Utils.print_error(e)
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                Utils.print_error(e)
                conn.rollback()
                break
        try:
            conn.commit()
        except Exception as e:
            Utils.print_error(e)
            conn.rollback()
        conn.close()


class MainFolderRemover:
    def __init__(self):
        """
        Сверяет список экземпляров класса MainFolder в бд (THUMBS.c.brand)     
        со списком MainFolder в приложении.     
        Удаляет весь контент MainFolder, если MainFolder больще нет в бд:   
        - изображения thumbs из hashdir в ApplicationSupport    
        - записи в базе данных

        Вызови run для работы
        """
        super().__init__()
        self.conn = Dbase.engine.connect()

    def run(self):
        q = sqlalchemy.select(THUMBS.c.brand).distinct()
        res = self.conn.execute(q).fetchall()
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
        for main_folder in removed_main_folders:
            rows = self.get_rows(main_folder)
            self.remove_images(rows)
            self.remove_rows(rows)

        self.conn.close()
        
    def get_rows(self, main_folder: MainFolder):
        q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.short_hash) #rel thumb path
        q = q.where(THUMBS.c.brand == main_folder.name)
        res = self.conn.execute(q).fetchall()
        res = [
            (id_, Utils.get_thumb_path(rel_thumb_path))
            for id_, rel_thumb_path in res
        ]
        return res

    def remove_images(self, rows: list):
        """
        rows: [(row id int, thumb path), ...]
        """
        total = len(rows)
        for x, (id_, image_path) in enumerate(rows):
            try:
                os.remove(image_path)
                folder = os.path.dirname(image_path)
                if not os.listdir(folder):
                    os.rmdir(folder)
                t = f"{Lang.deleting}: {x} {Lang.from_} {total}"
                ScanerTools.progressbar_text(t)
            except Exception as e:
                Utils.print_error(e)
                continue

    def remove_rows(self, rows: list):
        """
        rows: [(row id int, thumb path), ...]
        """
        for id_, thumb_path in rows:
            q = sqlalchemy.delete(THUMBS)
            q = q.where(THUMBS.c.id == id_)

            try:
                self.conn.execute(q)
            except (sqlalchemy.exc.IntegrityError, OverflowError) as e:
                Utils.print_error(e)
                self.conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                Utils.print_error(e)
                self.conn.rollback()
                break
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            Utils.print_error(e)


class Signals(QObject):
    finished_ = pyqtSignal()


class ScanerThread(URunnable):
    def __init__(self):
        super().__init__()
        self.signals_ = Signals()

    def task(self):
        for main_folder in MainFolder.list_:
            if main_folder.is_available():
                self.main_folder_scan(main_folder)
                print("scaner started", main_folder.name)

    def main_folder_scan(self, main_folder: MainFolder):
        ScanerTools.can_scan = True
        main_folder_remover = MainFolderRemover()
        main_folder_remover.run()
        finder_images = FinderImages(main_folder)
        finder_images = finder_images.run()
        gc.collect()
        if isinstance(finder_images, list):
            db_images = DbImages(main_folder)
            db_images = db_images.run()
            compator = Compator(finder_images, db_images)
            del_items, new_items = compator.run()
            file_updater = FileUpdater(del_items, new_items, main_folder)
            del_items, new_items = file_updater.run()
            db_updater = DbUpdater(del_items, new_items, main_folder)
            db_updater.run()
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
            if main_folder.is_available():
                avaibility = True
    
        if not avaibility:
            print("scaner no smb, wait", self.wait_sec//1000, "sec")
            self.wait_timer.start(self.wait_sec)

        else:
            self.scaner_thread = ScanerThread()
            self.scaner_thread.signals_.finished_.connect(self.after_scan)
            UThreadPool.start(self.scaner_thread)

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