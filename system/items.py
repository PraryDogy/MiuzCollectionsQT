import os
from dataclasses import dataclass
from multiprocessing import Queue
from typing import Literal

import numpy as np
import sqlalchemy

from .main_folder import Mf


@dataclass(slots=True)
class OneFileInfoItem:
    type_: str
    size: str
    mod: str
    res: str


@dataclass(slots=True)
class ReadImgItem:
    src: str
    img_array: np.ndarray


@dataclass(slots=True)
class NeedResetItem:
    need_reset: bool = False


@dataclass(slots=True)
class OnStartItem:
    mf_list: list["Mf"]


class ScanerItem:
    def __init__(self, mf: Mf, engine: sqlalchemy.Engine, q: Queue):
        super().__init__()
        self.mf = mf
        self.engine = engine
        self.q = q

        self.gui_text: str = "gui_text"
        self.reload_gui = False
        if mf.curr_path:
            self.mf_real_name = os.path.basename(mf.curr_path)
        else:
            self.mf_real_name = os.path.basename(mf.paths[0])
        self.total_count = 0


class CopyTaskItem:
    def __init__(self, dst_dir: str, src_urls: list[str], is_cut: bool):
        super().__init__()
        self.dst_dir = dst_dir
        self.src_urls = src_urls
        self.is_cut = is_cut

        self.current_size: int = 0
        self.total_size: int = 0
        self.current_count: int = 0
        self.total_count: int = 0
        self.dst_urls: list[str] = []
        self.msg: Literal["", "error", "need_replace", "replace_one", "replace_all", "finished"] = ""
