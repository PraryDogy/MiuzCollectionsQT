import os
import shutil
import traceback
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

import sqlalchemy
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver as Observer

from cfg import Cfg, Static

from .database import ClmnNames, Dbase, Dirs, Thumbs
from .items import (CopyTaskItem, OneFileInfoItem, ReadImgItem,
                    UpdateThumbItem, WatchDogItem)
from .lang import Lng
from .main_folder import Mf
from .shared_utils import ImgUtils, SharedUtils
from .tasks import Utils
import numpy as np

class BaseProcessWorker:
    _registry = []

    def __init__(self, target: callable, args: tuple):
        super().__init__()
        self.process = Process(target=target, args=(*args, ))
        self._queues: list[Queue] = [a for a in args if hasattr(a, 'put')]
        BaseProcessWorker._registry.append(self)

    def start(self):
        self.process.start()

    def is_alive(self):
        return self.process.is_alive()
    
    def terminate_join(self):
        """
        Корректно terminate с join
        Завершает все очереди Queue
        """
        self.process.terminate()
        self.process.join(timeout=0.2)

        for queue in self._queues:
            queue.close()
            queue.cancel_join_thread()

        if self.process.is_alive():
            self.process.kill()

        if self in BaseProcessWorker._registry:
            BaseProcessWorker._registry.remove(self)

    @staticmethod
    def stop_all():
        for worker in BaseProcessWorker._registry.copy():
            worker: BaseProcessWorker
            worker.terminate_join()


class ProcessWorker(BaseProcessWorker):
    """
        Передает в BaseProcessWorker args + self.proc (Queue)
    """
    def __init__(self, target: callable, args: tuple):
        self.process_queue = Queue()
        super().__init__(target, (*args, self.process_queue))


class ReadImg:
    @staticmethod
    def start(src: str, desaturate: bool, queue: Queue):
        img_array = ImgUtils.read_img(src)
        if desaturate:
            img_array = ImgUtils.desaturate_image(img_array, 0.2)
        queue.put(ReadImgItem(src, img_array))


class OneFileInfo:

    @staticmethod
    def start(path: str, process_queue: Queue):
        """
        Возвращает в Queue либо dict либо str
        Если str, процесс окончен
        """
        try:
            info_item = OneFileInfo._gather_info(path)
            process_queue.put(info_item)

            resol = ImgUtils.get_img_res(path)
            if resol:
                info_item.res = resol
            process_queue.put(info_item)
        except Exception as e:
            Utils.print_error()

    @staticmethod
    def _gather_info(path: str) -> OneFileInfoItem:
        name = os.path.basename(path)
        _, type_ = os.path.splitext(name)
        stats = os.stat(path)
        size = SharedUtils.get_f_size(stats.st_size)
        date_time = datetime.fromtimestamp(stats.st_mtime)
        month = Lng.months_genitive_case[Cfg.lng_index][str(date_time.month)]
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
        self.process_queue = Queue()
        self.gui_queue = Queue()
        super().__init__(target, (*args, self.process_queue, self.gui_queue))


class CopyTask:
    @staticmethod
    def start(copy_item: CopyTaskItem, process_queue: Queue, que_queue: Queue):

        src_dst_urls = CopyTask.get_another_dir_urls(copy_item)
        copy_item.dst_urls = [dst for src, dst in src_dst_urls]

        total_size = 0
        for src, dest in src_dst_urls:
            total_size += os.path.getsize(src)

        copy_item.total_size = total_size // 1024
        copy_item.total_count = len(src_dst_urls)
        replace_all = False

        for count, (src, dest) in enumerate(src_dst_urls, start=1):

            if src == dest:
                dest = CopyTask.set_count_name(dest)

            if not replace_all and dest.exists() and src.name == dest.name:
                copy_item.msg = "need_replace"
                process_queue.put(copy_item)
                while True:
                    sleep(1)
                    if not que_queue.empty():
                        new_copy_item: CopyTaskItem = que_queue.get()
                        if new_copy_item.msg == "replace_one":
                            break
                        elif new_copy_item.msg == "replace_all":
                            replace_all = True
                            break

            copy_item.current_count = count
            copy_item.msg = ""
            try:
                CopyTask.copy_file_with_progress(process_queue, copy_item, src, dest)
            except Exception as e:
                print("CopyTask copy error", e)
                copy_item.msg = "error"
                process_queue.put(copy_item)
                return
            if copy_item.is_cut:
                os.remove(src)
                "удаляем файлы чтобы очистить директории"
        
        copy_item.msg = "finished"
        process_queue.put(copy_item)

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
    def set_count_name(path: Path):
        counter = 2
        filename, ext = os.path.splitext(path.name)
        while os.path.exists(path):
            new_filename = f"{filename} ({counter}){ext}"
            path = os.path.join(path.parent, new_filename)
            path = Path(path)
            counter += 1
        return path
        
    @staticmethod
    def copy_file_with_progress(process_queue: Queue, copy_item: CopyTaskItem, src: Path, dest: Path):
        block = 4 * 1024 * 1024  # 4 MB
        with open(src, "rb") as fsrc, open(dest, "wb") as fdst:
            while True:
                buf = fsrc.read(block)
                if not buf:
                    break
                fdst.write(buf)
                copy_item.current_size += len(buf) // 1024
                process_queue.put(copy_item)
        try:
            shutil.copystat(src, dest, follow_symlinks=True)
        except OSError as e:
            # import traceback
            # print(traceback.format_exc())
            print("copy task - copy stat error", e)


class FilesRemover:
    @staticmethod
    def start(paths: list[str], queue: Queue):
        deleted_files = []
        for path in paths:
            try:
                os.remove(path)
                deleted_files.append(path)
            except Exception as e:
                print("FilesRemover error:", e)
        queue.put(deleted_files)
        

class MfRemover:
    def start(mf_alias: str, queue: Queue):
        engine = Dbase.create_engine()
        conn = engine.connect()

        stmt = sqlalchemy.select(Thumbs.rel_thumb_path).where(
            Thumbs.mf_alias==mf_alias
        )
        res = conn.execute(stmt).scalars()

        for rel_thumb_path in res:
            abs_thumb_path = Utils.get_abs_thumb_path(rel_thumb_path)
            try:
                os.remove(abs_thumb_path)
                os.rmdir(os.path.dirname(abs_thumb_path))
            except Exception as e:
                pass

        stmt = sqlalchemy.delete(Thumbs.table).where(Thumbs.mf_alias == mf_alias)
        conn.execute(stmt)

        stmt = sqlalchemy.delete(Dirs.table).where(Dirs.mf_alias == mf_alias)
        conn.execute(stmt)

        conn.commit()
        conn.close()
        engine.dispose()


class _DirChangedHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            self.callback(event)


class DirWatcher:
    @staticmethod
    def start(mf_list: list[Mf], queue: Queue):
        observer = Observer()

        for mf in mf_list:
            callback = lambda e, mf=mf: queue.put(
                WatchDogItem(mf=mf, event=e)
            )
            handler = _DirChangedHandler(callback)
            observer.schedule(handler, mf.mf_current_path, recursive=False)
        observer.start()

        try:
            while True:
                sleep(1)
        finally:
            observer.stop()
            observer.join()


class UpdateThumb:

    @staticmethod
    def start(mf: Mf, rel_img_paths: list[str], queue: Queue):

        def _write_thumb(abs_img_path: str, abs_thumb_path: str):
            img_array = ImgUtils.read_img(abs_img_path)
            img_array = ImgUtils.fit_to_thumb(img_array, Static.max_img_size)
            if ImgUtils.write_thumb(abs_thumb_path, img_array):
                return img_array
            return None

        update_thumb_items: list[UpdateThumbItem] = []
        engine = Dbase.create_engine()
        step = 10
        chunked_rel_img_paths = [
            rel_img_paths[i:i+step]
            for i in range(0, len(rel_img_paths), step)
        ]
        for chunk_rel_img_paths in chunked_rel_img_paths:
            values_list: list[dict] = []
            for rel_img_path in chunk_rel_img_paths:
                abs_img_path = Utils.get_abs_any_path(
                    mf.mf_current_path,
                    rel_img_path
                )
                abs_thumb_path = Utils.create_abs_thumb_path(
                    rel_img_path,
                    mf.mf_alias
                )
                rel_thumb_path = Utils.get_rel_thumb_path(abs_thumb_path)
                thumb = _write_thumb(abs_img_path, abs_thumb_path)
                if thumb is not None:
                    update_thumb_items.append(
                        UpdateThumbItem(rel_img_path, thumb)
                    )
                    stats = os.stat(abs_img_path)
                    values_list.append({
                        ClmnNames.rel_item_path: rel_img_path,
                        ClmnNames.rel_thumb_path: rel_thumb_path,
                        ClmnNames.size: int(stats.st_size),
                        ClmnNames.birth: 0,
                        ClmnNames.mod: int(stats.st_mtime),
                        ClmnNames.resol: "none",
                        ClmnNames.coll: "none",
                        ClmnNames.fav: 0,
                        ClmnNames.mf_alias: mf.mf_alias
                    })
            with engine.begin() as conn:
                stmt = sqlalchemy.delete(Thumbs.table)
                stmt = stmt.where(Thumbs.mf_alias == mf.mf_alias)
                stmt = stmt.where(Thumbs.rel_img_path.in_(chunk_rel_img_paths))
                conn.execute(stmt)
                stmt = sqlalchemy.insert(Thumbs.table).values(values_list)
                conn.execute(stmt)

        queue.put(update_thumb_items)
