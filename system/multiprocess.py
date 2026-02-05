import os
import shutil
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep

from cfg import Static
from system.items import CopyItem, DataItem, MultipleInfoItem
from system.shared_utils import ImgUtils, SharedUtils
from system.tasks import Utils


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
        q.put((src, img_array))


class ImgRes:
    undef_text = "Неизвестно"
    @staticmethod
    def psd_read(path: str):
        try:
            w, h = ImgUtils.get_psd_size(path)
            resol= f"{w}x{h}"
        except Exception as e:
            print("multiprocess > ImgRes psd error", e)
            resol = ImgRes.undef_text
        return resol

    @staticmethod
    def read(path: str):
        img_ = ImgUtils.read_img(path)
        if img_ is not None and len(img_.shape) > 1:
            h, w = img_.shape[0], img_.shape[1]
            resol= f"{w}x{h}"
        else:
            resol = ImgRes.undef_text
        return resol

    @staticmethod
    def start(path: str, q: Queue):
        """
        Возвращает str "ширина изображения x высота изображения
        """
        if path.endswith(ImgUtils.ext_psd):
            resol = ImgRes.psd_read(path)
        else:
            resol = ImgRes.read(path)
        q.put(resol)


class MultipleInfo:
    err = " Произошла ошибка"

    @staticmethod
    def start(data_items: list[DataItem], show_hidden: bool, q: Queue):
        info_item = MultipleInfoItem()

        try:
            MultipleInfo._task(data_items, info_item, show_hidden)
            info_item.total_size = SharedUtils.get_f_size(info_item.total_size),
            info_item.total_files = len(list(info_item._files_set))
            info_item.total_files = format(info_item.total_files, ",").replace(",", " ")
            info_item.total_folders = len(list(info_item._folders_set))
            info_item.total_folders = format(info_item.total_folders, ",").replace(",", " ")
            q.put(info_item)

        except Exception as e:
            print("tasks, MultipleInfoFiles error", e)
            info_item.total_size = MultipleInfo.err
            info_item.total_files = MultipleInfo.err
            info_item.total_folders = MultipleInfo.err
            q.put(info_item)

    @staticmethod
    def _task(items: list[dict], info_item: MultipleInfoItem, show_hidden: bool):
        for i in items:
            if i["type_"] == Static.folder_type:
                MultipleInfo.get_folder_size(i, info_item, show_hidden)
                info_item._folders_set.add(i["src"])
            else:
                info_item.total_size += i["size"]
                info_item._files_set.add(i["src"])

    @staticmethod
    def get_folder_size(item: dict, info_item: MultipleInfoItem, show_hidden: bool):
        stack = [item["src"]]
        while stack:
            current_dir = stack.pop()
            try:
                os.listdir(current_dir)
            except Exception as e:
                print("tasks, MultipleItemsInfo error", e)
                continue
            for entry in os.scandir(current_dir):
                if entry.is_dir():
                    info_item._folders_set.add(item["src"])
                    stack.append(entry.path)
                else:
                    if show_hidden:
                        info_item.total_size += entry.stat().st_size
                        info_item._files_set.add(entry.path)
                    if not entry.name.startswith(Static.hidden_symbols):
                        info_item.total_size += entry.stat().st_size
                        info_item._files_set.add(entry.path)


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
