import json
import os
import shutil
from cfg import Static

from .utils import Utils


class Mf:
    current: "Mf" = None
    list_: list["Mf"] = []
    json_file = os.path.join(Static.app_support, "mf.json")
    json_file_backup = os.path.join(Static.app_support, "mf_backup.json")
    __slots__ = [
        "name",
        "paths",
        "stop_list",
        "curr_path",
    ]

    def __init__(
            self,
            name: str = "name",
            paths: list[str] = ["/path", ],
            stop_list: list[str] = ["stop word", ],
            curr_path: str = "",
            **kw
    ):
        """
        Использование:
        - При инициализации из JSON по умолчанию curr_path будет пустым.
        - Значение устанавливается при вызове метода is_available(), который
          проверяет наличие путей из `paths` на диске.
        - Может быть передано явно, если известен корректный путь.  

        name (str): Имя Mf — произвольное, используется для отображения в интерфейсе.
            Важно: имя нельзя изменить после создания. Чтобы изменить, необходимо
            удалить текущий Mf в настройках и создать новый с другим именем.

        paths (list[str]): Список возможных абсолютных путей к папке Mf.
            Все пути указываются вручную пользователем — приложение не ищет их автоматически.
            Используется для определения актуального доступного пути (обычно на сетевом диске).
            Пример: если папка Mf лежит по пути 
            /Volumes/Shares/Studio/MIUZ/Photo/Art/Ready, но при следующем подключении
            сетевые диски смонтированы иначе — и этот путь больше не существует —
            приложение попробует альтернативные пути, например:
            /Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready,
            /Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready и т.д.
            Это позволяет избежать ошибок при изменении порядка монтирования дисков.

        stop_list (list[str]): Список вложенных папок внутри Mf, которые следует игнорировать.
            Пример: если в папке лежат "A", "B", "C", и "C" указана в stop_list,
            то она будет исключена из обработки.

        curr_path (str): Актуальный, проверенный путь к папке из списка `paths`.

        """
        super().__init__()
        self.name = name
        self.paths = paths
        self.stop_list = stop_list
        self.curr_path: str = curr_path
            
    def set_curr_path(self) -> str | None:
        """
        Проверяет и устанавливает путь к Mf.    
        Возвращает доступный путь к Mf или None
        """
        self.curr_path = ""
        for i in self.paths:
            if os.path.exists(i):
                self.curr_path = i
                return self.curr_path
        return None
    
    def get_data(self):
        return {
            i: getattr(self, i)
            for i in self.__slots__
        }

    @classmethod
    def init(cls):
        if not os.path.exists(cls.json_file):
            cls.list_ = cls.get_default_mfs()
            cls.current = cls.list_[0]
            return
        
        try:
            with open(cls.json_file, "r", encoding="utf-8") as file:
                data: list[dict] = json.load(file)
            if not isinstance(data, list):
                cls.list_ = cls.get_default_mfs()
                cls.current = cls.list_[0]
            else:
                for mf in data:
                    if mf["paths"]:
                        item = Mf(**mf)
                        cls.list_.append(item)
                    else:
                        print("папка не имеет путей")
            if len(cls.list_) == 0:
                cls.list_ = cls.get_default_mfs()

            cls.current = cls.list_[0]

        except Exception as e:
            Utils.print_error()
            cls.backup_corruped_file()
            cls.list_ = cls.get_default_mfs()
            cls.current = cls.list_[0]

    @classmethod
    def write_json_data(cls):
        with open(cls.json_file, "w", encoding="utf-8") as file:
            data = [i.get_data() for i in cls.list_]
            json.dump(data, file, ensure_ascii=False, indent=4)

    @classmethod
    def backup_corruped_file(cls):
        shutil.copy2(cls.json_file, cls.json_file_backup)

    @classmethod
    def get_default_mfs(cls) -> list["Mf"]:
        miuz = Mf(
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

        panacea = Mf(
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