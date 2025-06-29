import json
import os

from cfg import Static

from .lang import Lang
from .utils import MainUtils


class UserFilter:
    first_load = False
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
        return [getattr(self, i) for i in self.__slots__]

    def get_types(self):
        return [type(getattr(self, i))for i in self.__slots__]

    @classmethod
    def init(cls):
        validate = cls.validate_data()
        if validate is None:
            cls.first_load = True
            data = []
        else:
            with open(UserFilter.json_file, "r", encoding='utf-8') as f:
                data = json.loads(f.read())
        UserFilter.list_ = [UserFilter(*item) for item in data]

    @classmethod
    def set_miuz_filters(cls):
        data = cls.default_user_filters()
        with open(UserFilter.json_file, "w", encoding='utf-8') as f:
            f.write(json.dumps(obj=data, indent=4, ensure_ascii=False))

    @classmethod
    def validate_data(cls) -> list | None:
        try:
            if not os.path.exists(UserFilter.json_file):
                return None

            with open(UserFilter.json_file, "r", encoding='utf-8') as f:
                data: list[list] = json.load(f)

            if not isinstance(data, list):
                print("Ошибка в файле main_folders.json)")
                print("ожидается list, получен: ", type(data).__name__)
                return None            

            test = UserFilter(["Rus", "Eng"], "1 IMG", False)
            cls_types = test.get_types()

            for idx, user_filter in enumerate(data):
                json_types = [type(i) for i in user_filter]

                if len(cls_types) != len(user_filter):
                    print(f"Ошибка в элементе [{idx}] файла main_folders.json")
                    print(f"ожидается длина {len(cls_types)}, получена длина {len(user_filter)}")
                    return None

                elif cls_types != json_types:
                    print(f"Ошибка в элементе [{idx}] файла main_folders.json")
                    print(f"ожидается {cls_types}, получен {json_types}")
                    return None

            return True
        except Exception as e:
            MainUtils.print_error()
            return None

    @classmethod
    def write_json_data(cls):
        data = [i.get_data() for i in UserFilter.list_]
        with open(UserFilter.json_file, "w", encoding='utf-8') as f:
            f.write(json.dumps(obj=data, indent=4, ensure_ascii=False))

    @classmethod
    def default_user_filters(cls):
        return [
            [["Продукт", "Product"], "1 IMG", False],
            [["Модели", "Model"], "2 MODEL IMG", False]
        ]


class SystemFilter:
    """
    Системный фильтр — фильтрует записи, не подходящие ни под один обычный фильтр.

    Используется для определения записей, не попавших ни под один явно заданный фильтр.
    Должен быть один на систему — предотвращает конфликты логики фильтрации.
    """
    lang_names: list[str] = Lang.system_filter
    value: bool = False


