import gc
import os

import sqlalchemy
import sqlalchemy.exc
from numpy import ndarray
from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Static, ThumbData
from system.database import THUMBS, ClmNames, Dbase
from system.lang import Lang
from system.main_folder import MainFolder

from ..utils import ImgUtils, TaskState, ThumbUtils, MainUtils


class FinderImages(QObject):
    progress_text = pyqtSignal(str)

    def __init__(self, main_folder: MainFolder, task_state: TaskState):
        """
        Запуск: run()   
        Сигналы: progress_text(str)     

        Возвращает все изображения, найденные в MainFolder    
        [(img_path, size, birth_time, mod_time), ...]   
        Если не найдено ни одного изображения, вернет None и установит
        TaskState.should_run на False

        При любой неизвестной ошибке TaskState.should_run будет установлен на False,     
        чтобы последующие действия не привели к массовому удалению фотографий.      
        Возвращает None
        """
        super().__init__()
        self.main_folder = main_folder
        self.task_state = task_state

    def run(self) -> list | None:
        try:
            collections = self.collect_scan_dirs()
            finder_images = self.process_subdirs(collections)
            if finder_images:
                return finder_images
            else:
                self.task_state.set_should_run(False)
                return None
        except Exception as e:
            MainUtils.print_error()
            self.task_state.set_should_run(False)
            return None

    def collect_scan_dirs(self) -> list[str]:
        """
        Возвращает список путей для сканирования:
        - все подпапки текущей директории MainFolder, кроме тех, что в stop_list
        - сам путь MainFolder в конце списка
        """
        collections = []
        for item in os.scandir(self.main_folder.get_current_path()):
            if item.is_dir() and item.name not in self.main_folder.stop_list:
                collections.append(item.path)
        collections.append(self.main_folder.get_current_path())
        return collections

    def process_subdirs(self, subdirs: list[str]) -> list:
        """
        Обрабатывает переданные директории и собирает информацию об изображениях.

        Возвращает список кортежей с данными файлов:
        [(img_path, size, birth_time, mod_time), ...]

        - Все подпапки (кроме последней) сканируются рекурсивно.
        - Последняя папка (корневая) сканируется только на наличие изображений в ней самой.
        - Прогресс отображается через сигнал progress_text.
        - Если task_state.should_run() возвращает False, процесс прерывается.
        """
        finder_images = []
        *subdirs, rootdir = subdirs
        subrirs_count = len(subdirs)

        for index, subdir in enumerate(subdirs, start=1):
            if not self.task_state.should_run():
                return finder_images
            text = self.get_progress_text(index, subrirs_count)
            self.progress_text.emit(text)
            try:
                walked_images = self.walk_subdir(subdir)
                finder_images.extend(walked_images)
            except Exception as e:
                MainUtils.print_error()
                continue

        for i in os.scandir(rootdir):
            if i.name.endswith(Static.ext_all):
                try:
                    file_data = self.get_file_data(i)
                    finder_images.append(file_data)
                except Exception as e:
                    MainUtils.print_error()
                    continue
        return finder_images

    def get_progress_text(self, current: int, total: int) -> str:
        """
        Формирует строку для отображения прогресса обработки:
        Пример: "Miuz (MainFolder.name): коллекция 3 из 10"
        """
        main_folder = self.main_folder.name.capitalize()
        collection_name = Lang.collection
        return f"{main_folder}: {collection_name.lower()} {current} {Lang.from_} {total}"

    def walk_subdir(self, subdir: str) -> list[tuple]:
        """
        Рекурсивно обходит поддиректории и собирает данные об изображениях.

        Возвращает:
        - Список кортежей: [(путь, размер, дата_создания, дата_модификации), ...]
        - Прерывается, если task_state.should_run() вернёт False.
        """
        finder_images = []
        stack = [subdir]
        while stack:
            current_dir = stack.pop()
            for entry in os.scandir(current_dir):
                if not self.task_state.should_run():
                    return finder_images
                if entry.is_dir():
                    stack.append(entry.path)
                elif entry.name.endswith(Static.ext_all):
                    finder_images.append(self.get_file_data(entry))
        return finder_images

    def get_file_data(self, entry: os.DirEntry) -> tuple:
        """
        Возвращает информацию о файле: (путь, размер, время создания, время изменения).
        """
        stats = entry.stat()
        return (
            entry.path,
            int(stats.st_size),
            int(stats.st_birthtime),
            int(stats.st_mtime),
        )


class DbImages(QObject):
    progress_text = pyqtSignal(str)

    def __init__(self, main_folder: MainFolder):
        """
        Запуск: run()   
        Сигналы: progress_text(str)     

        Возвращает записи из бд, относящиеся к MainFolder:  
        {rel thumb path: (img path, size, birth time, mod time), ...}   
        """
        super().__init__()
        self.main_folder = main_folder

    def run(self) -> dict:
        self.progress_text.emit("")
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
                MainUtils.get_abs_path(main_folder_path, rel_img_path),
                size,
                birth,
                mod
            )
            for rel_thumb_path, rel_img_path, size, birth, mod in res
        }


class Compator:
    def __init__(self, finder_images: dict, db_images: dict):
        """
        Сравнивает данные об изображениях FinderImages и DbImages.  
        del_items: нет в FinderImages и есть в DbImages     
        new_items: есть в FinderImages и нет в DbImages

        Принимает:      
        finder_images: [(img_path, size, birth_time, mod_time), ...]    
        db_images:  {rel thumb path: (img path, size, birth time, mod time), ...}

        Возвращает:
        del_items: [rel thumb path, ...]    
        new_items: [(img_path, size, birth, mod), ...]
        """
        super().__init__()
        self.finder_images = finder_images
        self.db_images = db_images

    def run(self):
        finder_set = set(self.finder_images)
        db_values = set(self.db_images.values())
        del_items = [k for k, v in self.db_images.items() if v not in finder_set]
        ins_items = list(finder_set - db_values)
        return del_items, ins_items


class Inspector(QObject):
    def __init__(self, del_items: list, main_folder: MainFolder):
        """
        del_items: [rel thumb path, ...]

        Этот класс выполняет проверку безопасности перед удалением данных.
        Метод is_remove_all() инициирует сравнение между количеством записей
        в БД и количеством удаляемых миниатюр, связанных с MainFolder.

        Если количество удаляемых элементов совпадает с количеством записей в базе,
        это может свидетельствовать о потенциальной ошибке в логике сканера,
        приводящей к попытке удалить все данные, связанные с MainFolder.
        В таком случае, операция считается подозрительной и может быть заблокирована
        как мера предосторожности.
        """
        super().__init__()
        self.del_items = del_items
        self.main_folder = main_folder
    
    def is_remove_all(self):
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(sqlalchemy.func.count())
        q = q.where(THUMBS.c.brand == self.main_folder.name)
        result = conn.execute(q).scalar()
        conn.close()
        if len(self.del_items) == result and len(self.del_items) != 0:
            return True
        return None


class HashdirUpdater(QObject):
    progress_text = pyqtSignal(str)

    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder, task_state: TaskState):
        """
        Удаляет thumbs из hashdir, добавляет thumbs в hashdir.  
        Запуск: run()   
        Сигналы: progress_text(str)
        
        Принимает:  
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  


        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        """
        super().__init__()
        self.del_items = del_items
        self.new_items = new_items
        self.main_folder = main_folder
        self.task_state = task_state

    def run(self) -> tuple[list, list]:
        """
        Возвращает:     
        del_items: [rel_thumb_path, ...]    
        new_items: [(img_path, size, birth, mod), ...]  
        """
        if not self.task_state.should_run():
            return ([], [])
        del_items = self.run_del_items()
        new_items = self.run_new_items()
        self.progress_text.emit("")
        return del_items, new_items

    def progressbar_text(self, text: str, x: int, total: int):
        """
        text: `Lang.adding`, `Lang.deleting`
        x: item of `enumerate`
        total: `len`
        """
        main_folder = self.main_folder.name.capitalize()
        t = f"{main_folder}: {text.lower()} {x} {Lang.from_} {total}"
        self.progress_text.emit(t)

    def run_del_items(self):
        new_del_items = []
        total = len(self.del_items)
        for x, rel_thumb_path in enumerate(self.del_items, start=1):
            if not self.task_state.should_run():
                break
            thumb_path = ThumbUtils.get_thumb_path(rel_thumb_path)
            if os.path.exists(thumb_path):
                self.progressbar_text(Lang.deleting, x, total)
                try:
                    os.remove(thumb_path)
                    folder = os.path.dirname(thumb_path)
                    if not os.listdir(folder):
                        os.rmdir(folder)
                    new_del_items.append(rel_thumb_path)
                except Exception as e:
                    MainUtils.print_error()
                    continue
        return new_del_items

    def create_thumb(self, img_path: str) -> ndarray | None:
        img = ImgUtils.read_image(img_path)
        thumb = ThumbUtils.fit_to_thumb(img, ThumbData.DB_PIXMAP_SIZE)
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
            if not self.task_state.should_run():
                break
            self.progressbar_text(Lang.adding, x, total)
            try:
                thumb = self.create_thumb(img_path)
                thumb_path = ThumbUtils.create_thumb_path(img_path)
                ThumbUtils.write_thumb(thumb_path, thumb)
                new_new_items.append((img_path, size, birth, mod))
            except Exception as e:
                MainUtils.print_error()
                continue
        return new_new_items


class DbUpdater(QObject):
    reload_gui = pyqtSignal()

    def __init__(self, del_items: list, new_items: list, main_folder: MainFolder):
        """
        Удаляет записи thumbs из бд, добавляет записи thumbs в бд.  
        Запуск: run()  
        Сигналы: reload_gui()

        Принимает:  
        - del_items: [rel_thumb_path, ...]       
        - new_items: [(img_path, size, birth, mod), ...]          
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
                MainUtils.print_error()
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                MainUtils.print_error()
                conn.rollback()
                conn.close()
                return None
        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()
        conn.close()

        if len(self.del_items) > 0:
            self.reload_gui.emit()

    def run_new_items(self):
        conn = Dbase.engine.connect()
        for img_path, size, birth, mod in self.new_items:
            small_img_path = ThumbUtils.create_thumb_path(img_path)
            short_img_path = MainUtils.get_rel_path(self.main_folder.get_current_path(), img_path)
            rel_thumb_path = ThumbUtils.get_rel_thumb_path(small_img_path)
            coll_name = MainUtils.get_coll_name(self.main_folder.get_current_path(), img_path)
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
                MainUtils.print_error()
                conn.rollback()
                continue
            except sqlalchemy.exc.OperationalError as e:
                MainUtils.print_error()
                conn.rollback()
                break
        try:
            conn.commit()
        except Exception as e:
            MainUtils.print_error()
            conn.rollback()
        conn.close()

        if len(self.new_items) > 0:
            self.reload_gui.emit()


class MainFolderRemover(QObject):
    progress_text = pyqtSignal(str)

    def __init__(self):
        """
        Запуск: run()   
        Сигналы: progress_text(str)

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
        db_main_folders = self.conn.execute(q).scalars().all()
        app_main_folders = [i.name for i in MainFolder.list_]
        del_main_folders = [i for i in db_main_folders if i not in app_main_folders]
        for i in del_main_folders:
            rows = self.get_rows(i)
            self.remove_images(rows)
            self.remove_rows(rows)
        self.conn.close()
        
    def get_rows(self, main_folder_name):
        q = sqlalchemy.select(THUMBS.c.id, THUMBS.c.short_hash) #rel thumb path
        q = q.where(THUMBS.c.brand == main_folder_name)
        res = self.conn.execute(q).fetchall()
        res = [
            (id_, ThumbUtils.get_thumb_path(rel_thumb_path))
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
                t = f"{Lang.deleting}: {x} {Lang.from_} {total}"
                self.progress_text.emit(t)

                if os.path.exists(image_path):
                    os.remove(image_path)
                folder = os.path.dirname(image_path)
                if os.path.exists(folder) and not os.listdir(folder):
                    os.rmdir(folder)

            except Exception as e:
                MainUtils.print_error()
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
                MainUtils.print_error()
                self.conn.rollback()
                continue

            except sqlalchemy.exc.OperationalError as e:
                MainUtils.print_error()
                self.conn.rollback()
                break
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            MainUtils.print_error()
