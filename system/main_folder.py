import json
import os

from pydantic import BaseModel
from .utils import MainUtils

from cfg import Static


class MainFolderErrors:
    was = False


class MainFolderItemModel(BaseModel):
    name: str
    paths: list[str]
    stop_list: list[str]
    curr_path: str


class MainFolderListModel(BaseModel):
    main_folder_list: list[MainFolderItemModel]


class MainFolder:
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    json_file = os.path.join(Static.APP_SUPPORT_DIR, "main_folders.json")
    __slots__ = ["name", "paths", "stop_list", "curr_path"]

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
        self.curr_path: str = curr_path
    
    def get_instance_copy(self):
        return MainFolder(
            name=self.name,
            paths=self.paths.copy(),
            stop_list=self.stop_list.copy(),
            curr_path=""
        )

    def get_current_path(self):
        return self.curr_path
        
    def is_available(self) -> str | None:
        """
        Проверяет и устанавливает путь к MainFolder.    
        Возвращает доступный путь к MainFolder или None
        """
        self.curr_path = ""
        for i in self.paths:
            if os.path.exists(i):
                self.curr_path = i
                break        
        return self.curr_path

    def to_model(self) -> MainFolderItemModel:
        """
        Преобразует экземпляр MainFolder в объект модели MainFolderItemModel 
        для сериализации или валидации.
        
        :return: Экземпляр MainFolderItemModel с текущими данными.
        """
        return MainFolderItemModel(
            name=self.name,
            paths=self.paths,
            stop_list=self.stop_list,
            curr_path=self.curr_path
        )

    @classmethod
    def from_model(cls, model: MainFolderItemModel) -> "MainFolder":
        """
        Создаёт экземпляр MainFolder из объекта модели MainFolderItemModel.

        :param model: Объект MainFolderItemModel.
        :return: Экземпляр MainFolder.
        """
        return cls(
            name=model.name,
            paths=model.paths,
            stop_list=model.stop_list,
            curr_path=model.curr_path
        )

    @classmethod
    def init(cls):
        """
        Инициализирует список папок `cls.list_`.

        - Если JSON-файл отсутствует — используется предустановленный список.
        - Если файл есть — загружает и валидирует данные из него.
        - В случае ошибки — используется предустановленный список.
        Устанавливает текущую активную папку в `MainFolder.current`.
        """
        if not os.path.exists(cls.json_file):
            cls.list_ = cls.miuz_main_folders()
        else:
            try:
                with open(cls.json_file, "r", encoding="utf-8") as f:
                    json_data: dict = json.load(f)
                    validated = MainFolderListModel(**json_data)
                    cls.list_ = [
                        cls.from_model(m)
                        for m in validated.main_folder_list
                    ]
            except Exception as e:
                MainUtils.print_error()
                cls.list_ = cls.miuz_main_folders()

        MainFolder.current = MainFolder.list_[0]

    @classmethod
    def write_json_data(cls):
        """
        Сохраняет текущий список `cls.list_` в JSON-файл, предварительно 
        сериализовав его через модель MainFolderListModel.

        Использует `ensure_ascii=False` для сохранения Unicode-символов (например, кириллицы).
        """
        lst: list[MainFolderItemModel] = [item.to_model() for item in cls.list_]
        data = MainFolderListModel(main_folder_list=lst)
        with open(cls.json_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(data.model_dump(), indent=4, ensure_ascii=False))


    @classmethod
    def miuz_main_folders(cls) -> list["MainFolder"]:
        miuz = MainFolder(
            "miuz",
            [
                '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
                '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
                '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
            ],
            [
                "_Archive_Commerce_Брендинг",
                "Chosed",
                "LEVIEV",
            ],
            ""
        )

        panacea = MainFolder(
            "panacea",
            [
                '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
                '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
                '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
            ],
            [
            ],
            ""
        )

        return [miuz, panacea]
