import json
import os
from datetime import datetime

from pydantic import BaseModel

from cfg import Static

from .utils import MainUtils


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
    validation_failed: bool = False
    used_defaults: bool = False
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
        return MainFolderItemModel(
            name=self.name,
            paths=self.paths,
            stop_list=self.stop_list,
            curr_path=self.curr_path
        )

    @classmethod
    def from_model(cls, model: MainFolderItemModel) -> "MainFolder":
        return MainFolder(
            name=model.name,
            paths=model.paths,
            stop_list=model.stop_list,
            curr_path=model.curr_path
        )

    @classmethod
    def do_backup(cls):
        if not os.path.exists(Static.APP_SUPPORT_BACKUP):
            os.makedirs(Static.APP_SUPPORT_BACKUP, exist_ok=True)

        if not cls.list_:
            return

        backups = cls.get_backups()
        cls.remove_backups(backups)

        now = datetime.now().replace(microsecond=0)
        now = now.strftime("%Y-%m-%d %H-%M-%S") 
        
        filename = f"{now} main_folders.json"
        filepath = os.path.join(Static.APP_SUPPORT_BACKUP, filename)

        item_list: list[MainFolderItemModel] = [item.to_model() for item in cls.list_]
        data = MainFolderListModel(main_folder_list=item_list)
        data = data.model_dump()
        data = json.dumps(data, indent=4, ensure_ascii=False)
 
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)

    @classmethod
    def get_backups(cls) -> list[os.DirEntry]:
        return [
            entry for entry in os.scandir(Static.APP_SUPPORT_BACKUP)
            if entry.is_file() and "main_folders" in entry.name
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
                pass  # Можно логировать, если нужно

    @classmethod
    def init(cls):
        if not os.path.exists(cls.json_file):
            cls.set_default_main_folders()
            return

        try:
            with open(cls.json_file, "r", encoding="utf-8") as f:
                json_data: dict = json.load(f)

            main_folder_list_model = cls.validate(json_data)
            cls.list_ = [
                cls.from_model(m)
                for m in main_folder_list_model.main_folder_list
            ]

            if not cls.list_:
                raise ValueError("MainFolder.list_ пуст после валидации")

            cls.current = cls.list_[0]

        except Exception:
            MainUtils.print_error()

            if cls.get_backups():
                cls.validation_failed = True
            else:
                cls.used_defaults = True
                cls.set_default_main_folders()

    @classmethod
    def write_json_data(cls):
        if not cls.list_:
            print("Ошибка записи main_folder > MainFolder > write_json_data")
            return

        models = [item.to_model() for item in cls.list_]
        data = MainFolderListModel(main_folder_list=models).model_dump()

        with open(cls.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def validate(cls, json_data: dict):
        return MainFolderListModel(**json_data)

    @classmethod
    def set_default_main_folders(cls) -> list["MainFolder"]:
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

        cls.list_ = [miuz, panacea]
        cls.current = cls.list_[0]
