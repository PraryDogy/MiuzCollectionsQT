import json
import os
from typing import get_type_hints

from cfg import Static


class Strings:
    mf_alias = "mf_alias"
    mf_paths = "mf_paths"
    mf_stop_list = "mf_stop_list"
    mf_current_path = "mf_current_path"



class Mf:
    current_mf: "Mf" = None
    items: list["Mf"] = []
    __slots__ = [
        Strings.mf_alias,
        Strings.mf_paths,
        Strings.mf_stop_list,
        Strings.mf_current_path,
    ]

    def __init__(self, mf_alias, mf_paths, mf_stop_list, mf_current_path):
        super().__init__()
        self.mf_alias: str = mf_alias
        self.mf_paths: list[str] = mf_paths
        self.mf_stop_list: list[str] = mf_stop_list
        self.mf_current_path: str = mf_current_path

    @classmethod
    def validate_json(cls):
        try:
            with open(Static.external_mf, "r", encoding="utf-8") as file:
                data: list[dict] = json.load(file)
        except Exception as e:
            print("Mf, error reading file", e)
            return False

        if not isinstance(data, list):
            print("Mf: json data не является списком")
            return False

        if len(data) == 0:
            print("Mf: json data список пуст")
            return False

        # валидация по списку словарей
        mf_dicts = (i for i in data if isinstance(i, dict))
        if not mf_dicts:
            print("Mf: список пуст, нет словарей в списке")
            return False

        # валидация по ключам
        slots_set = set(Mf.__slots__)
        all_slots_dicts = []
        for d in mf_dicts:
            if slots_set.issubset(d.keys()):
                cleaned_dict = {key: d[key] for key in slots_set}
                all_slots_dicts.append(cleaned_dict)
        if not all_slots_dicts:
            print("Mf: список пуст по валидации по ключам")
            return False

        # валидация по типу данных
        all_types_dicts = []
        for d in all_slots_dicts:
            base_types_ok = (
                isinstance(d[Strings.mf_alias], str),
                isinstance(d[Strings.mf_paths], list),
                isinstance(d[Strings.mf_stop_list], list),
                isinstance(d[Strings.mf_current_path], str)
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
            return False

        # валидация по mf_alias
        unique_mf= {}
        for d in all_types_dicts:
            if d[Strings.mf_alias] not in unique_mf:
                unique_mf[d[Strings.mf_alias]] = d
        unique_mf = list(unique_mf.values())
        if not unique_mf:
            print("Mf: не пройдена проверка по уникальности mf_alias")
            return False

        return unique_mf

    @classmethod
    def json_to_app(cls, data: list[dict]):
        cls.items.clear()
        for d in data:
            cls.items.append(Mf(**d))
        # for i in cls.items:
        #     print(i.mf_alias)
        # os._exit(1)

    def get_avaiable_mf_path(self):
        for i in self.mf_paths:
            if os.path.exists(i):
                return i
        return None

    def set_mf_current_path(self, path: str):
        self.mf_current_path = path
    
    def get_data(self):
        return {i: getattr(self, i) for i in self.__slots__}

    @classmethod
    def write_json_data(cls):
        with open(Static.external_mf, "w", encoding="utf-8") as file:
            data = [i.get_data() for i in cls.items]
            json.dump(data, file, ensure_ascii=False, indent=4)
