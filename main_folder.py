import os

NAME = "name"
PATHS = "paths"
STOP_LIST = "stop_list"
_CURR_PATH = "_curr_path"
MAIN_FOLDERS = "main_folders"

class MainFolder:
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    __slots__ = [NAME, PATHS, STOP_LIST, _CURR_PATH]
    json_key = "main_folders"

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

    @classmethod
    def get_data(cls):
        """
        Возвращает данные основных папок в виде словаря.
        Формат:
        {"main_folders": [(имя: str, пути: list[str], стоп-слова: list[str]), ...]}
        Пример:
        {"main_folders": [("Some Name", ["/path/1", "/path/2"], ["tmp", "cache"])]}
        """
        data = {
            MainFolder.json_key: [
                [i.name, i.paths, i.stop_list]
                for i in MainFolder.list_
            ]
        }
        return data
    
    @classmethod
    def init(cls, json_data: dict):
        """
        структуру смотри в get_data
        """
        main_folders: list = json_data.get(MainFolder.json_key)
        if not main_folders:
            MainFolder.list_ = cls.default_main_folders()
            MainFolder.current = MainFolder.list_[0]
            return
        else:
            MainFolder.list_.clear()
            for name, path_list, stop_list in main_folders:
                item = MainFolder(name, path_list, stop_list)
                MainFolder.list_.append(item)
            MainFolder.current = MainFolder.list_[0]
    
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
            MainFolder("miuz", miuz_paths, miuz_stop),
            MainFolder("panacea", panacea_paths, []),
        ]

