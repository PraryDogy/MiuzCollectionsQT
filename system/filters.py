import os

from pydantic import BaseModel

from cfg import Static

from .lang import Lang
from .utils import JsonUtils


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
        validate = JsonUtils.validate_data(UserFilter.json_file, UserFilterModel)
        if validate is None:
            data: list[dict] = cls.default_user_filters()
            JsonUtils.write_json_data(UserFilter.json_file, data)
        else:
            data = JsonUtils.read_json_data(UserFilter.json_file)

        UserFilter.list_ = [UserFilter(*list(i.values())) for i in data]

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


