import json
import os
from datetime import datetime

from pydantic import BaseModel

from cfg import Static

from .lang import Lang
from .utils import MainUtils


class UserFilterErrors:
    was: bool = False


class UserFilterItemModel(BaseModel):
    lang_names: list[str]
    dir_name: str
    value: bool


class UserFilterListModel(BaseModel):
    user_filter_list: list[UserFilterItemModel]


class UserFilter:
    list_: list["UserFilter"] = []
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
        if not os.path.exists(Static.APP_SUPPORT_BACKUP):
            os.makedirs(Static.APP_SUPPORT_BACKUP, exist_ok=True)
        cls.remove_backups()

        now = datetime.now().replace(microsecond=0)
        now = now.strftime("%Y-%m-%d %H-%M-%S") 
        
        filename = f"{now} user_filters.json"
        filepath = os.path.join(Static.APP_SUPPORT_BACKUP, filename)

        if not UserFilter.list_:
            return

        lst: list[UserFilterItemModel] = [item.to_model() for item in cls.list_]
        data = UserFilterListModel(user_filter_list=lst)
        data = data.model_dump()
        data = json.dumps(data, indent=4, ensure_ascii=False)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)

    @classmethod
    def get_backups(cls):
        return [
            entry
            for entry in os.scandir(Static.APP_SUPPORT_BACKUP)
            if entry.is_file() and "user_filters" in entry.name
        ]

    @classmethod
    def remove_backups(cls):
        entries = cls.get_backups()
        entries.sort(key=lambda e: e.stat().st_mtime, reverse=True)
        to_delete = entries[20:]
        for entry in to_delete:
            try:
                os.remove(entry.path)
            except Exception as ex:
                continue

    @classmethod
    def init(cls):
        if not os.path.exists(UserFilter.json_file):
            cls.set_default_filters()
        else:
            try:
                with open(UserFilter.json_file, "r", encoding="utf-8") as f:
                    json_data: dict = json.load(f)
                    validated = cls.validate(json_data)
                    UserFilter.list_ = [
                        cls.from_model(i)
                        for i in validated.user_filter_list
                    ]
            except Exception:
                MainUtils.print_error()
                if cls.get_backups():
                    UserFilterErrors.was = True
                else:
                    cls.set_default_filters()
            
    @classmethod
    def validate(cls, json_data: dict):
        return UserFilterListModel(**json_data)

    @classmethod
    def write_json_data(cls):
        if not cls.list_:
            print("Ошибка записи filters > UserFilter > write json data")
            print("UserFilter.list_ пуст")
            return
        lst: list[UserFilterItemModel] = [item.to_model() for item in cls.list_]
        data = UserFilterListModel(user_filter_list=lst)
        data = json.dumps(data.model_dump(), indent=4, ensure_ascii=False)
        with open(cls.json_file, "w", encoding="utf-8") as f:
            f.write(data)

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


