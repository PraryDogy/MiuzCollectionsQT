import json
import os
import shutil

from cfg import Static, JsonData

from .lang import Lng
from .utils import MainUtils


class UserFilter:
    list_: list["UserFilter"] = []
    validation_failed: bool = False
    json_file = os.path.join(Static.APP_SUPPORT_DIR, "user_filters.json")
    json_file_backup = os.path.join(Static.APP_SUPPORT_DIR, "user_filters_backup.json")
    __slots__ = ["lang_names", "dir_name", "value"]

    def __init__(
            self,
            lang_names: list[str] = ["filter eng, filter rus"],
            dir_name: str = "filter_dir",
            value: bool = False,
            **kw
    ):
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
        if not os.path.exists(cls.json_file):
            cls.list_ = cls.get_default_filters()
            return
        
        try:
            with open(cls.json_file, "r", encoding="utf-8") as file:
                data: list[dict] = json.load(file)
            if not isinstance(data, list):
                cls.list_ = cls.get_default_filters()
            else:
                for item in data:
                    item = UserFilter(**item)
                    cls.list_.append(item)
            if len(cls.list_) == 0:
                cls.list_ = cls.get_default_filters()

        except Exception as e:
            MainUtils.print_error()
            cls.backup_corruped_file()
            cls.list_ = cls.get_default_filters()

    @classmethod
    def write_json_data(cls):
        with open(cls.json_file, "w", encoding="utf-8") as file:
            data = [i.get_data() for i in cls.list_]
            json.dump(data, file, ensure_ascii=False, indent=4)

    @classmethod
    def backup_corruped_file(cls):
        shutil.copy2(cls.json_file, cls.json_file_backup)

    @classmethod
    def get_default_filters(cls) -> list["UserFilter"]:
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
    lang_names: list[str] = Lng.system_filter
    value: bool = False