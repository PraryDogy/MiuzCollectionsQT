import json
import os
import traceback

from cfg import Static


class MainFolder:
    is_first_load = None
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    json_file = os.path.join(Static.APP_SUPPORT_DIR, "main_folders.json")
    __slots__ = ["name", "paths", "stop_list", "_curr_path"]

    def __init__(self, name: str, paths: list[str], stop_list: list[str], curr_path: str):
        """
        curr_path (str): Актуальный, проверенный путь к папке из списка `paths`.

        Использование:
        - При инициализации из JSON по умолчанию curr_path будет пустым.
        - Значение устанавливается при вызове метода is_available(), который
          проверяет наличие путей из `paths` на диске.
        - Может быть передано явно, если известен корректный путь.  

        name (str): Имя MainFolder — произвольное, используется для отображения в интерфейсе.
            Важно: имя нельзя изменить после создания. Чтобы изменить, необходимо
            удалить текущий MainFolder в настройках и создать новый с другим именем.

        paths (list[str]): Список возможных абсолютных путей к папке MainFolder.
            Все пути указываются вручную пользователем — приложение не ищет их автоматически.
            Используется для определения актуального доступного пути (обычно на сетевом диске).
            Пример: если папка MainFolder лежит по пути 
            /Volumes/Shares/Studio/MIUZ/Photo/Art/Ready, но при следующем подключении
            сетевые диски смонтированы иначе — и этот путь больше не существует —
            приложение попробует альтернативные пути, например:
            /Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready,
            /Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready и т.д.
            Это позволяет избежать ошибок при изменении порядка монтирования дисков.

        stop_list (list[str]): Список вложенных папок внутри MainFolder, которые следует игнорировать.
            Пример: если в папке лежат "A", "B", "C", и "C" указана в stop_list,
            то она будет исключена из обработки.
        """
        super().__init__()
        self.name = name
        self.paths = paths
        self.stop_list = stop_list
        self._curr_path: str = curr_path

    def set_name(self, value: str):
        self.name = value
    
    def get_instance_copy(self):
        return MainFolder(
            name=self.name,
            paths=self.paths.copy(),
            stop_list=self.stop_list.copy(),
            curr_path=""
        )

    def get_current_path(self):
        return self._curr_path
    
    def get_data(self):
        return [getattr(self, i) for i in self.__slots__]
    
    def get_types(self):
        return [type(getattr(self, i))for i in self.__slots__]

    def is_available(self) -> str | None:
        """
        Проверяет и устанавливает путь к MainFolder.    
        Возвращает доступный путь к MainFolder или None
        """
        self._curr_path = ""
        for i in self.paths:
            if os.path.exists(i):
                self._curr_path = i
                break        
        return self._curr_path

    @classmethod
    def init(cls):
        validate = cls.validate_data()
        if validate is None:
            cls.is_first_load = True
            data = cls.miuz_main_folders()
            with open(MainFolder.json_file, "w", encoding='utf-8') as f:
                f.write(json.dumps(obj=data, indent=2, ensure_ascii=False))
        else:
            with open(MainFolder.json_file, "r", encoding='utf-8') as f:
                data = json.loads(f.read())

        MainFolder.list_ = [MainFolder(*item) for item in data]
        MainFolder.current = MainFolder.list_[0]

    @classmethod
    def validate_data(cls) -> list | None:
        try:
            if not os.path.exists(MainFolder.json_file):
                return None

            with open(MainFolder.json_file, "r", encoding='utf-8') as f:
                data: list[list] = json.load(f)

            if not isinstance(data, list):
                print("Ошибка в файле main_folders.json)")
                print("ожидается list, получен: ", type(data).__name__)
                return None            

            test = MainFolder("name", ["paths", ], ["stop list", ], "")
            cls_types = test.get_types()

            for idx, main_folder in enumerate(data):
                json_types = [type(i) for i in main_folder]

                if len(cls_types) != len(main_folder):
                    print(f"Ошибка в элементе [{idx}] файла main_folders.json")
                    print(f"ожидается длина {len(cls_types)}, получена длина {len(main_folder)}")
                    return None

                elif cls_types != json_types:
                    print(f"Ошибка в элементе [{idx}] файла main_folders.json")
                    print(f"ожидается {cls_types}, получен {json_types}")
                    return None

            return True
        except Exception as e:
            print()
            print(traceback.format_exc())
            print()
            return None

    @classmethod
    def write_json_data(cls):
        data = [i.get_data() for i in MainFolder.list_]
        with open(MainFolder.json_file, "w", encoding='utf-8') as f:
            f.write(json.dumps(obj=data, indent=2, ensure_ascii=False))

    @classmethod
    def miuz_main_folders(cls):
        miuz_paths = [
            '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
        ]
        miuz_stop = [
            "_Archive_Commerce_Брендинг",
            "Chosed",
            "LEVIEV",
        ]

        panacea_paths = [
            '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
            '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
            '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
        ]

        return [
            ["miuz", miuz_paths, miuz_stop, ""],
            ["panacea", panacea_paths, [], ""]
        ]
    
    @classmethod
    def example_main_folders(cls):
        return [
            [
                "Имя (Name)",
                ["путь/к/папке/с/коллекциями", "path/to/collections/folder"],
                ["коллекция 1", "коллекция 2", "collection 1", "collection 2"],
                ""
            ]
        ]

    @classmethod
    def set_miuz_folders(cls):
        data = cls.miuz_main_folders()
        MainFolder.list_ = [MainFolder(*item) for item in data]
