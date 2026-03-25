import os
from multiprocessing import Queue
from time import sleep

import sqlalchemy

from cfg import Static
from system.database import ClmnNames, Dbase, Dirs, Thumbs
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import ImgUtils
from system.utils import Utils

from .items import (ScanerDirItem, ScanerImgItem, ScanerItem,
                    SingleDirScanerItem)


class Gui:
    def send_data(queue: Queue, text: str, reload_gui: bool = False):
        queue.put((text, reload_gui))


class AllDirLoader:
    @staticmethod
    def get_finder_dirs(scaner_item: ScanerItem):
        """
        Собирает список директорий, которые:
        - есть в каталоге `Mf.curr_path`
        - не в стоп листе `Mf.stop_list`
        """
        text = (
            f"{scaner_item.mf.mf_alias}: "
            f"{Lng.search_in[scaner_item.lng_index].lower()}"
        )
        Gui.send_data(scaner_item.queue, text)

        dirs: list[ScanerDirItem] = []
        stack = [scaner_item.mf.mf_current_path]
        while stack:
            try:
                scandir_iterator = os.scandir(stack.pop())
            except Exception as e:
                print("scaner > DirLoader error", e)
                continue
            for entry in scandir_iterator:
                try:
                    is_allowed = entry.name not in scaner_item.mf.mf_stop_list
                    stmt = (entry.is_dir() and is_allowed)
                except Exception as e:
                    print("scaner > DirLoader error", e)
                    continue
                if stmt:
                    stack.append(entry.path)
                    rel_path = Utils.get_rel_any_path(
                        mf_path=scaner_item.mf.mf_current_path,
                        abs_img_path=entry.path
                    )
                    stats = entry.stat()
                    mod = int(stats.st_mtime)
                    dir_item = ScanerDirItem(entry.path, rel_path, mod)
                    dirs.append(dir_item)
        try:
            stats = os.stat(scaner_item.mf.mf_current_path)
            mod = int(stats.st_mtime)
            dir_item = ScanerDirItem(scaner_item.mf.mf_current_path, os.sep, mod)
            dirs.append(dir_item)
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
            Dirs.mf_alias == scaner_item.mf.mf_alias
        )
        dirs: list[ScanerDirItem] = []
        for rel_path, mod in conn.execute(q):
            rel_path: str
            abs_dir_path = os.path.join(
                os.sep,
                scaner_item.mf.mf_current_path.strip(os.sep),
                rel_path.strip(os.sep)
            )
            item = ScanerDirItem(abs_dir_path, rel_path, mod)
            dirs.append(item)
        conn.close()
        return dirs


class DirsCompator:

    @staticmethod
    def get_dirs_to_remove(finder_dirs: list[ScanerDirItem], db_dirs: list[ScanerDirItem]):
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
    def get_dirs_to_scan(finder_dirs: list[ScanerDirItem], db_dirs: list[ScanerDirItem]):
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
    def upsert_records(scaner_item: ScanerItem, dirs_to_scan: list[ScanerDirItem]):
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
        conn = scaner_item.engine.connect()
        rel_paths = [dir_item.rel_path for dir_item in dirs_to_scan]
        del_stmt = sqlalchemy.delete(Dirs.table).where(
            Dirs.rel_dir_path.in_(rel_paths),
            Dirs.mf_alias == scaner_item.mf.mf_alias
        )
        conn.execute(del_stmt)

        # вставить новые записи батчем
        values_list = [
            {
                ClmnNames.rel_item_path: dir_item.rel_path,
                ClmnNames.mod: dir_item.mod,
                ClmnNames.mf_alias: scaner_item.mf.mf_alias
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
    def get_finder_images(
        scaner_item: ScanerItem,
        dirs_to_scan: list[ScanerDirItem]
    ):
        """
        Собирает список `ImgItem` из указанных директорий:
        - fider_images список ImgItem
        """
        text = (
            f"{scaner_item.mf.mf_alias}: "
            f"{Lng.search_in[scaner_item.lng_index].lower()}"
        )
        Gui.send_data(scaner_item.queue, text)
        finder_images: list[ScanerImgItem] = []
        for dir_item in dirs_to_scan:
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
                    size = int(stat.st_size)
                    mod = int(stat.st_mtime)
                    if size == 0:
                        continue
                    img_item = ScanerImgItem(entry.path, size, mod)
                    finder_images.append(img_item)
        return finder_images

    @staticmethod
    def get_db_images(
        scaner_item: ScanerItem,
        dirs_to_scan: list[ScanerDirItem]
    ):
        """
        Возвращает информацию об изображениях в БД из указанных директорий:
        - db_images список ImgItem
        """
        conn = scaner_item.engine.connect()
        db_images: list[ScanerImgItem] = []
        for dir_item in dirs_to_scan:
            q = sqlalchemy.select(
                Thumbs.rel_thumb_path,
                Thumbs.rel_img_path,
                Thumbs.size,
                Thumbs.mod
                )
            q = q.where(Thumbs.mf_alias == scaner_item.mf.mf_alias)
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
            for rel_thumb_path, rel_path, size, mod in conn.execute(q):
                abs_img_path = Utils.get_abs_any_path(
                    mf_path=scaner_item.mf.mf_current_path,
                    rel_path=rel_path
                )
                img_item = ScanerImgItem(
                    abs_img_path, size, mod, rel_thumb_path
                )
                db_images.append(img_item)
        conn.close()
        return db_images


class ImgCompator:
    @staticmethod
    def start(finder_images: list[ScanerImgItem], db_images: list[ScanerImgItem]):
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
            (i.abs_img_path, i.size, i.mod): i
            for i in finder_images
        }
        db_dict = {
            (i.abs_img_path, i.size, i.mod): i
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
    def run_del_images(scaner_item: ScanerItem, del_images: list[ScanerImgItem]):
        """
        Пытается удалить изображения из `hashdir` и пустые папки.   
        Обрати внимание:
        - Только в списке del_images есть параметр `ImgItem.rel_thumb_path`
        - Он был присвоен при загрузуке записей из БД
        - Необходим, чтоб сформировать полный путь до миниатюры и удалить ее
        """
        for img_item in del_images:
            scaner_item.total_count -= 1
            Gui.send_data(
                scaner_item.queue,
                HashdirImgUpdater.get_gui_text(scaner_item)
            )
            abs_thumb_path = Utils.get_abs_thumb_path(img_item.rel_thumb_path)
            root = os.path.dirname(abs_thumb_path)
            try:
                os.remove(abs_thumb_path)
            except Exception as e:
                pass
            try:
                os.rmdir(root)
            except OSError:
                pass

    @staticmethod
    def run_new_images(scaner_item: ScanerItem, new_images: list[ScanerImgItem]):
        """
        Пытается создать изображения в "hashdir"
        """
        for img_item in new_images:
            scaner_item.total_count -= 1
            Gui.send_data(
                scaner_item.queue,
                HashdirImgUpdater.get_gui_text(scaner_item)
            )
            img = ImgUtils.read_img(img_item.abs_img_path)
            img = ImgUtils.fit_to_thumb(img, Static.max_img_size)
            try:
                rel_img_path = Utils.get_rel_any_path(
                    mf_path=scaner_item.mf.mf_current_path,
                    abs_img_path=img_item.abs_img_path
                )
                thumb_path = Utils.create_abs_thumb_path(
                    rel_img_path=rel_img_path,
                    mf_alias=scaner_item.mf.mf_alias
                )
                ImgUtils.write_thumb(thumb_path, img)
            except Exception as e:
                print("scaner HashdirImgUpdater error", e)
                continue
    
    def get_gui_text(scaner_item: ScanerItem):
        return (
            f"{scaner_item.mf.mf_alias}: "
            f"{Lng.updating[scaner_item.lng_index].lower()} "
            f"({scaner_item.total_count})"
        )


class DbImgUpdater:

    @staticmethod
    def delete_records(scaner_item: ScanerItem, del_images: list[ScanerImgItem]):
        """
        Удаляет из БД удаленные изображения.
        """
        conn = scaner_item.engine.connect()
        q = sqlalchemy.delete(Thumbs.table).where(
            Thumbs.rel_thumb_path.in_([i.rel_thumb_path for i in del_images]),
            Thumbs.mf_alias == scaner_item.mf.mf_alias
        )
        conn.execute(q)
        conn.commit()
        conn.close()

    @staticmethod
    def upsert_records(scaner_item: ScanerItem, new_images: list[ScanerImgItem]):
        """
        Добавляет записи из БД об успешно сохраненных изображениях.
        """
        conn = scaner_item.engine.connect()

        del_stmt = sqlalchemy.delete(Thumbs.table).where(
            Thumbs.rel_thumb_path.in_([i.rel_thumb_path for i in new_images]),
            Thumbs.mf_alias == scaner_item.mf.mf_alias
        )
        conn.execute(del_stmt)
        conn.commit()

        # добавляем записи
        values_list = []
        for img_item in new_images:
            rel_img_path = Utils.get_rel_any_path(
                mf_path=scaner_item.mf.mf_current_path,
                abs_img_path=img_item.abs_img_path
            )
            abs_thumb_path = Utils.create_abs_thumb_path(
                rel_img_path=rel_img_path,
                mf_alias=scaner_item.mf.mf_alias
            )
            rel_thumb_path = Utils.get_rel_thumb_path(abs_thumb_path)
            values_list.append({
                ClmnNames.rel_item_path: rel_img_path,
                ClmnNames.rel_thumb_path: rel_thumb_path,
                ClmnNames.size: img_item.size,
                ClmnNames.birth: 0,
                ClmnNames.mod: img_item.mod,
                ClmnNames.resol: "none",
                ClmnNames.coll: "none",
                ClmnNames.fav: 0,
                ClmnNames.mf_alias: scaner_item.mf.mf_alias
            })
        stmt = sqlalchemy.insert(Thumbs.table).values(values_list)
        conn.execute(stmt)
        conn.commit()
        conn.close()


class DirsToScanWorker:    
    @staticmethod
    def start(dirs_to_scan: list[ScanerDirItem], scaner_item: ScanerItem):
        """
        Параметры: 
        - dirs_to_scan список DirItem
        - на основе этого списка добавляются и удаляются миниатюры в "hashdir"
        - обновляются базы данных THUMBS и DIRS
        """
        finder_images = ImgLoader.get_finder_images(scaner_item, dirs_to_scan)
        db_images = ImgLoader.get_db_images(scaner_item, dirs_to_scan)
        del_images, new_images = ImgCompator.start(finder_images, db_images)
        # общий счет для отображения в GUI
        scaner_item.total_count = len(del_images) + len(new_images)
        # удаляем миниатюры
        # обновляем БД
        HashdirImgUpdater.run_del_images(scaner_item, del_images)
        DbImgUpdater.delete_records(scaner_item, del_images)

        # делим новые миниатюры на списки по 10
        step = 10
        chunked_new_images = [
            new_images[i:i+step]
            for i in range(0, len(new_images), step)
        ]
        for new_images_chunk in chunked_new_images:
            # создаем миниатюры с шагом 10
            HashdirImgUpdater.run_new_images(scaner_item, new_images_chunk)
            DbImgUpdater.upsert_records(scaner_item, new_images_chunk)

        DbDirUpdater.upsert_records(scaner_item, dirs_to_scan)
    

class RemovedDirsWorker:

    @staticmethod
    def remove_thumbs(
        dir_item: ScanerDirItem,
        scaner_item: ScanerItem,
        conn: sqlalchemy.Connection
    ):
        """
        Удаляет миниатюры из 'hashdir' и записи в базе данных Thumbs
        """
        stmt_thumbs_to_remove = (
            sqlalchemy.select(Thumbs.id, Thumbs.rel_thumb_path)
            .where(Thumbs.rel_img_path.ilike(f"{dir_item.rel_path}/%"))
            .where(Thumbs.rel_img_path.not_ilike(f"{dir_item.rel_path}/%/%"))
            .where(Thumbs.mf_alias == scaner_item.mf.mf_alias)
        )
        thumbs_to_remove = conn.execute(stmt_thumbs_to_remove).all()

        for _, rel_thumb_path in thumbs_to_remove:
            try:
                abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
                root = os.path.dirname(abs_thumb_path)
                os.remove(abs_thumb_path)
                try:
                 os.rmdir(root)
                except OSError:
                    pass
            except Exception as e:
                print("DelDirsHandler, remove thumb:", e)

        del_stmt = sqlalchemy.delete(Thumbs.table).where(
            Thumbs.id.in_([id_ for id_, _ in thumbs_to_remove])
        )
        conn.execute(del_stmt)

    def remove_dirs(
            dir_item: ScanerDirItem,
            scaner_item: ScanerItem,
            conn: sqlalchemy.Connection
        ):
        """
        Удаляет записи в базе данных Dirs
        """
        stmt = (
            sqlalchemy.delete(Dirs.table)
            .where(Dirs.rel_dir_path == dir_item.rel_path)
            .where(Dirs.mf_alias == scaner_item.mf.mf_alias)
        )
        conn.execute(stmt)


class AllDirScaner:
    @staticmethod
    def start(mf_list: list[Mf], lng_index: int, queue: Queue):
        engine = Dbase.create_engine()
        # нельзя обращаться сразу к Mf так как это мультипроцесс
        for mf in mf_list:
            scaner_item = ScanerItem(mf, engine, queue, lng_index, 0)
            avaible_mf_path = scaner_item.mf.get_avaiable_mf_path()
            if avaible_mf_path:
                scaner_item.mf.set_mf_current_path(avaible_mf_path)
                try:
                    print("scaner started", scaner_item.mf.mf_alias)
                    AllDirScaner.single_mf_scan(scaner_item)
                    print("scaner finished", scaner_item.mf.mf_alias)
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    continue
            else:
                text = (
                    f"{scaner_item.mf.mf_alias}: "
                    f"{Lng.no_connection[lng_index].lower()}"
                )
                Gui.send_data(scaner_item.queue, text)
                print(text)
                sleep(3)
        engine.dispose()

    @staticmethod
    def single_mf_scan(scaner_item: ScanerItem):
        finder_dirs = AllDirLoader.get_finder_dirs(scaner_item)
        db_dirs = AllDirLoader.get_db_dirs(scaner_item)
        if not finder_dirs:
            print(scaner_item.mf.mf_alias, "no finder dirs")
            return
        removed_dirs = DirsCompator.get_dirs_to_remove(finder_dirs, db_dirs)
        dirs_to_scan = DirsCompator.get_dirs_to_scan(finder_dirs, db_dirs)

        # это нужно, когда удалена вся папка "имя папки"
        # то есть не когда "имя папки" пуста, но существует,
        # а когда папка "имя папки" не существует
        reload_gui = False
        if removed_dirs:
            reload_gui = True
            conn = scaner_item.engine.connect()
            for dir_item in removed_dirs:
                RemovedDirsWorker.remove_thumbs(dir_item, scaner_item, conn)
                RemovedDirsWorker.remove_dirs(dir_item, scaner_item, conn)
            conn.commit()
            conn.close()
        if dirs_to_scan:
            reload_gui = True
            DirsToScanWorker.start(dirs_to_scan, scaner_item)
        Gui.send_data(scaner_item.queue, "", reload_gui)


class SingleDirScaner:

    @staticmethod
    def start(scaner_item: SingleDirScanerItem, lng_index: int, queue: Queue):
        for mf, dirs_to_scan in scaner_item.data.items():
            print("single dir scaner started, mf:", mf.mf_alias)
            SingleDirScaner.single_mf_scan(
                mf=mf,
                dirs_to_scan=dirs_to_scan,
                lng_index=lng_index,
                queue=queue
            )
            print("single dir scaner finished, mf:", mf.mf_alias)

    @staticmethod
    def single_mf_scan(mf: Mf, dirs_to_scan: list[str], lng_index: int, queue: Queue):
        """
        Сканирует заданне директории в пределах Mf на предмет новых или
        удаленных изображений.

        Параметры:
        - mf: сканируемая директория должна принадлежать определенному Mf
        - dirs_to_scan: директории, которые нужно просканировать
        """
        engine = Dbase.create_engine()
        scaner_item = ScanerItem(mf, engine, queue, lng_index, 0)
        avaiable_mf_path = scaner_item.mf.get_avaiable_mf_path()
        if avaiable_mf_path:
            scaner_item.mf.set_mf_current_path(avaiable_mf_path)
            dir_items: list[ScanerDirItem] = []
            for i in dirs_to_scan:
                try:
                    mod = int(os.stat(i).st_mtime)
                except Exception as e:
                    print("SingleDirScaner error", e)
                    continue
                item = ScanerDirItem(
                    abs_path=i,
                    rel_path=Utils.get_rel_any_path(mf.mf_current_path, i),
                    mod=mod
                )
                dir_items.append(item)
            reload_gui = False
            if dir_items:
                DirsToScanWorker.start(dir_items, scaner_item)
                reload_gui = True
            Gui.send_data(scaner_item.queue, "", reload_gui)