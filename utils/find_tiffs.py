import os
import re
from difflib import SequenceMatcher

from PyQt5.QtCore import pyqtSignal

from cfg import cnf

from .my_thread import MyThread


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
        self.count = 0
        self.run()

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
        root, full_jpg = os.path.split(self.src)
        short_jpg = TiffUtils.remove_punct(full_jpg)
        short_jpg = TiffUtils.remove_stop_words(short_jpg)
        result = []

        if len(short_jpg) <= 5:
            files = sorted(os.listdir(root))
            posible_tiff = files[files.index(full_jpg) + 1]

            if posible_tiff.lower().endswith((".tif", ".tiff", ".psd", "psb")):
                posible_tiff = os.path.join(root, posible_tiff)
                result.append(posible_tiff)

            return result

        tiff_list = [
            os.path.join(root, file)
            for file in os.listdir(root)
            if file.lower().endswith((".tif", ".tiff", ".psd", "psb"))
            ]

        for tiff in tiff_list:
            _, tiff_name = os.path.split(tiff)

            tiff_filename = TiffUtils.remove_punct(tiff_name)
            tiff_filename = TiffUtils.remove_stop_words(tiff_filename)

            if short_jpg == tiff_filename:
                result.append(tiff)
                return result

            if TiffUtils.filename_in_filename(src=short_jpg, tiff=tiff_filename):
                result.append(tiff)

        return result

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
            res = search.get_result()
            if res:
                tiff_list.append(res)

        self.finished.emit(tiff_list)
        self.can_remove.emit()
        self.remove_threads()