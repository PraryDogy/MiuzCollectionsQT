NAME = "name"
PATHS = "paths"
STOP_LIST = "stop_list"
CURRENT_PATH = "current_path"

class MainFolder:
    current: "MainFolder" = None
    list_: list["MainFolder"] = []
    __slots__ = [NAME, PATHS, STOP_LIST, CURRENT_PATH]

    def __init__(self, name: str, paths: list[str], stop_list: list[str]):
        super().__init__()
        self.name = name
        self.paths = paths
        self.stop_list = stop_list
        self.current_path: str = None # этот аттрибут нужен для сканера
        MainFolder.list_.append(self)

    @classmethod
    def init(cls):
        MainFolder.current = MainFolder.list_[0]

    @classmethod
    def get_data(cls):
        """возвращает данные о брендах в виде словаря"""
        return {
            main_folder.name: {
                PATHS: main_folder.paths,
                STOP_LIST: main_folder.stop_list
            }
            for main_folder in MainFolder.list_
        }
    
    @classmethod
    def setup_main_folders(cls, json_data: dict):
        for main_folder in MainFolder.list_:
            new_data: dict = json_data.get(main_folder.name)
            if new_data:
                main_folder.paths = new_data.get(PATHS)
                main_folder.stop_list = new_data.get(STOP_LIST)

MainFolder(
    name="miuz",
    paths=[
        '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
    ],
    stop_list=[
        "_Archive_Commerce_Брендинг",
        "Chosed",
        "LEVIEV"
    ]
)

MainFolder(
    name="panacea",
    paths=[
        '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
    ],
    stop_list=[
    ]
)