import os
import re

from PyQt5.QtCore import QThread, pyqtSignal

from cfg import cnf
from database import Dbase, ThumbsMd
import sqlalchemy

class TiffUtils:

    @staticmethod
    def compare_names(src: str, tiff: str):
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


class FindTiffLocal:
    def __init__(self, src: str):
        super().__init__()
        self.src = src
        self.tiff_list = cnf.tiff_images
        self.count = 0

    def run_search(self):
        try:
            tiff_list = self.find_tiffs()
            self.final_tiff = TiffUtils.nearest_len(self.src, tiff_list)
            self.count = 0
        except RuntimeError:
            self.count += 1
            if self.count != 10:
                self.run_search()
            else:
                self.count == 0
                self.final_tiff = None

    def find_tiffs(self) -> list:
        _, src_filename = os.path.split(self.src)

        aa_name = TiffUtils.remove_punct(src_filename)
        aa_name = TiffUtils.remove_stop_words(aa_name)

        tiff_list = []

        for tiff in self.tiff_list:
            _, tiff_name = os.path.split(tiff)

            bb_name = TiffUtils.remove_punct(tiff_name)
            bb_name = TiffUtils.remove_stop_words(bb_name)

            if len(bb_name) <= 2:
                continue

            if TiffUtils.compare_names(src=aa_name, tiff=bb_name):
                tiff_list.append(tiff)

        return tiff_list

    def get_result(self) -> str:
        if self.final_tiff:
            return self.final_tiff
        else:
            return ""


class FindTiffThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, src: str):
        super().__init__()
        self.src = src

    def run(self):
        search = FindTiffLocal(src=self.src)
        search.run_search()
        self.finished.emit(search.get_result())
