import json
import os

from cfg import Static

from .utils import Utils


class Mf:
    current_mf: "Mf" = None
    mf_list: list["Mf"] = []
    __json_file = os.path.join(Static.app_support, "mf.json")
    __slots__ = ["mf_alias", "mf_paths", "mf_stop_list", "mf_current_path",]

    def __init__(self, **kw):
        """
        mf_alias: str  
        mf_paths: list[str]    
        mf_stop_list: list[str]     
        mf_current_path: str    
        """
        super().__init__()
        self.mf_alias: str = kw["mf_alias"]
        self.mf_paths: list[str] = kw["mf_paths"]
        self.mf_stop_list: list[str] = kw["mf_stop_list"]
        self.mf_current_path: str = kw["mf_current_path"]

    def get_avaiable_mf_path(self):
        for i in self.mf_paths:
            if os.path.exists(i):
                return i
        return None

    def set_mf_current_path(self, path: str):
        self.mf_current_path = path
    
    def get_data(self):
        return {i: getattr(self, i) for i in self.__slots__}

    @classmethod
    def init(cls):
        if not os.path.exists(cls.__json_file):
            cls.mf_list = cls.get_default_mfs()
            cls.current_mf = cls.mf_list[0]
            return
        
        try:
            with open(cls.__json_file, "r", encoding="utf-8") as file:
                data: list[dict] = json.load(file)

            if not isinstance(data, list):
                cls.mf_list = cls.get_default_mfs()
                cls.current_mf = cls.mf_list[0]
                return

            for mf in data:
                if list(mf.keys()) != Mf.__slots__:
                    print("mf не сооветствует слотам", mf["mf_alias"])
                    continue
                elif not mf["mf_paths"]:
                    print("mf нет путей", mf["mf_alias"])
                    continue
                else:
                    cls.mf_list.append(Mf(**mf))

            if len(cls.mf_list) == 0:
                cls.mf_list = cls.get_default_mfs()
            cls.current_mf = cls.mf_list[0]

        except Exception as e:
            Utils.print_error()
            cls.mf_list = cls.get_default_mfs()
            cls.current_mf = cls.mf_list[0]

    @classmethod
    def write_json_data(cls):
        with open(cls.__json_file, "w", encoding="utf-8") as file:
            data = [i.get_data() for i in cls.mf_list]
            json.dump(data, file, ensure_ascii=False, indent=4)

    @classmethod
    def get_default_mfs(cls) -> list["Mf"]:
        miuz = Mf(
            mf_alias = "miuz",
            mf_paths = [
                '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
                '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
                '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
            ],
            mf_stop_list = [
                "_Archive_Commerce_Брендинг",
                "Chosed",
                "LEVIEV",
            ],
            mf_current_path = ""
        )

        panacea = Mf(
            mf_alias = "panacea",
            mf_paths = [
                '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
                '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
                '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
            ],
            mf_stop_list = [
            ],
            mf_current_path = ""
        )

        return [miuz, panacea]
