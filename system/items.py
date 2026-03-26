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


@dataclass(slots=True)
class ScanerDirItem:
    """
    Параметры:
    - rel_path: относительный путь к подкаталогу относительно `Mf.curr_path`.
      Пример:
        - Mf.curr_path = /User/Downloads/parent/folder
        - подкаталог = /User/Downloads/parent/folder/subfolder
        - rel_path = /subfolder
    - mod: дата модификации каталога (os.stat.st_mtime)
    """
    abs_path: str
    rel_path: str
    mod: int


@dataclass(slots=True)
class ScanerImgItem:
    """
    Параметры:
    - abs_img_path: полный путь до изображения
    - size: размер изображения в байтах
    - mod: os.stat.st_mtime
    - rel_thumb_path: путь до миниатюры /hashdir/thumb.jpg
    """
    abs_img_path: str
    size: int
    mod: int
    rel_thumb_path: str = ""


@dataclass(slots=True)
class UpdateThumbItem:
    rel_img_path_to_array: dict[str, np.ndarray]