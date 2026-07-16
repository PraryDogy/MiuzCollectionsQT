from dataclasses import dataclass
from multiprocessing import Queue
from typing import Literal, Optional

import numpy as np
import sqlalchemy
from PyQt6.QtGui import QImage, QPixmap

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
    shm_name: str
    shape: tuple[int, ...]
    dtype: str


@dataclass(slots=True)
class BaseScanerItem:
    mf: Mf
    engine: sqlalchemy.Engine
    process_queue: Queue
    response_queue: Queue
    lng_index: int
    total_count: int
    current_count: int


@dataclass(slots=True)
class ForcedScanerItem:
    mf: Mf
    dirs_to_scan: list[str]
    lng_index: int


@dataclass(slots=True)
class CopyTaskItem:
    dst_dir: str
    src_urls: list[str]
    current_percent: int
    copied_bytes: int
    total_bytes: int
    current_file_count: int
    total_file_count: int
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
class WatchDogItem:
    mf: Mf
    src_path: str


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
    rel_img_path: str
    array: np.ndarray


@dataclass(slots=True)
class DbImagesItem:
    rel_img_path: str
    rel_thumb_path: str
    fav: int
    qimage: QImage
    day_month_year: str
    month_year: str


@dataclass(slots=True)
class HashDirSizeItem:
    mf: Mf
    size: int
    total_images: int


@dataclass(slots=True)
class DataItem:
    pixmap: QPixmap
    rel_path: str
    fav: bool
    month_year: str
    day_month_year: str
    filename: str


@dataclass(slots=True)
class ImgViewItem:
    start_data_item: DataItem
    data_items: list[DataItem]
    is_selection: bool
