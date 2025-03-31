NAME = "name"
PATHS = "paths"
STOP_LIST = "stop_list"
CURRENT_PATH = "current_path"
MAIN_FOLDERS = "main_folders"

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

    @classmethod
    def init(cls):
        if MainFolder.list_:
            MainFolder.current = MainFolder.list_[0]
        else:
            print("MainFolder.list_ пуст")

    @classmethod
    def get_data(cls):
        """возвращает данные о брендах в виде словаря"""
        data = {
            MAIN_FOLDERS: {
                main_folder.name: {
                    PATHS: main_folder.paths,
                    STOP_LIST: main_folder.stop_list
                }
                for main_folder in MainFolder.list_
            }
        }

        return data
    
    @classmethod
    def setup_main_folders(cls, json_data: dict):
        json_main_folders: dict = json_data.get(MAIN_FOLDERS)

        if not json_main_folders:
            # если в json нет данных, мы останавливаем извлечение данных
            # из json, оставляя список MainFolder.list_ по умолчанию
            # данные берутся из классов, определенных ниже
            return

        else:
            # в случае, если в json есть данные о папках main_folders
            # мы очищаем список от установленных по умолчанию main_folders
            MainFolder.list_.clear()


        for main_folder_name, data in json_main_folders.items():
            data: dict
            paths = data.get(PATHS)
            stop_list = data.get(STOP_LIST)

            item = MainFolder(
                name=main_folder_name,
                paths=paths,
                stop_list=stop_list
            )

            MainFolder.list_.append(item)


miuz = MainFolder(
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

panacea = MainFolder(
    name="panacea",
    paths=[
        '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
    ],
    stop_list=[
    ]
)

MainFolder.list_.append(miuz)
MainFolder.list_.append(panacea)