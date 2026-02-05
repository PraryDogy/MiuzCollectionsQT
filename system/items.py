from typing import Literal

import numpy as np


class CopyItem:
    def __init__(self, src_dir: str, dst_dir: str, src_urls: list[str], is_search: bool, is_cut: bool):
        super().__init__()
        self.src_dir = src_dir
        self.dst_dir = dst_dir
        self.src_urls = src_urls
        self.is_search = is_search
        self.is_cut = is_cut

        self.current_size: int = 0
        self.total_size: int = 0
        self.current_count: int = 0
        self.total_count: int = 0
        self.dst_urls: list[str] = []
        self.msg: Literal["", "error", "need_replace", "replace_one", "replace_all", "finished"]


class OneFileInfoItem:
    def __init__(self, type_: str, size: str, mod: str, res: str):
        super().__init__()
        self.type_ = type_
        self.size = size
        self.mod = mod
        self.res = res


class ReadImgItem:
    def __init__(self, src: str, img_array: np.ndarray):
        super().__init__()
        self.src = src
        self.img_array = img_array


class NeedResetItem:
    def __init__(self):
        super().__init__()
        self.need_reset = False