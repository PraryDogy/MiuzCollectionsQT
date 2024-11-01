import json
import os
import shutil
from datetime import datetime
from typing import Literal

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMainWindow

from lang import Eng, Rus

GRAY = "rgba(111, 111, 111, 0.5)"
BLUE = "rgba(0, 122, 255, 1)"
_IMG_EXT: tuple = (
    ".jpg", ".jpeg", ".jfif",
    ".tif", ".tiff",
    ".psd", ".psb",
    ".png",
    )
IMG_EXT: tuple = tuple(
    upper_ext
    for ext in _IMG_EXT
    for upper_ext in (ext, ext.upper())
    )
PSD_TIFF: tuple = (
    ".psd", ".psb", ".tiff", ".tif",
    ".PSD", ".PSB", ".TIFF", ".TIF"
    )

DB_SIZE = 200
PIXMAP_SIZE: list = [90, 130, 170, DB_SIZE]
THUMB_W: list = [110, 150, 170, DB_SIZE]
THUMBPAD: int = 15
TEXT_LENGTH: list = [18, 23, 28, 33]

class Thumbnail(QObject):
    def __init__(self):
        """
        reference:
        widgets > thumbnails > thumbnail.py > Thumbnail
        """
        super().__init__()

    def regular_style(self):
        ...

    def selected_style(self):
        ...


class User:
    def __init__(self) -> None:
        super().__init__()
        self.app_ver: str = "5.4.3"
    
        self.coll_folder: str = "/Volumes/Shares/Collections"
        
        self.curr_size_ind: int = 0
        self.curr_coll: str = "miuzcollections_all"
        self.cust_fltr_names: dict = {
            "prod": "1 IMG",
            "mod": "2 Model IMG"
            }
        self.cust_fltr_vals: dict = {
            "prod": False,
            "mod": False
            }    
        
        self.imgview_g: dict = {
            "aw": 700,
            "ah": 500
            }

        self.root_g: dict = {
            "aw": 700,
            "ah": 500
            }
        
        self.scaner_minutes: int = 5
        self.stop_colls: list = [
            "_Archive_Commerce_Брендинг",
            "Chosed",
            "LEVIEV"
            ]
        self.stop_words: list = [
            "копия",
            "copy",
            "1x1",
            "preview",
            "square"
            ]
        self.sys_fltr_vals: dict = {
            "other" : False
            }
        
        self.theme: str = "dark_theme"
        self.user_lng: str = "en"
        self.small_view: str = True
        self.small_menu_view: str = True

        self.down_folder: str = os.path.join(os.path.expanduser("~"), "Downloads")

        self.udpdate_file_paths = [
            '/Volumes/Shares/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
            '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
            '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
            '/Volumes/Shares-3/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
            ]

        self.coll_folder_list = [
            '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-3/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares/Collections',
            '/Volumes/Shares-1/Collections',
            '/Volumes/Shares-2/Collections',
            '/Volumes/Shares-3/Collections'
            ]

class Static:
    def __init__(self):
        super().__init__()

        self.LIMIT: int = 150
        self.ALL_COLLS: str = "miuzcollections_all"
        self.MENU_W: int = 210

class Dymanic:
    def __init__(self) -> None:
        super().__init__()

        self.current_photo_limit: int = self.LIMIT

        self.date_start: datetime = None
        self.date_end: datetime = None

        self.search_widget_text: str = None
        self.date_start_text: str = "1 january 1991" # datetime as readable text
        self.date_end_text: str = "31 december 1991" # datetime as readable text

        self.lng: Eng = Eng()

        self.image_viewer: QMainWindow = None
        self.selected_thumbnail: Thumbnail = Thumbnail()

        self.copy_threads: list = []

class AppInfo:
    def __init__(self):
        super().__init__()
        self.app_name: str = "MiuzCollections"


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
        
    def update_json(self, data: dict):        
        data["scaner_minutes"] = 5

        if "LEVIEV" not in data["stop_colls"]:
            data["stop_colls"].append("LEVIEV")

        data["coll_folder_list"] = self.coll_folder_list
        data["udpdate_file_paths"] = self.udpdate_file_paths

        data["app_ver"] = self.app_ver

        return data

    def read_json_cfg(self):
        with open(self.json_file, "r", encoding="utf8") as file:
            data: dict = json.load(file)

        if "app_ver" not in data or self.app_ver != data["app_ver"]:
            data = self.update_json(data)
        
        for k, v in data.items():
            if hasattr(self, k):

                if type(v) == dict:
                    cnf_dict: dict = getattr(self, k)
                    if v.keys() != cnf_dict.keys():
                        v = cnf_dict

                setattr(self, k, v)

        self.set_language(self.user_lng)

        if self.coll_folder not in self.coll_folder_list:
            print("\ncoll folder в json не из coll folder list")
            print("исправь вручную json файл")
            print("coll folder:\n", self.coll_folder)
            print("coll folder list:\n", *[i + "\n" for i in self.coll_folder_list], "\n")

    def write_json_cfg(self):
        data = {
            i: getattr(self, i)
            for i in list(User().__dict__)
            }

        data = dict(sorted(data.items()))

        try:
            with open(self.json_file, "w", encoding="utf8") as file:
                json.dump(obj=data, fp=file, indent=4, ensure_ascii=False)
        except FileNotFoundError:
            self.check_app_dirs()
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

        if not os.path.exists(path="db.db"):
            print("please, download db.db.zip from")
            print("https://disk.yandex.ru/d/FmwEPA8nS3JsMw")
            print("extract and move to project root directory")
            quit()

        if not os.path.exists(path=self.json_file):
            self.write_json_cfg()

        if not os.path.exists(path=self.db_file):
            shutil.copyfile(src="db.db", dst=self.db_file)

cnf = Config()
cnf.check_app_dirs()
cnf.read_json_cfg()
cnf.write_json_cfg()