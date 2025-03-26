NAME = "name"
COLL_FOLDERS = "coll_folders"
STOP_COLLS = "stop_colls"
COLL_FOLDER_PATH = "coll_folder_path"

class Brand:
    current: "Brand" = None
    brands_list: list["Brand"] = []
    __slots__ = [NAME, COLL_FOLDERS, STOP_COLLS, COLL_FOLDER_PATH]

    def __init__(self, name: str, coll_folders: list[str], stop_colls: list[str]):
        super().__init__()
        self.name = name
        self.coll_folders = coll_folders
        self.stop_colls = stop_colls
        self.coll_folder_path: str = None
        Brand.brands_list.append(self)

    @classmethod
    def init(cls):
        Brand.current = Brand.brands_list[0]

    @classmethod
    def get_brands_data(cls):
        """возвращает данные о брендах в виде словаря"""
        return {
            brand.name: {
                COLL_FOLDERS: brand.coll_folders,
                STOP_COLLS: brand.stop_colls
            }
            for brand in Brand.brands_list
        }
    
    @classmethod
    def setup_brands(cls, json_data: dict):
        for brand in Brand.brands_list:
            new_data: dict = json_data.get(brand.name)
            if new_data:
                brand.coll_folders = new_data.get(COLL_FOLDERS)
                brand.stop_colls = new_data.get(STOP_COLLS)


Brand(
    name="miuz",
    coll_folders=[
        '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
    ],
    stop_colls=[
        "_Archive_Commerce_Брендинг",
        "Chosed",
        "LEVIEV"
    ]
)

Brand(
    name="panacea",
    coll_folders=[
        '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
    ],
    stop_colls=[
    ]
)