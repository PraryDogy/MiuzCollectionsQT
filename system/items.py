import os
from dataclasses import dataclass
from multiprocessing import Queue
from typing import Literal, Optional

import numpy as np
import sqlalchemy
from watchdog.events import FileSystemEvent

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
class OnStartItem:
    mf_list: list["Mf"]


@dataclass(slots=True)
class ScanerItem:
    mf: Mf
    engine: sqlalchemy.Engine
    queue: Queue
    lng_index: int
    total_count: int


@dataclass(slots=True)
class SingleDirScanerItem:
    data: dict[Mf, list[str]]


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
        self.msg: Literal[
            "none",
            "error",
            "need_replace",
            "replace_one",
            "replace_all",
            "finished"
        ]


@dataclass(slots=True)
class SettingsItem:
    type_: Literal["general", "filters", "new_folder", "edit_folder"]
    content: str


@dataclass(slots=True)
class Buffer:
    type_: Literal["cut", "copy"]
    source_mf: Mf
    files_to_copy: Optional[list[str]]


@dataclass(slots=True)
class WatchDogItem:
    mf: Mf
    event: FileSystemEvent