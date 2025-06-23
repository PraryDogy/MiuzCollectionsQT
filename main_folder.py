import os
import json
from cfg import Static

NAME = "name"
PATHS = "paths"
STOP_LIST = "stop_list"
_CURR_PATH = "_curr_path"
MAIN_FOLDERS = "main_folders"

class MainFolder:
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    json_file = os.path.join(Static.APP_SUPPORT_DIR, "main_folders.json")
    __slots__ = [NAME, PATHS, STOP_LIST, _CURR_PATH]

    def __init__(self, name: str, paths: list[str], stop_list: list[str]):

        super().__init__()
        self.name = name
        self.paths = paths
        self.stop_list = stop_list
        self._curr_path: str = None # этот аттрибут нужен для сканера
    
    def get_current_path(self):
        return self._curr_path

    def is_available(self) -> str | None:
        """
        Проверяет и устанавливает путь к MainFolder.    
        Возвращает доступный путь к MainFolder или None
        """
        self._curr_path = None
        for i in self.paths:
            if os.path.exists(i):
                self._curr_path = i
                break        
        return self._curr_path

    def get_data(self):
        return [self.name, self.paths, self.stop_list]
    
    @classmethod
    def init(cls):

        if not os.path.exists(MainFolder.json_file):
            data = cls.default_main_folders()
            with open(MainFolder.json_file, "w") as f:
                f.write(json.dumps(obj=data, indent=2, ensure_ascii=False))
        else:
            with open(MainFolder.json_file, "r") as f:
                data = json.loads(f.read())

        MainFolder.list_ = [MainFolder(*item) for item in data]
        MainFolder.current = MainFolder.list_[0]

    @classmethod
    def write_json_data(cls):
        data = [
            i.get_data()
            for i in MainFolder.list_
        ]
        with open(MainFolder.json_file, "w") as f:
            f.write(json.dumps(obj=data, indent=2, ensure_ascii=False))

    
    @classmethod
    def default_main_folders(cls):
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
            ["miuz", miuz_paths, miuz_stop],
            ["panacea", panacea_paths, [] ]
        ]

