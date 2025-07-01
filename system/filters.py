import os

from pydantic import BaseModel

from cfg import Static

from .lang import Lang
from .utils import JsonUtils


class UserFilterErrors:
    list_: list[dict] = []


class UserFilterModel(BaseModel):
    lang_names: list[str]
    dir_name: str
    value: bool


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

    @classmethod
    def init(cls):
        json_data: list[dict] = JsonUtils.read_json_data(UserFilter.json_file)

        valid_json = (
            json_data is not None
            and isinstance(json_data, list)
            and all(isinstance(item, dict) for item in json_data)
        )

        if not valid_json:
            UserFilter.list_ = cls.miuz_main_folders()
            cls.write_json_data()
            return

        schema = UserFilterModel.model_json_schema()
        for json_user_filter in json_data:
            if JsonUtils.validate_data(json_user_filter, schema):
                user_filter = UserFilter(**json_user_filter)
                UserFilter.list_.append(user_filter)
            else:
                UserFilterErrors.list_.append(json_user_filter)

    def write_json_data(cls):
        data = [i.get_data() for i in UserFilter.list_]
        JsonUtils.write_json_data(UserFilter.json_file, data)

    @classmethod
    def default_user_filters(cls) -> list[str]:
        """
        Возвращает список словарей
        """

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

        return [product.get_data(), model.get_data()]


class SystemFilter:
    """
    Системный фильтр — фильтрует записи, не подходящие ни под один обычный фильтр.

    Используется для определения записей, не попавших ни под один явно заданный фильтр.
    Должен быть один на систему — предотвращает конфликты логики фильтрации.
    """
    lang_names: list[str] = Lang.system_filter
    value: bool = False


