import os
import shutil
from dataclasses import dataclass
from multiprocessing import Queue
from time import sleep

import sqlalchemy

from cfg import Static, cfg
from system.database import ColumnNames, Dbase, Dirs, Thumbs
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import ImgUtils
from system.utils import Utils

from .items import ScanerItem


@dataclass(slots=True)
class DirItem:
    """
    Параметры:
    - rel_path: относительный путь к подкаталогу относительно `Mf.curr_path`.
      Пример:
        - Mf.curr_path = /User/Downloads/parent/folder
        - подкаталог = /User/Downloads/parent/folder/subfolder
        - rel_path = /subfolder
    - mod: дата модификации каталога (os.stat.st_birthtime)
    """
    abs_path: str
    rel_path: str
    mod: int


@dataclass(slots=True)
class ImgItem:
    """
    Параметры:
    - abs_img_path: полный путь до изображения
    - size: размер изображения в байтах
    - birth: os.stat.st_birthtime
    - mod: os.stat.st_mtime
    - rel_thumb_path: путь до миниатюры /hashdir/thumb.jpg
    """
    abs_img_path: str
    size: int
    birth: int
    mod: int
    rel_thumb_path: str = ""


class DirLoader:
    @staticmethod
    def start(scaner_item: ScanerItem):
        """
        - Собирает список всех вложенных директорий в каталоге `Mf.curr_path`
        - Собирает список всех директорий из базы данных, которые
          соответствуют `Mf.alias`
        """
        finder_dirs = DirLoader.get_finder_dirs(scaner_item)
        db_dirs = DirLoader.get_db_dirs(scaner_item)
        return (finder_dirs, db_dirs)

    @staticmethod
    def get_finder_dirs(scaner_item: ScanerItem):
        """
        Собирает список директорий, которые:
        - есть в каталоге `Mf.curr_path`
        - не в стоп листе `Mf.stop_list`
        """
        # Создаем локальный ScanerItem без sql Engine, иначе ошибка pickle
        # в put
        # Отправляем текст в гуи что идет поиск в папке
        # gui_text: Имя папки (псевдоним папки): поиск в папке
        put_scaner_item = ScanerItem(
            mf=scaner_item.mf,
            engine=None,
            q=None
        )
        put_scaner_item.gui_text = (
            f"{scaner_item.mf_real_name} "
            f"({scaner_item.mf.alias}): "
            f"{Lng.search_in[cfg.lng].lower()}"
        )
        scaner_item.q.put(put_scaner_item)
        dirs: list[DirItem] = []
        stack = [scaner_item.mf.curr_path]
        while stack:
            try:
                scandir_iterator = os.scandir(stack.pop())
            except Exception as e:
                print("scaner > DirLoader error", e)
                continue
            for entry in scandir_iterator:
                try:
                    is_allowed = entry.name not in scaner_item.mf.stop_list
                    stmt = (entry.is_dir() and is_allowed)
                except Exception as e:
                    print("scaner > DirLoader error", e)
                    continue
                if stmt:
                    # передаем с каждой итерацией в основной поток ScanerItem
                    # чтобы в основном потоке сбрасывался таймер таймаута
                    scaner_item.q.put(put_scaner_item)
                    stack.append(entry.path)
                    rel_path = Utils.get_rel_img_path(
                        mf_path=scaner_item.mf.curr_path,
                        abs_img_path=entry.path
                    )
                    stats = entry.stat()
                    mod = int(stats.st_mtime)
                    dir_item = DirItem(entry.path, rel_path, mod)
                    dirs.append(dir_item)
        try:
            stats = os.stat(scaner_item.mf.curr_path)
            mod = int(stats.st_mtime)
            dir_item = DirItem(scaner_item.mf.curr_path, os.sep, mod)
        except Exception as e:
            print("new scaner dirs loader finder dirs error add root dir", e)
        return dirs

    @staticmethod
    def get_db_dirs(scaner_item: ScanerItem):
        """
        Возвращает список директорий из базы данных, которые:
        - соответствуют условию DIRS.c.brand == `Mf.alias`
        """
        conn = scaner_item.engine.connect()
        q = sqlalchemy.select(Dirs.rel_dir_path, Dirs.mod).where(
            Dirs.mf_alias == scaner_item.mf.alias
        )
        dirs: list[DirItem] = []
        for rel_path, mod in conn.execute(q):
            rel_path: str
            abs_dir_path = os.path.join(
                os.sep,
                scaner_item.mf.curr_path.strip(os.sep),
                rel_path.strip(os.sep)
            )
            item = DirItem(abs_dir_path, rel_path, mod)
            dirs.append(item)
        conn.close()
        return dirs


class DirsCompator:
    @staticmethod
    def start(finder_dirs: list[DirItem], db_dirs: list[DirItem]):
        """
        Сравнивает директории из Finder и из базы данных:
        - Создает список удаленных директорий (нет в Finer, есть в БД)
        - Создает список новых директорий (есть в Finder, нет в БД)
        """
        dirs_to_remove = DirsCompator.get_dirs_to_remove(finder_dirs, db_dirs)
        dirs_to_scan = DirsCompator.get_dirs_to_scan(finder_dirs, db_dirs)
        return (dirs_to_remove, dirs_to_scan)

    @staticmethod
    def get_dirs_to_remove(finder_dirs: list[DirItem], db_dirs: list[DirItem]):
        """
        Собирает список `DirItem`:
        - которых больше нет в Finder, но есть в базе данных
        - которые нужно удалить из базы данных
        """
        rel_paths = [dir_item.rel_path for dir_item in finder_dirs]
        return [
            dir_item
            for dir_item in db_dirs
            if dir_item.rel_path not in rel_paths
        ]

    @staticmethod
    def get_dirs_to_scan(finder_dirs: list[DirItem], db_dirs: list[DirItem]):
        """
        Собирает список `DirItem`:
        - которые есть в Finder, но нет в базе данных
        - которые нужно добавить в базу данных
        """
        rel_paths = [
            (dir_item.rel_path, dir_item.mod)
            for dir_item in db_dirs
        ]
        return [
            dir_item
            for dir_item in finder_dirs
            if (dir_item.rel_path, dir_item.mod) not in rel_paths
        ]


class DbDirUpdater:
    @staticmethod
    def start(scaner_item: ScanerItem, dirs_to_scan: list[DirItem]):
        """
        Запускать только, когда:
        - добавлены и удалены изображения `ImgItem` из БД
        - добавлены и удалены изображения `ImgItem` из `hashdir`

        Работает с БД:
        - удаляет записи из `DIRS`, которые соответствуют `Mf.alias`
        - добавляет записи в `DIRS`, которые соответствуют `Mf.alias`
        - по сути это замена `sqlalchemy.update`
        """
        # удалить старые записи
        if not dirs_to_scan:
            return
        conn = scaner_item.engine.connect()
        rel_paths = [dir_item.rel_path for dir_item in dirs_to_scan]
        del_stmt = sqlalchemy.delete(Dirs.table).where(
            Dirs.rel_dir_path.in_(rel_paths),
            Dirs.mf_alias == scaner_item.mf.alias
        )
        conn.execute(del_stmt)

        # вставить новые записи батчем
        values_list = [
            {
                ColumnNames.rel_item_path: dir_item.rel_path,
                ColumnNames.mod: dir_item.mod,
                ColumnNames.mf_alias: scaner_item.mf.alias
            }
            for dir_item in dirs_to_scan
        ]
        if values_list:
            conn.execute(sqlalchemy.insert(Dirs.table), values_list)
        conn.commit()
        conn.close()
        return None


class ImgLoader:
    @staticmethod
    def start(scaner_item: ScanerItem, dirs_to_scan: list[DirItem]):
        """
        - Обходит список `DirItem`:
            - Находит в Finder изображения и создает список `ImgItem`
            - Создает список `ImgItem` из записей БД с фильтрами:
                - Только из итерируемой директории
                - Если запись соответствует `Mf.alias`
        """
        finder_images = ImgLoader.get_finder_images(scaner_item, dirs_to_scan)
        db_images = ImgLoader.get_db_images(scaner_item, dirs_to_scan)
        return (finder_images, db_images)

    @staticmethod
    def get_finder_images(scaner_item: ScanerItem, dir_list: list[DirItem]):
        """
        Собирает список `ImgItem` из указанных директорий:
        - fider_images список ImgItem
        """
        # передает в гуи текст
        # имя папки (псевдоним): поиск
        text = (
            f"{scaner_item.mf_real_name} "
            f"({scaner_item.mf.alias}): "
            f"{Lng.search[cfg.lng].lower()}"
        )
        scaner_item.gui_text = text
        scaner_item.q.put(scaner_item)
        finder_images: list[ImgItem] = []
        for dir_item in dir_list:
            try:
                scandir_iterator = os.scandir(dir_item.abs_path)
            except Exception as e:
                print("scaner > ImgLoader error", e)
                continue
            for entry in scandir_iterator:
                if entry.path.endswith(ImgUtils.ext_all):
                    try:
                        stat = entry.stat()
                    except Exception as e:
                        print("scaner > ImgLoader error", e)
                        continue
                    # передаем в основной поток ScanerItem
                    # чтобы в основном потоке сбрасывался таймер таймаута
                    scaner_item.q.put(scaner_item)
                    size = int(stat.st_size)
                    birth = int(stat.st_birthtime)
                    mod = int(stat.st_mtime)
                    img_item = ImgItem(entry.path, size, birth, mod)
                    finder_images.append(img_item)
        return finder_images

    @staticmethod
    def get_db_images(scaner_item: ScanerItem, dir_list: list[DirItem]):
        """
        Возвращает информацию об изображениях в БД из указанных директорий:
        - db_images список ImgItem
        """
        conn = scaner_item.engine.connect()
        db_images: list[ImgItem] = []
        for dir_item in dir_list:
            q = sqlalchemy.select(
                Thumbs.rel_thumb_path,
                Thumbs.rel_img_path,
                Thumbs.size,
                Thumbs.birth,
                Thumbs.mod
                )
            q = q.where(Thumbs.mf_alias == scaner_item.mf.alias)
            if dir_item.rel_path == os.sep:
                q = q.where(Thumbs.rel_img_path.ilike("/%"))
                q = q.where(Thumbs.rel_img_path.not_ilike(f"/%/%"))
            else:
                q = q.where(
                    Thumbs.rel_img_path.ilike(f"{dir_item.rel_path}/%")
                )
                q = q.where(
                    Thumbs.rel_img_path.not_ilike(f"{dir_item.rel_path}/%/%")
                )
            for rel_thumb_path, rel_path, size, birth, mod in conn.execute(q):
                abs_img_path = Utils.get_abs_img_path(
                    mf_path=scaner_item.mf.curr_path,
                    rel_path=rel_path
                )
                img_item = ImgItem(
                    abs_img_path, size, birth, mod, rel_thumb_path
                )
                db_images.append(img_item)
        conn.close()
        return db_images


class ImgCompator:
    @staticmethod
    def start(finder_images: list[ImgItem], db_images: list[ImgItem]):
        """
        Сравнивает данные об изображениях из Finder и базы данных.  
        Получить данные об изображениях необходимо из ImgLoader.    
        Параметры:      
        - finder_images список ImgItem
        - db_images список ImgItem

        Собирает списки `ImgItem`:
        - изображения, которых больше нет в Finder но есть в БД
        - изображения, которых нет в БД, но есть в Finder
        """
        finder_dict = {
            (i.abs_img_path, i.size, i.birth, i.mod): i
            for i in finder_images
        }
        db_dict = {
            (i.abs_img_path, i.size, i.birth, i.mod): i
            for i in db_images
        }
        removed_images = [
            img_item
            for data, img_item in db_dict.items()
            if data not in finder_dict
        ]
        new_images = [
            img_item
            for data, img_item in finder_dict.items()
            if data not in db_dict
        ]
        return removed_images, new_images


class HashdirImgUpdater:
    @staticmethod
    def start(scaner_item: ScanerItem, del_images: list, new_images: list):
        """
        - Удаляет из `hashdir` миниатюры, которых больше нет в Finder
        - Добавляет миниатюры в `hashdir`, которые есть в Finder
        - Возвращает список успешно удаленных и список успешно добавленных
          миниатюр.
        - Далее необходимо обновить информацию в базе данных на основе
          полученных списков.

        Получить данные del_images и new_images необходимо из ImgCompator.  
        Параметры:  
        - del_images список ImgItem
        - new_images список ImgItem

        Возвращает:     
        - успешно удаленные из `hashdir` список `ImgItem`
        - успешно добавленные в `hashdir` список `ImgItem`
        """
        scaner_item.total_count = len(del_images) + len(new_images)
        new_del_images = HashdirImgUpdater.run_del_images(
            scaner_item=scaner_item,
            del_images=del_images
        )
        new_items = HashdirImgUpdater.run_new_images(
            scaner_item=scaner_item,
            new_images=new_images
        )
        return new_del_images, new_items

    @staticmethod
    def run_del_images(scaner_item: ScanerItem, del_images: list[ImgItem]):
        """
        Пытается удалить изображения из `hashdir` и пустые папки.   
        Возвращает список успешно удаленных изображений.
        Обрати внимание:
        - Только в списке del_images есть параметр `ImgItem.rel_thumb_path`
        - Он был присвоен при загрузуке записей из БД
        - Необходим, чтоб сформировать полный путь до миниатюры и удалить ее
        """
        new_del_images: list[ImgItem] = []
        for img_item in del_images:
            thumb_path = Utils.get_abs_thumb_path(img_item.rel_thumb_path)
            if os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                    folder = os.path.dirname(thumb_path)
                    if not os.listdir(folder):
                        shutil.rmtree(folder)
                    new_del_images.append(img_item)
                    scaner_item.total_count -= 1
                    # передаем в основной поток текст для отображения
                    # и чтобы в основном потоке сбрасывался таймер таймаута
                    HashdirImgUpdater.send_text(scaner_item)
                except Exception as e:
                    print("scaner HashdirImgUpdater error", e)
                    continue
        return new_del_images

    @staticmethod
    def run_new_images(scaner_item: ScanerItem, new_images: list[ImgItem]):
        """
        Пытается создать изображения в "hashdir".     
        Возвращает список успешно созданных изображений.
        """
        new_new_images: list[ImgItem] = []
        for img_item in new_images:
            img = ImgUtils.read_img(img_item.abs_img_path)
            img = Utils.fit_to_thumb(img, Static.max_img_size)
            if img is not None:
                try:
                    rel_img_path = Utils.get_rel_img_path(
                        mf_path=scaner_item.mf.curr_path,
                        abs_img_path=img_item.abs_img_path
                    )
                    thumb_path = Utils.create_abs_thumb_path(rel_img_path)
                    Utils.write_thumb(thumb_path, img)
                    new_new_images.append(img_item)
                    scaner_item.total_count -= 1
                    # передаем в основной поток текст для отображения
                    # и чтобы в основном потоке сбрасывался таймер таймаута
                    HashdirImgUpdater.send_text(scaner_item)
                except Exception as e:
                    print("scaner HashdirImgUpdater error", e)
                    continue
        return new_new_images

    @staticmethod
    def send_text(scaner_item: ScanerItem):
        """
        Посылает текст в гуи.   
        Имя папки (псевдоним): обновление (оставшееся число)
        """
        text = (
            f"{scaner_item.mf_real_name} "
            f"({scaner_item.mf.alias}): "
            f"{Lng.updating[cfg.lng].lower()} "
            f"({scaner_item.total_count})"
        )
        scaner_item.gui_text = text
        scaner_item.q.put(scaner_item)


class DbImgUpdater:
    @staticmethod
    def start(
        scaner_item: ScanerItem,
        del_images: list[ImgItem],
        new_images: list[ImgItem]
    ):
        if del_images:
            DbImgUpdater.remove_del_imgs(scaner_item, del_images)
        if new_images:
            DbImgUpdater.remove_exits_imgs(scaner_item, new_images)
            DbImgUpdater.add_new_imgs(scaner_item, new_images)
        return None

    @staticmethod
    def remove_del_imgs(scaner_item: ScanerItem, del_images: list[ImgItem]):
        conn = scaner_item.engine.connect()
        rel_thumb_paths = [i.rel_thumb_path for i in del_images]
        q = sqlalchemy.delete(Thumbs.table).where(
            Thumbs.rel_thumb_path.in_(rel_thumb_paths),
            Thumbs.mf_alias == scaner_item.mf.alias
        )
        conn.execute(q)
        conn.commit()
        conn.close()

    @staticmethod
    def remove_exits_imgs(scaner_item: ScanerItem, new_images: list[ImgItem]):
        conn = scaner_item.engine.connect()
        rel_img_paths = [
            Utils.get_rel_img_path(
                mf_path=scaner_item.mf.curr_path,
                abs_img_path=img_item.abs_img_path
            )
            for img_item in new_images
        ]
        q = sqlalchemy.delete(Thumbs.table).where(
            Thumbs.rel_img_path.in_(rel_img_paths),
            Thumbs.mf_alias == scaner_item.mf.alias
        )
        conn.execute(q)
        conn.commit()
        conn.close()

    @staticmethod
    def add_new_imgs(scaner_item: ScanerItem, new_images: list[ImgItem]):
        conn = scaner_item.engine.connect()
        values_list = []
        for img_item in new_images:
            rel_img_path = Utils.get_rel_img_path(
                scaner_item=scaner_item.mf.curr_path,
                abs_img_path=img_item.abs_img_path
            )
            abs_thumb_path = Utils.create_abs_thumb_path(rel_img_path)
            rel_thumb_path = Utils.get_rel_thumb_path(abs_thumb_path)
            values_list.append({
                ColumnNames.rel_item_path: rel_img_path,
                ColumnNames.rel_thumb_path: rel_thumb_path,
                ColumnNames.size: img_item.size,
                ColumnNames.birth: img_item.birth,
                ColumnNames.mod: img_item.mod,
                ColumnNames.resol: "",
                ColumnNames.coll: "",
                ColumnNames.fav: 0,
                ColumnNames.mf_alias: scaner_item.mf.alias
            })
        conn.execute(sqlalchemy.insert(Thumbs.table), values_list)
        conn.commit()
        conn.close()


class NewDirsWorker:    
    @staticmethod
    def start(dirs_to_scan: list[DirItem], scaner_item: ScanerItem):
        """
        Параметры: 
        - dirs_to_scan список DirItem
        - на основе этого списка добавляются и удаляются миниатюры в "hashdir"
        - обновляются базы данных THUMBS и DIRS
        """
        finder_images, db_images = ImgLoader.start(
            scaner_item=scaner_item,
            dirs_to_scan=dirs_to_scan
        )
        del_images, new_images = ImgCompator.start(
            finder_images=finder_images,
            db_images=db_images
        )
        del_images, new_images = HashdirImgUpdater.start(
            scaner_item=scaner_item,
            del_images=del_images,
            new_images=new_images
        )
        DbImgUpdater.start(
            scaner_item=scaner_item,
            del_images=del_images,
            new_images=new_images
        )
        DbDirUpdater.start(
            scaner_item=scaner_item,
            dirs_to_scan=dirs_to_scan
        )
        return None
    

class RemovedDirsWorker:
    @staticmethod
    def start(dirs_to_del: list[DirItem], scaner_item: ScanerItem):
        conn = scaner_item.engine.connect()
        for dir_item in dirs_to_del:
            RemovedDirsWorker.remove_thumbs(dir_item, scaner_item, conn)
            RemovedDirsWorker.remove_dir_entry(dir_item, scaner_item, conn)
        conn.commit()
        conn.close()

    @staticmethod
    def remove_thumbs(
        dir_item: DirItem,
        scaner_item: ScanerItem,
        conn: sqlalchemy.Connection
    ):
        stmt = (
            sqlalchemy.select(Thumbs.rel_thumb_path)
            .where(Thumbs.rel_img_path.ilike(f"{dir_item.rel_path}/%"))
            .where(Thumbs.rel_img_path.not_ilike(f"{dir_item.rel_path}/%/%"))
            .where(Thumbs.mf_alias == scaner_item.mf.alias)
        )
        for rel_thumb_path in conn.execute(stmt).scalars():
            try:
                os.remove(Utils.get_abs_thumb_path(rel_thumb_path))
            except Exception as e:
                print("DelDirsHandler, remove thumb:", e)

        del_stmt = (
            sqlalchemy.delete(Thumbs.table)
            .where(Thumbs.rel_img_path.ilike(f"{dir_item.rel_path}/%"))
            .where(Thumbs.rel_img_path.not_ilike(f"{dir_item.rel_path}/%/%"))
            .where(Thumbs.mf_alias == scaner_item.mf.alias)
        )
        conn.execute(del_stmt)

    def remove_dir_entry(
            dir_item: DirItem,
            scaner_item: ScanerItem,
            conn: sqlalchemy.Connection
        ):
        stmt = (
            sqlalchemy.delete(Dirs.table)
            .where(Dirs.rel_dir_path == dir_item.rel_path)
            .where(Dirs.mf_alias == scaner_item.mf.alias)
        )
        conn.execute(stmt)


class AllDirScaner:
    @staticmethod
    def start(mf_list: list[Mf], q: Queue):
        engine = Dbase.create_engine()
        # нельзя обращаться сразу к Mf так как это мультипроцесс
        for mf in mf_list:
            scaner_item = ScanerItem(mf, engine, q)
            if scaner_item.mf.get_available_path():
                try:
                    print("scaner started", scaner_item.mf.alias)
                    AllDirScaner.single_mf_scan(scaner_item)
                    print("scaner finished", scaner_item.mf.alias)
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    print("scaner AllDirsScaner error", e)
                    continue
            else:
                no_conn = Lng.no_connection[cfg.lng].lower()
                scaner_item.gui_text = (
                    f"{scaner_item.mf_real_name} "
                    f"({scaner_item.mf.alias}): "
                    f"{no_conn}"
                )
                scaner_item.q.put(scaner_item)
                print(
                    "scaner no connection",
                    scaner_item.mf_real_name,
                    scaner_item.mf.alias
                )
                sleep(5)
            if scaner_item.reload_gui:
                scaner_item.q.put(scaner_item)
        engine.dispose()

    @staticmethod
    def single_mf_scan(scaner_item: ScanerItem):
        # собираем Finder директории и директории из БД
        finder_dirs, db_dirs = DirLoader.start(scaner_item)
        print("finder dirs********", finder_dirs)
        print("db_dirs********", db_dirs)
        return
        if not finder_dirs:
            print(scaner_item.mf.alias, "no finder dirs")
            return
        removed_dirs, new_dirs = DirsCompator.start(finder_dirs, db_dirs)
        if new_dirs:
            NewDirsWorker.start(new_dirs, scaner_item)
        # удаляем удаленные Finder директории
        if removed_dirs:
            del_handler = RemovedDirsWorker.start(removed_dirs, scaner_item)
            del_handler.run()