import json
import os
import traceback

from cfg import Static


class Slots:
    name = "name"
    paths = "paths"
    stop_list = "stop_list"
    _curr_path = "_curr_path"


class MainFolder:
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    json_file = os.path.join(Static.APP_SUPPORT_DIR, "main_folders.json")
    __slots__ = [Slots.name, Slots.paths, Slots.stop_list, Slots._curr_path]

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
        validate = cls.validate_data()
        if validate is None:
            if os.path.exists(MainFolder.json_file):
                os.remove(MainFolder.json_file)
            data = cls.default_main_folders()
            with open(MainFolder.json_file, "w") as f:
                f.write(json.dumps(obj=data, indent=2, ensure_ascii=False))
        else:
            with open(MainFolder.json_file, "r") as f:
                data = json.loads(f.read())

        MainFolder.list_ = [MainFolder(*item) for item in data]
        MainFolder.current = MainFolder.list_[0]

    @classmethod
    def validate_data(cls) -> list | None:
        try:
            with open(MainFolder.json_file, "r") as f:
                data: list[list] = json.load(f)

            if not isinstance(data, list):
                print("MainFolders json: общий тип не соответствует list")
                return None            

            cls_types = [str, list, list]

            for main_folder in data:
                if len(cls_types) != len(main_folder):
                    print("MainFolders json: длина элемента MainFolder не соответсвует нужной длине")
                    return None

            for main_folder in data:
                if cls_types != [type(i) for i in main_folder]:
                    print("MainFolders json: тип элементов MainFolder не соответсвует нужным типам")
                    return None

            return True
        except Exception as e:
            print()
            print(traceback.format_exc())
            print()
            return None

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

