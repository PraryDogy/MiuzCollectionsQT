import os
import shutil
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

from cfg import Static, cfg
from system.items import CopyItem, OneFileInfoItem, ReadImgItem
from system.shared_utils import ImgUtils, SharedUtils
from system.tasks import Utils

from .lang import Lng


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
    
    def terminate(self):
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


class CopyWorker(BaseProcessWorker):
    def __init__(self, target, args):
        self.proc_q = Queue()
        self.gui_q = Queue()
        super().__init__(target, (*args, self.proc_q, self.gui_q))


class CopyTask:
    @staticmethod
    def start(copy_item: CopyItem, proc_q: Queue, gui_q: Queue):

        if copy_item.is_search or copy_item.src_dir != copy_item.dst_dir:
            src_dst_urls = CopyTask.get_another_dir_urls(copy_item)
        else:
            src_dst_urls = CopyTask.get_same_dir_urls(copy_item)

        copy_item.dst_urls = [dst for src, dst in src_dst_urls]

        total_size = 0
        for src, dest in src_dst_urls:
            total_size += os.path.getsize(src)

        copy_item.total_size = total_size // 1024
        copy_item.total_count = len(src_dst_urls)
        replace_all = False

        for count, (src, dest) in enumerate(src_dst_urls, start=1):

            if src.is_dir():
                continue

            if not replace_all and dest.exists() and src.name == dest.name:
                copy_item.msg = "need_replace"
                proc_q.put(copy_item)
                while True:
                    sleep(1)
                    if not gui_q.empty():
                        new_copy_item: CopyItem = gui_q.get()
                        if new_copy_item.msg == "replace_one":
                            break
                        elif new_copy_item.msg == "replace_all":
                            replace_all = True
                            break

            os.makedirs(dest.parent, exist_ok=True)
            copy_item.current_count = count
            copy_item.msg = ""
            try:
                if os.path.exists(dest) and dest.is_file():
                    os.remove(dest)
                CopyTask.copy_file_with_progress(proc_q, copy_item, src, dest)
            except Exception as e:
                print("CopyTask copy error", e)
                copy_item.msg = "error"
                proc_q.put(copy_item)
                return
            if copy_item.is_cut and not copy_item.is_search:
                os.remove(src)
                "удаляем файлы чтобы очистить директории"

        if copy_item.is_cut and not copy_item.is_search:
            for src, dst in src_dst_urls:
                if src.is_dir() and src.exists():
                    try:
                        shutil.rmtree(src)
                    except Exception as e:
                        print("copy task error dir remove", e)
        
        copy_item.msg = "finished"
        proc_q.put(copy_item)

    @staticmethod
    def get_another_dir_urls(copy_item: CopyItem):
        src_dst_urls: list[tuple[Path, Path]] = []
        src_dir = Path(copy_item.src_dir)
        dst_dir = Path(copy_item.dst_dir)
        for url in copy_item.src_urls:
            url = Path(url)
            if url.is_dir():
                # мы добавляем директорию в список копирования
                # чтобы потом можно было удалить ее при вырезании
                src_dst_urls.append((url, url))
                for filepath in url.rglob("*"):
                    if filepath.is_file():
                        rel_path = filepath.relative_to(src_dir)
                        new_path = dst_dir.joinpath(rel_path)
                        src_dst_urls.append((filepath, new_path))
            else:
                new_path = dst_dir.joinpath(url.name)
                src_dst_urls.append((url, new_path))
        return src_dst_urls
    
    @staticmethod
    def get_same_dir_urls(copy_item: CopyItem, copy_name: str = ""):
        src_dst_urls: list[tuple[Path, Path]] = []
        dst_dir = Path(copy_item.dst_dir)
        for url in copy_item.src_urls:
            url = Path(url)
            url_with_copy = dst_dir.joinpath(url.name)
            counter = 2
            while url_with_copy.exists():
                name, ext = os.path.splitext(url.name)
                new_name = f"{name} {copy_name} {counter}{ext}"
                url_with_copy = dst_dir.joinpath(new_name)
                counter += 1
            if url.is_file():
                src_dst_urls.append((url, url_with_copy))
            else:
                for filepath in url.rglob("*"):
                    if filepath.is_file():
                        rel_path = filepath.relative_to(url)
                        new_url = url_with_copy.joinpath(rel_path)
                        src_dst_urls.append((filepath, new_url))
        return src_dst_urls
    
    @staticmethod
    def copy_file_with_progress(proc_q: Queue, copy_item: CopyItem, src: Path, dest: Path):
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