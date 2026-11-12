import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PyQt6.QtGui import QImage

from cfg import Static


@dataclass(slots=True)
class DataItem:
	base_qimage: QImage
	resized_qimages: list[QImage]
	rel_thumb_path: str
	rel_path: str
	abs_path: str
	fav: bool
	day_month_year: str
	hour_min_sec: str
	filename: str
	ext: str


class Filters:
	items = []

	@classmethod
	def validate_json(cls):
		try:
			with open(Static.FILTERS_JSON, "r", encoding="utf-8") as file:
				data: list[str] = json.load(file)
		except Exception as e:
			print("Filters, error reading file", e)
			return False

		if not isinstance(data, list):
			print("Filters: json data не является списком")
			return False

		if len(data) == 0:
			print("Filters: json data список пуст")
			return False

		filters = []
		for i in data:
			if isinstance(i, str):
				filters.append(i)
		if not filters:
			print("Filters, нет string фильтров")
			return False

		return filters

	@classmethod
	def json_to_app(cls, data: list[str]):
		cls.items.clear()
		cls.items = data

	@classmethod
	def write_json_data(cls):
		with open(Static.FILTERS_JSON, "w", encoding="utf-8") as f:
			json.dump(cls.items, f, indent=4, ensure_ascii=False)


class Strings:
	mf_alias = "mf_alias"
	mf_paths = "mf_paths"
	mf_stop_list = "mf_stop_list"


class Mf:
	current_mf: "Mf" = None
	items: list["Mf"] = []
	__slots__ = [
		Strings.mf_alias,
		Strings.mf_paths,
		Strings.mf_stop_list,
	]

	def __init__(self, mf_alias, mf_paths, mf_stop_list):
		super().__init__()
		self.mf_alias: str = mf_alias
		self.mf_paths: list[str] = mf_paths
		self.mf_stop_list: list[str] = mf_stop_list

	@property
	def mf_path(self):
		return self.mf_paths[0]

	@mf_path.setter
	def mf_path(self, value: str):
		self.mf_paths[0] = value

	@property
	def old_mf_path(self):
		return self.mf_paths[1] if len(self.mf_paths) > 1 else None

	@old_mf_path.setter
	def old_mf_path(self, value: str | None):
		if value is None:
			del self.mf_paths[1:]
		elif len(self.mf_paths) > 1:
			self.mf_paths[1] = value
		else:
			self.mf_paths.append(value)

	@classmethod
	def json_to_app(cls, data: list[dict]):
		cls.items.clear()
		for d in data:
			cls.items.append(Mf(**d))

	def create_abs_path(self, rel_path: str) -> str:
		return os.path.join(self.mf_path, rel_path.lstrip(os.sep))

	def create_rel_path(self, abs_path: str) -> str:
		rel = os.path.relpath(abs_path, self.mf_path)
		if rel == os.curdir:
			return os.sep
		return os.sep + rel

	def create_abs_thumb_path(self, rel_img_path: str) -> str:
		clean_rel_path = rel_img_path.strip(os.sep)
		encoded = clean_rel_path.encode('utf-8')
		filename = hashlib.md5(encoded).hexdigest() + ".jpg"
		folder_name = f"{self.mf_alias}-{filename[:2]}"
		new_folder = Static.HASHDIR / folder_name
		new_folder.mkdir(parents=True, exist_ok=True)
		return str(new_folder / filename)

	@classmethod
	def get_rel_thumb_path(cls, abs_thumb_path: str):
		p_base = Path(str(Static.APP_DATA_DIR).strip(os.sep))
		p_abs = Path(abs_thumb_path.strip(os.sep))
		if p_abs.is_relative_to(p_base):
			return os.sep + str(p_abs.relative_to(p_base))

	@classmethod
	def get_abs_thumb_path(cls, rel_thumb_path: str):
		rel_thumb_path = Path(rel_thumb_path.strip(os.sep))
		return Static.APP_DATA_DIR / rel_thumb_path

	def is_root_alive(self):
		return os.path.exists(self.mf_path)
	
	def get_data(self):
		return {i: getattr(self, i) for i in self.__slots__}

	def repair_ignore_list(self):
		self.mf_stop_list = [i for i in self.mf_stop_list if i]

	@classmethod
	def write_json_data(cls):
		with open(Static.MF_JSON, "w", encoding="utf-8") as file:
			data = []
			for i in cls.items:
				i.repair_ignore_list()
				data.append(i.get_data())
			json.dump(data, file, ensure_ascii=False, indent=4)

	@classmethod
	def validate_json(cls):
		try:
			with open(Static.MF_JSON, "r", encoding="utf-8") as file:
				data: list[dict] = json.load(file)
		except Exception as e:
			print("Mf, error reading file", e)
			return None

		if not isinstance(data, list):
			print("Mf: json data не является списком")
			return None

		if len(data) == 0:
			print("Mf: json data список пуст")
			return None

		# валидация по списку словарей
		mf_dicts = (i for i in data if isinstance(i, dict))
		if not mf_dicts:
			print("Mf: список пуст, нет словарей в списке")
			return None

		# валидация по ключам
		slots_set = set(Mf.__slots__)
		all_slots_dicts = []
		for d in mf_dicts:
			if slots_set.issubset(d.keys()):
				cleaned_dict = {key: d[key] for key in slots_set}
				all_slots_dicts.append(cleaned_dict)
		if not all_slots_dicts:
			print("Mf: список пуст по валидации по ключам")
			return None

		# валидация по типу данных
		all_types_dicts = []
		for d in all_slots_dicts:
			base_types_ok = (
				isinstance(d[Strings.mf_alias], str),
				isinstance(d[Strings.mf_paths], list),
				isinstance(d[Strings.mf_stop_list], list)
			)
			if all(base_types_ok):
				lists_are_strings = (
					all(isinstance(i, str) for i in d[Strings.mf_paths]),
					all(isinstance(i, str) for i in d[Strings.mf_stop_list])
				)
				if all(lists_are_strings):
					all_types_dicts.append(d)
		if not all_types_dicts:
			print("Mf: список пуст по валидации по типу данных")
			return None

		# валидация по mf_alias
		unique_mf= {}
		for d in all_types_dicts:
			if d[Strings.mf_alias] not in unique_mf:
				unique_mf[d[Strings.mf_alias]] = d
		unique_mf = list(unique_mf.values())
		if not unique_mf:
			print("Mf: не пройдена проверка по уникальности mf_alias")
			return None

		return unique_mf


class Servers:
	items = []

	@classmethod
	def validate_json(cls):
		try:
			with open(Static.SERVERS_JSON, "r", encoding="utf-8") as file:
				data: list[list[str]] = json.load(file)
		except Exception as e:
			print("Servers, error reading file", e)
			return False

		if not isinstance(data, list):
			print("Servers: json data не является списком")
			return False

		if len(data) == 0:
			print("Servers: json data список пуст")
			return False

		servers = []
		for server_data in data:
			if isinstance(server_data, list):
				if (x for x in server_data if isinstance(x, str)):
					servers.append(server_data)
		if not servers:
			return False

		return servers

	@classmethod
	def json_to_app(cls, data: list[list[str]]):
		cls.items.clear()
		cls.items = data

	@classmethod
	def write_json_data(cls):
		with open(Static.SERVERS_JSON, "w", encoding="utf-8") as file:
			json.dump(cls.items, file, indent=4, ensure_ascii=False)