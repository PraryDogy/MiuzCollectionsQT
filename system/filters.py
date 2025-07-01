import json
import os

from pydantic import BaseModel

from cfg import Static

from .lang import Lang
from .utils import JsonUtils, MainUtils


class UserFilterErrors:
    list_: list[dict] = []


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
    
    def get_data(self):
        return {
            i: getattr(self, i)
            for i in self.__slots__
        }
    
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
    def init(cls):
        if not os.path.exists(UserFilter.json_file):
            UserFilter.list_ = cls.default_user_filters()

        try:
            with open(UserFilter.json_file, "r", encoding="utf-8") as f:
                json_data: dict = json.load(f)
                validated = UserFilterListModel(**json_data)
                cls.list_ = [
                    cls.from_model(i)
                    for i in validated.user_filter_list
                ]

        except Exception:
            MainUtils.print_error()
            UserFilter.list_ = cls.default_user_filters()

    @classmethod
    def write_json_data(cls):
        lst: list[UserFilterItemModel] = [item.to_model() for item in cls.list_]
        data = UserFilterListModel(user_filter_list=lst)
        with open(cls.json_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(data.model_dump(), indent=4, ensure_ascii=False))

    @classmethod
    def default_user_filters(cls) -> list["UserFilter"]:
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

        return [product, model]


class SystemFilter:
    """
    Системный фильтр — фильтрует записи, не подходящие ни под один обычный фильтр.

    Используется для определения записей, не попавших ни под один явно заданный фильтр.
    Должен быть один на систему — предотвращает конфликты логики фильтрации.
    """
    lang_names: list[str] = Lang.system_filter
    value: bool = False


