from dataclasses import dataclass
from typing import Literal

from PyQt6.QtGui import QImage, QPixmap


@dataclass(slots=True)
class SettingsItem:
	type_: Literal["general", "filters", "new_folder", "edit_folder"]
	content: str


@dataclass(slots=True)
class DataItem:
	base_qimage: QImage
	resized_qimages: list[QImage]
	rel_thumb_path: str
	rel_path: str
	fav: bool
	day_month_year: str
	hour_min_sec: str
	filename: str
	ext: str