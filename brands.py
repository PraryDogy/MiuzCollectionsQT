class Brand:
    current: int = 0
    brands_list: list["Brand"] = []

    # имена соответствуют аттрибутам класса Brand: coll_folders и stop_colls
    # нельзя менять
    var_name = "name"
    var_coll_folders = "coll_folders"
    var_stop_colls = "stop_colls"

    __slots__ = [var_name, var_coll_folders, var_stop_colls]

    def __init__(self, name: str, coll_folders: list[str], stop_colls: list[str]):
        super().__init__()
        self.name = name
        self.coll_folders = coll_folders
        self.stop_colls = stop_colls

        Brand.brands_list.append(self)

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