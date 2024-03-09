import json
import os
import shutil
from datetime import datetime
from typing import Literal, Type, Union

from lang import Eng, Rus


class User:
    def __init__(self) -> None:
        super().__init__()

        self.key: dict = {"db_ver": 1.0, "load": True}

        self.coll_folder: str = os.path.join(
            "Volumes",
            "Shares",
            "Marketing",
            "Photo",
            "_Collections"
            )
        
        self.down_folder: str = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
            )

        self.curr_coll: str = "miuzcollections_all"
        self.user_lng: str = "en"
        self.zoom: bool = False
        self.move_jpg = True
        self.move_layers = False

        self.root_g: dict = {
            "ax": 100,
            "ay": 100,
            "aw": 700,
            "ah": 500
            }

        self.imgview_g: dict = {
            "ax": 100,
            "ay": 100,
            "aw": 700,
            "ah": 500
            }
        
        self.cust_fltr_vals: dict = {
            "prod": False,
            "mod": False
            }

        self.sys_fltr_vals: dict = {
            "other" : False
            }

        self.cust_fltr_names: dict = {
            "prod": "1 IMG",
            "mod": "2 Model IMG"
            }

        self.stop_words: dict = [
            "копия",
            "copy",
            "1x1",
            "preview",
            "square"
            ]
        
        self.stop_colls: dict = [
            "_Archive_Commerce_Брендинг",
            "Chosed",
            ]
        

class Static:
    def __init__(self):
        super().__init__()

        self.THUMBSIZE: int = 200
        self.ZOOMED_THUMBSIZE: int = 240
        self.LIMIT: int = 150
        self.ALL_COLLS: str = "miuzcollections_all"
        self.RECENT_COLLS: str = "miuzcollections_recents"


class Dymanic:
    def __init__(self) -> None:
        super().__init__()

        self.current_limit: int = self.LIMIT
        self.search_text: str = None
        self.images: list = []
        self.tiff_images: set = set()
        self.date_start: datetime = None
        self.date_end: datetime = None
        self.date_start_text: str = None # datetime as readable text
        self.date_end_text: str = None # datetime as readable text
        self.lng: Union[Type[Eng], Type[Rus]] = Eng()


class AppInfo:
    def __init__(self):
        super().__init__()

        self.app_name: str = "MiuzCollections"
        self.app_ver: str = "5.0.0"


class Config(User, Dymanic, Static, AppInfo):
    def __init__(self):
        super().__init__()

        self.app_support_app_dir: str = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            f"{self.app_name}QT"
            )

        self.json_file: str = os.path.join(
            self.app_support_app_dir,
            "cfg.json"
            )

        self.db_file: str = os.path.join(
            self.app_support_app_dir,
            "db.db"
            )

    def read_json_cfg(self):
        with open(self.json_file, "r", encoding="utf8") as file:
            data: dict = json.load(file)

        if "key" not in data or data["key"]["db_ver"] != self.key["db_ver"]:
            print("New DB. Copying database")
            shutil.copyfile(src="db.db", dst=self.db_file)
            data["key"]["db_ver"] = self.key["db_ver"]

        for k, v in data.items():
            if hasattr(self, k):

                if type(v) == dict:
                    cnf_dict: dict = getattr(self, k)
                    if v.keys() != cnf_dict.keys():
                        v = cnf_dict

                setattr(self, k, v)

        self.set_language(self.user_lng)

    def write_json_cfg(self):
        data = {
            i: getattr(self, i)
            for i in list(User().__dict__)
            }

        with open(self.json_file, "w", encoding="utf8") as file:
            json.dump(obj=data, fp=file, indent=4, ensure_ascii=False)

    def set_language(self, lang_name: Literal["ru", "en"]):
        if lang_name == "ru":
            self.user_lng = "ru"
            self.lng = Rus()

        elif lang_name == "en":
            self.user_lng = "en"
            self.lng = Eng()

        else:
            raise Exception("cfg > set_language wrong lang_name arg")

    def check_app_dirs(self):
        os.makedirs(name=self.app_support_app_dir, exist_ok=True)

        if not os.path.exists(path=self.json_file):
            self.write_json_cfg()

        if not os.path.exists(path=self.db_file):
            shutil.copyfile(src="db.db", dst=self.db_file)

    def set_default(self):
        defaults = User().__dict__
        for k, v in defaults.items():
            if hasattr(self, k):
                setattr(self, k, v)


cnf = Config()
cnf.check_app_dirs()
cnf.read_json_cfg()
cnf.write_json_cfg()