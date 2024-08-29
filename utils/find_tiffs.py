import os
import re

from PyQt5.QtCore import pyqtSignal

from .my_thread import MyThread
from cfg import cnf


class TiffUtils:

    @staticmethod
    def filename_in_filename(src: str, tiff: str):
        if src in tiff or tiff in src:
            return True
        return False

    @staticmethod
    def remove_punct(name: str):
        name, _ = os.path.splitext(p=name)
        pattern = re.compile('[\W_]+')
        result = re.sub(pattern, '', name)
        return result

    @staticmethod
    def remove_stop_words(name: str):
        for stop_word in cnf.stop_words:
            name = re.sub(stop_word, '', name, flags=re.IGNORECASE)
        return name

    @staticmethod
    def nearest_len(src: str, tiff_list: list) -> str | None:
        len_src = len(src)
        len_tiffs = {abs(len(i) - len_src) : i for i in tiff_list}

        try:
            return len_tiffs[min(len_tiffs)]
        except ValueError:
            return None


class FindTiffBase:
    def __init__(self, src: str):
        super().__init__()
        self.src = src
        self.tiff_list = cnf.tiff_images
        self.count = 0

    def run(self):
        try:
            tiff_list = self._find_tiffs()
            self.final_tiff = TiffUtils.nearest_len(self.src, tiff_list)
            self.count = 0
        except RuntimeError:
            self.count += 1
            if self.count != 10:
                self.run()
            else:
                self.count == 0
                self.final_tiff = None

    def _find_tiffs(self) -> list:
        src_path, full_src_filename = os.path.split(self.src)
        src_filename = TiffUtils.remove_punct(full_src_filename)
        src_filename = TiffUtils.remove_stop_words(src_filename)
        tiff_list = []

        if len(src_filename) <= 5:
            nearly_files = sorted(os.listdir(src_path))
            posible_tiff = nearly_files[nearly_files.index(full_src_filename) + 1]
            _, ext = os.path.splitext(posible_tiff)

            if ext.lower() in (".tif", ".tiff", ".psd", "psb"):
                posible_tiff = os.path.join(src_path, posible_tiff)
                tiff_list.append(posible_tiff)

            return tiff_list

        for tiff in self.tiff_list:
            _, tiff_name = os.path.split(tiff)

            tiff_filename = TiffUtils.remove_punct(tiff_name)
            tiff_filename = TiffUtils.remove_stop_words(tiff_filename)

            # if len(src_filename) <= 3 or len(tiff_filename) <= 3:
            #     continue

            if src_filename == tiff_filename:
                tiff_list.append(tiff)
                return tiff_list

            if TiffUtils.filename_in_filename(src=src_filename, tiff=tiff_filename):
                tiff_list.append(tiff)

        return tiff_list

    def get_result(self) -> str:
        if self.final_tiff:
            return self.final_tiff
        else:
            return ""


class ThreadFindTiff(MyThread):
    finished = pyqtSignal(str)
    can_remove = pyqtSignal()

    def __init__(self, src: str):
        super().__init__(parent=None)
        self.src = src

    def run(self):
        search = FindTiffBase(src=self.src)
        search.run()
        self.finished.emit(search.get_result())
        self.can_remove.emit()
        self.remove_threads()


class ThreadFindTiffsMultiple(MyThread):
    finished = pyqtSignal(list)
    can_remove = pyqtSignal()

    def __init__(self, files_list: list):
        super().__init__(parent=None)
        self.files_list = files_list

    def run(self):
        tiff_list = []

        for i in self.files_list:
            search = FindTiffBase(src=i)
            search.run()

            res = search.get_result()
            if res:
                tiff_list.append(res)

        self.finished.emit(tiff_list)
        self.can_remove.emit()
        self.remove_threads()