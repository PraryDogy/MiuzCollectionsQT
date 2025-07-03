import json
import os
from datetime import datetime

from pydantic import BaseModel

from cfg import Static

from .lang import Lang
from .utils import MainUtils


class UserFilterItemModel(BaseModel):
    lang_names: list[str]
    dir_name: str
    value: bool


class UserFilterListModel(BaseModel):
    user_filter_list: list[UserFilterItemModel]


class UserFilter:
    list_: list["UserFilter"] = []
    validation_failed: bool = False
    json_file = os.path.join(Static.APP_SUPPORT_DIR, "user_filters.json")
    __slots__ = ["lang_names", "dir_name", "value"]

    def __init__(self, lang_names: list[str], dir_name: str, value: bool):
        """
        Аргументы:
        - lang_names (list[str]): Названия фильтра (на русском и английском).    
        - dir_name (str): Имя папки, к которой относится фильтр.
        - value (bool): Активен ли фильтр.    
        """
        self.lang_names = lang_names
        self.dir_name = dir_name
        self.value = value

    def to_model(self) -> UserFilterItemModel:
        return UserFilterItemModel(
            lang_names=self.lang_names,
            dir_name=self.dir_name,
            value=self.value
        )

    @classmethod
    def from_model(cls, model: UserFilterItemModel) -> "UserFilter":
        return UserFilter(
            lang_names=model.lang_names,
            dir_name=model.dir_name,
            value=model.value
        )

    @classmethod
    def do_backup(cls):
        os.makedirs(Static.APP_SUPPORT_BACKUP, exist_ok=True)

        backups = cls.get_backups()
        cls.remove_backups(backups)

        if not cls.list_:
            return

        timestamp = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H-%M-%S")
        filename = f"{timestamp} user_filters.json"
        filepath = os.path.join(Static.APP_SUPPORT_BACKUP, filename)

        models = [item.to_model() for item in cls.list_]
        data = UserFilterListModel(user_filter_list=models).model_dump()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def get_backups(cls):
        return [
            entry
            for entry in os.scandir(Static.APP_SUPPORT_BACKUP)
            if entry.is_file() and "user_filters" in entry.name
        ]

    @classmethod
    def remove_backups(cls, backups: list[os.DirEntry], limit: int = 20):
        if len(backups) <= limit:
            return

        backups.sort(key=lambda e: e.stat().st_mtime, reverse=True)
        for entry in backups[limit:]:
            try:
                os.remove(entry.path)
            except Exception:
                pass  # логировать при необходимости

    @classmethod
    def init(cls):
        if not os.path.exists(cls.json_file):
            cls.set_default_filters()
            return

        try:
            with open(cls.json_file, "r", encoding="utf-8") as f:
                json_data: dict = json.load(f)
                user_filter_list_model = cls.validate(json_data)
                cls.list_ = [
                    cls.from_model(i)
                    for i in user_filter_list_model.user_filter_list
                ]
        except Exception:
            MainUtils.print_error()
            if cls.get_backups():
                cls.validation_failed = True
            else:
                cls.set_default_filters()
            
    @classmethod
    def validate(cls, json_data: dict):
        return UserFilterListModel(**json_data)

    @classmethod
    def write_json_data(cls):
        data = UserFilterListModel(
            user_filter_list=[i.to_model() for i in cls.list_]
        )
        with open(cls.json_file, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(), f, indent=4, ensure_ascii=False)

    @classmethod
    def set_default_filters(cls) -> list["UserFilter"]:
        product = UserFilter(
            ["Продукт", "Product"],
            "1 IMG",
            False
        )
        
        model = UserFilter(
            ["Модели", "Model"],
            "2 MODEL IMG",
            False,
        )

        cls.list_ = [product, model]


class SystemFilter:
    """
    Системный фильтр — фильтрует записи, не подходящие ни под один обычный фильтр.

    Используется для определения записей, не попавших ни под один явно заданный фильтр.
    Должен быть один на систему — предотвращает конфликты логики фильтрации.
    """
    lang_names: list[str] = Lang.system_filter
    value: bool = False


