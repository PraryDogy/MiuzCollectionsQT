import os
import shutil
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

import sqlalchemy

from cfg import Static, cfg

from .database import Dbase, Dirs, Thumbs
from .items import CopyTaskItem, OneFileInfoItem, OnStartItem, ReadImgItem
from .lang import Lng
from .main_folder import Mf
from .shared_utils import ImgUtils, SharedUtils
from .tasks import Utils


class BaseProcessWorker:
    def __init__(self, target: callable, args: tuple):
        super().__init__()

        self.proc = Process(
            target=target,
            args=(*args, )
        )

    def start(self):
        self.proc.start()

    def is_alive(self):
        return self.proc.is_alive()
    
    def terminate_join(self):
        """
        Корректно terminate с join
        Завершает все очереди Queue
        """
        self.proc.terminate()
        self.proc.join(timeout=0.2)
        queues: tuple[Queue] = (i for i in dir(self) if hasattr(i, "put"))
        for i in queues:
                i.close()
                i.join_thread()


class ProcessWorker(BaseProcessWorker):
    """
        Передает в BaseProcessWorker args + self.proc (Queue)
    """
    def __init__(self, target: callable, args: tuple):
        self.proc_q = Queue()
        super().__init__(target, (*args, self.proc_q))


class ReadImg:
    @staticmethod
    def start(src: str, desaturate: bool, q: Queue):
        img_array = ImgUtils.read_img(src)
        if desaturate:
            img_array = Utils.desaturate_image(img_array, 0.2)
        q.put(ReadImgItem(src, img_array))


class OneFileInfo:

    @staticmethod
    def start(path: str, proc_q: Queue):
        """
        Возвращает в Queue либо dict либо str
        Если str, процесс окончен
        """
        try:
            info_item = OneFileInfo._gather_info(path)
            proc_q.put(info_item)

            resol = ImgUtils.get_img_res(path)
            if resol:
                info_item.res = resol
            proc_q.put(info_item)
        except Exception as e:
            Utils.print_error()

    @staticmethod
    def _gather_info(path: str) -> OneFileInfoItem:
        name = os.path.basename(path)
        _, type_ = os.path.splitext(name)
        stats = os.stat(path)
        size = SharedUtils.get_f_size(stats.st_size)
        date_time = datetime.fromtimestamp(stats.st_mtime)
        month = Lng.months_genitive_case[cfg.lng][str(date_time.month)]
        mod = f"{date_time.day} {month} {date_time.year}"
        item = OneFileInfoItem(type_, size, mod, "")
        return item

    @staticmethod
    def lined_text(text: str, max_row = 50) -> str:
        if len(text) > max_row:
            return "\n".join(
                text[i:i + max_row]
                for i in range(0, len(text), max_row)
            )
        return text
    


class CopyTaskWorker(BaseProcessWorker):
    def __init__(self, target, args):
        self.proc_q = Queue()
        self.gui_q = Queue()
        super().__init__(target, (*args, self.proc_q, self.gui_q))


class CopyTask:
    @staticmethod
    def start(copy_item: CopyTaskItem, proc_q: Queue, gui_q: Queue):

        src_dst_urls = CopyTask.get_another_dir_urls(copy_item)
        copy_item.dst_urls = [dst for src, dst in src_dst_urls]

        total_size = 0
        for src, dest in src_dst_urls:
            total_size += os.path.getsize(src)

        copy_item.total_size = total_size // 1024
        copy_item.total_count = len(src_dst_urls)
        replace_all = False

        for count, (src, dest) in enumerate(src_dst_urls, start=1):

            if not replace_all and dest.exists() and src.name == dest.name:
                copy_item.msg = "need_replace"
                proc_q.put(copy_item)
                while True:
                    sleep(1)
                    if not gui_q.empty():
                        new_copy_item: CopyTaskItem = gui_q.get()
                        if new_copy_item.msg == "replace_one":
                            break
                        elif new_copy_item.msg == "replace_all":
                            replace_all = True
                            break

            copy_item.current_count = count
            copy_item.msg = ""
            try:
                CopyTask.copy_file_with_progress(proc_q, copy_item, src, dest)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                print("CopyTask copy error", e)
                copy_item.msg = "error"
                proc_q.put(copy_item)
                return
            if copy_item.is_cut:
                os.remove(src)
                "удаляем файлы чтобы очистить директории"
        
        copy_item.msg = "finished"
        proc_q.put(copy_item)

    @staticmethod
    def get_another_dir_urls(copy_item: CopyTaskItem):
        src_dst_urls: list[tuple[Path, Path]] = []
        dst_dir = Path(copy_item.dst_dir)
        for url in copy_item.src_urls:
            url = Path(url)
            new_path = dst_dir.joinpath(url.name)
            src_dst_urls.append((url, new_path))
        return src_dst_urls
        
    @staticmethod
    def copy_file_with_progress(proc_q: Queue, copy_item: CopyTaskItem, src: Path, dest: Path):
        block = 4 * 1024 * 1024  # 4 MB
        with open(src, "rb") as fsrc, open(dest, "wb") as fdst:
            while True:
                buf = fsrc.read(block)
                if not buf:
                    break
                fdst.write(buf)
                copy_item.current_size += len(buf) // 1024
                proc_q.put(copy_item)
        shutil.copystat(src, dest, follow_symlinks=True)


class FilesRemover:
    @staticmethod
    def start(paths: list[str], q: Queue):
        deleted_files = []
        for path in paths:
            try:
                os.remove(path)
                deleted_files.append(path)
            except Exception as e:
                print("FilesRemover error:", e)
        q.put(deleted_files)
        

class _DeletedMfRemover:

    def start(engine: sqlalchemy.Engine, on_start_item: OnStartItem, q: Queue):
        """
        Логика такая:
        - Пользователь в настройках приложения удаляет Mf
        - Данные удаляются из БД, приложение перезапускается
        - RemoveMfCleaner вызывается при перезапуске приложения
        - Сравнивается список Mf в базе данных и список Mf в mf.json
        Если Mf нет в базе данных, но есть в mf.json, нужно удалить все данные
        по этой Mf:
        - изображения thumbs из hashdir в ApplicationSupport    
        - записи в базе данных
        Передает в Queue список удаленных Mf (список имен str)
        """
        conn = engine.connect()
        stmt = sqlalchemy.select(Thumbs.mf_alias).distinct()
        db_mf_list = conn.execute(stmt).scalars().all()
        json_mf_list = [i.alias for i in on_start_item.mf_list]
        removed_mf_list: list[str] = [
            i
            for i in db_mf_list
            if i not in json_mf_list and i is not None
        ]

        if removed_mf_list:
            for i in removed_mf_list:
                rows = _DeletedMfRemover.get_rows(i, conn)
                _DeletedMfRemover.remove_images(rows)
                _DeletedMfRemover.remove_rows(rows, conn)
            _DeletedMfRemover.remove_dirs(conn)
        conn.close()
        q.put(removed_mf_list)
    
    @staticmethod
    def get_rows(mf_name: str, conn: sqlalchemy.Connection):
        q = sqlalchemy.select(Thumbs.id, Thumbs.rel_thumb_path).where(
            Thumbs.mf_alias == mf_name
        )
        return [
            (id_, Utils.get_abs_thumb_path(rel_thumb_path))
            for id_, rel_thumb_path in conn.execute(q).fetchall()
        ]

    @staticmethod
    def remove_images(rows: list):
        """
        rows: [(row id int, thumb path), ...]
        """
        for id_, image_path in rows:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                folder = os.path.dirname(image_path)
                if os.path.exists(folder) and not os.listdir(folder):
                    shutil.rmtree(folder)
            except Exception as e:
                print(f"new scaner utils, MfRemover, remove images error. ID: {id_}, Path: {image_path}, Error: {e}")
                continue

    @staticmethod
    def remove_rows(rows: list, conn: sqlalchemy.Connection):
        """
        rows: [(row id int, thumb path), ...]
        """
        ids = [id_ for id_, _ in rows]
        if ids:
            q = sqlalchemy.delete(Thumbs.table).where(Thumbs.id.in_(ids))
            conn.execute(q)
            conn.commit()

    @staticmethod
    def remove_dirs(conn: sqlalchemy.Connection):
        q = sqlalchemy.select(Dirs.mf_alias).distinct()
        db_brands = set(conn.execute(q).scalars())
        app_brands = set(i.alias for i in Mf.list_)
        to_delete = db_brands - app_brands

        if to_delete:
            del_stmt = sqlalchemy.delete(Dirs.table).where(Dirs.mf_alias.in_(to_delete))
            conn.execute(del_stmt)
            conn.commit()


class _EmptyRecordsRemover:
    @staticmethod
    def start(engine: sqlalchemy.Engine, q: Queue):
        """
        При запуске приложения проверяет данные в базе данных и удаляет
        записи со значениями None
        Передает в очередь None
        """
        conn = engine.connect()
        stmt = (
            sqlalchemy.delete(Thumbs.table).where(
                sqlalchemy.or_(
                    Thumbs.rel_thumb_path == None,
                    Thumbs.rel_img_path == None
                )
            )
        )
        conn.execute(stmt)
        conn.commit()
        q.put(None)


class _EmptyHashdirRemover:
    @staticmethod
    def start(q: Queue):
        """
        При запуске приложения проверяет, есть ли пустые директории в thumbnails,
        удаляет лишние
        Передает в Queue список удаленных директорий
        """
        removed_dirs: list[str] = []
        for i in os.scandir(Static.app_support_hashdir):
            if os.path.isdir(i.path) and not os.listdir(i.path):
                try:
                    shutil.rmtree(i.path)
                    removed_dirs.append(i.path)
                except Exception as e:
                    print("new scaner, empty hashdir remover", e)
        if removed_dirs:
            q.put(removed_dirs)


class OnStartTask:
    @staticmethod
    def start(on_start_item: OnStartItem, q: Queue):
        engine = Dbase.create_engine()
        _DeletedMfRemover.start(engine, on_start_item, q)
        _EmptyRecordsRemover.start(engine, q)
        _EmptyHashdirRemover.start(q)