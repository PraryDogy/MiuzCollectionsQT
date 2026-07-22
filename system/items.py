from dataclasses import dataclass
from typing import Literal

from PyQt6.QtGui import QPixmap


@dataclass(slots=True)
class SettingsItem:
    type_: Literal["general", "filters", "new_folder", "edit_folder"]
    content: str


@dataclass(slots=True)
class DataItem:
    pixmap: QPixmap
    rel_path: str
    fav: bool
    month_year: str
    day_month_year: str
    filename: str
