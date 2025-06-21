import gc
import os
from time import sleep

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray

from cfg import Static, ThumbData
from database import THUMBS, ClmNames, Dbase
from lang import Lang
from main_folder import MainFolder
from signals import SignalsApp

from .utils import Utils

"""
Важно:
FinderImages собирает все изображения в main_folder,
которые будут сравниваться со всеми изображениями из DbImages.
и если FinderImages будет прерван каким-либо образом,
то будет сравнение всех изображений из DbImages только с частью
изображений FinderImages, а остальные будут считаться удаленными.
Чтобы избежать этого, у нас есть флаг can_scan в ScanHelper.
"""


# это описательный класс, чтобы не импортировать его из tasks с круговым импортом
# данный класс передается в некоторые классы в этом файле из файла tasks
class StopFlag:
    def should_run(self) -> bool: ...
    def set_should_run(self, value: bool): ...


class ScanHelper:
    @classmethod
    def progressbar_text(cls, text: str):
        try:
            SignalsApp.instance.progressbar_text.emit(text)
        except RuntimeError as e:
            pass

    @classmethod
    def reload_gui(cls):
        try:
            SignalsApp.instance.menu_left_cmd.emit("reload")
            SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        except RuntimeError as e:
            Utils.print_error(e)


class FinderImages:
    def __init__(self, main_folder: MainFolder, stop_flag: StopFlag):
        """
        run() to start
        """
        super().__init__()
        self.main_folder = main_folder
        self.stop_flag = stop_flag

    def run(self) -> list | None:
        """
        Возвращает все изображения из MainFolder    
        [(img_path, size, birth_time, mod_time), ...]
        Если не найдено ни одного изображения, вернет None и установит
        ScanHelper.can_scan на False
        ---     
        При любой неизвестной ошибке ScanHelper.can_scan установит на False,     
        Чтобы последующие действия не привели к массовому удалению фотографий.      
        Смотри сообщение в начале файла.
        Возвращает None
        """
        try:
            collections = self.get_main_folder_subdirs()
            finder_images = self.process_subdirs(collections)
            if finder_images:
                return finder_images
            else:
                self.stop_flag.set_should_run(False)
                return None
        except Exception as e:
            self.stop_flag.set_should_run(False)
            return None

    def get_main_folder_subdirs(self) -> list[str]:
        """
        Возвращает список подпапок MainFolder и путь MainFolder.    
        То есть для последующего сканирования у нас будет список:   
        [/path/to/MainFolder/sub_dir, ..., /path/to/MainFolder]     
        """
        collections = []
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
        return collections

    def process_subdirs(self, subdirs: list[str]) -> list:
        """
        Возвращает все изображения из MainFolder    
        [(img_path, size, birth_time, mod_time), ...]   
        """
        finder_images = []
        subrirs_count = len(subdirs)

        for index, subdir in enumerate(subdirs[:-1], start=1):
            progress_text = self.get_progress_text(index, subrirs_count)
            ScanHelper.progressbar_text(progress_text)
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
                    if not self.stop_flag.should_run():
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
        ScanHelper.progressbar_text("")
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

    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder, stop_flag: StopFlag):
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
        self.stop_flag = stop_flag

    def run(self) -> tuple[list, list]:
        """
        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        """
        if not self.stop_flag.should_run():
            return ([], [])
        del_items = self.run_del_items()
        new_items = self.run_new_items()
        ScanHelper.progressbar_text("")
        return del_items, new_items

    def progressbar_text(self, text: str, x: int, total: int):
        """
        text: `Lang.adding`, `Lang.deleting`
        x: item of `enumerate`
        total: `len`
        """
        main_folder = self.main_folder.name.capitalize()
        t = f"{main_folder}: {text.lower()} {x} {Lang.from_} {total}"
        ScanHelper.progressbar_text(t)

    def run_del_items(self):
        new_del_items = []
        total = len(self.del_items)
        for x, rel_thumb_path in enumerate(self.del_items, start=1):
            if not self.stop_flag.should_run():
                break
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
            ScanHelper.reload_gui()
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
        total = len(self.new_items)
        for x, (img_path, size, birth, mod) in enumerate(self.new_items, start=1):
            if not self.stop_flag.should_run():
                break
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
            ScanHelper.reload_gui()
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
                ScanHelper.progressbar_text(t)
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





        

# class ScanerShedule(QObject):
#     def __init__(self):
#         super().__init__()

#         self.wait_timer = QTimer(self)
#         self.wait_timer.setSingleShot(True)
#         self.wait_timer.timeout.connect(self.start)

#         self.wait_sec = 30000
#         self.scaner_thread = None

#     def start(self):
#         self.wait_timer.stop()

#         if self.scaner_thread:
#             print("prev scan not finished, wait", self.wait_sec//1000, "sec")
#             self.wait_timer.start(self.wait_sec)
#             return

#         avaibility = False

#         for main_folder in MainFolder.list_:
#             if main_folder.is_available():
#                 avaibility = True
    
#         if not avaibility:
#             print("scaner no smb, wait", self.wait_sec//1000, "sec")
#             self.wait_timer.start(self.wait_sec)

#         else:
#             self.scaner_thread = ScanerTask()
#             self.scaner_thread.signals_.finished_.connect(self.after_scan)
#             UThreadPool.start(self.scaner_thread)

#     def stop(self):
#         print("scaner manualy stoped.")
#         ScanerTools.can_scan = False
#         self.wait_timer.stop()

#     def after_scan(self):
#         print("scaner finished, new scan in", JsonData.scaner_minutes, "minutes")
#         self.scaner_thread = None
#         self.wait_timer.start(JsonData.scaner_minutes * 60 * 1000)
#         Dbase.vacuum()
#         ScanerTools.progressbar_text("")


# class Scaner:
#     app: ScanerShedule = None

#     @classmethod
#     def init(cls):
#         cls.app = ScanerShedule()

#     @classmethod
#     def start(cls):
#         cls.app.start()

#     @classmethod
#     def stop(cls):
#         cls.app.stop()