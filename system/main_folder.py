import json
import os
import shutil
from cfg import Static

from .utils import Utils


class Mf:
    current_mf: "Mf" = None
    mf_list: list["Mf"] = []
    json_file = os.path.join(Static.app_support, "mf.json")
    json_file_backup = os.path.join(Static.app_support, "mf_backup.json")
    __slots__ = [
        "mf_alias",
        "mf_paths",
        "mf_stop_list",
        "mf_current_path",
    ]

    def __init__(
            self,
            mf_alias: str = "Имя/Name",
            mf_paths: list[str] = ["/path", ],
            mf_stop_list: list[str] = ["stop word", ],
            mf_current_path: str = "",
            **kw
    ):
        super().__init__()
        self.mf_alias = mf_alias
        self.mf_paths = mf_paths
        self.mf_stop_list = mf_stop_list
        self.mf_current_path: str = mf_current_path
            
    def get_available_path(self) -> str | None:
        """
        Проверяет и устанавливает путь Mf.currpath  
        Возвращает доступный путь Mf.curr_path или None
        """
        self.mf_current_path = ""
        for i in self.mf_paths:
            if os.path.exists(i):
                self.mf_current_path = i
                return self.mf_current_path
        return None
    
    def get_data(self):
        return {
            i: getattr(self, i)
            for i in self.__slots__
        }

    @classmethod
    def init(cls):
        if not os.path.exists(cls.json_file):
            cls.mf_list = cls.get_default_mfs()
            cls.current_mf = cls.mf_list[0]
            return
        
        try:
            with open(cls.json_file, "r", encoding="utf-8") as file:
                data: list[dict] = json.load(file)
            if not isinstance(data, list):
                cls.mf_list = cls.get_default_mfs()
                cls.current_mf = cls.mf_list[0]
            else:
                for mf in data:
                    if mf["paths"]:
                        item = Mf(**mf)
                        cls.mf_list.append(item)
                    else:
                        print("папка не имеет путей")
            if len(cls.mf_list) == 0:
                cls.mf_list = cls.get_default_mfs()

            cls.current_mf = cls.mf_list[0]

        except Exception as e:
            Utils.print_error()
            cls.backup_corruped_file()
            cls.mf_list = cls.get_default_mfs()
            cls.current_mf = cls.mf_list[0]

    @classmethod
    def write_json_data(cls):
        with open(cls.json_file, "w", encoding="utf-8") as file:
            data = [i.get_data() for i in cls.mf_list]
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
