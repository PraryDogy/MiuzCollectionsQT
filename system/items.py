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


@dataclass(slots=True)
class CopyTaskItem:
    dst_dir: str
    src_urls: list[str]
    is_cut: bool
    current_size: int
    total_size: int
    current_count: int
    total_count: int
    dst_urls: list[str]
    msg: Literal[
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