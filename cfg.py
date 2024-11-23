import json
import os
import shutil
import webbrowser
from datetime import datetime

APP_VER = 5.85
APP_NAME: str = "MiuzCollections"

BRANDS = ["miuz", "panacea"]
GRID_LIMIT: int = 150
LINK_DB = "https://disk.yandex.ru/d/TVofkvNe9pLt8g"
MENU_LEFT_WIDTH: int = 210
NAME_ALL_COLLS: str = "miuzcollections_all"
NAME_FAVS: str = "miuzcollections_fav"
RGBA_BLUE = "rgba(0, 122, 255, 1)"
RGBA_GRAY = "rgba(111, 111, 111, 0.5)"
STAR_SYM = "\U00002605" + " "

PIXMAP_SIZE_MAX = 200
THUMB_MARGIN: int = 15
PIXMAP_SIZE: list = [90, 130, 170, PIXMAP_SIZE_MAX]
THUMB_W: list = [110, 140, 170, PIXMAP_SIZE_MAX]
TEXT_LENGTH: list = [17, 20, 25, 29]

APP_SUPPORT_DIR: str = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    APP_NAME + "QT"
    )

JSON_FILE: str = os.path.join(
    APP_SUPPORT_DIR,
    "cfg.json"
    )

DB_FILE: str = os.path.join(
    APP_SUPPORT_DIR,
    "db.db"
    )

HASH_DIR: str = os.path.join(
    APP_SUPPORT_DIR,
    "hashdir"
    )

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


PRELOAD_FOLDER: str = "_preload"

PRELOAD_DB: str = os.path.join(
    PRELOAD_FOLDER,
    "db.db"
    )

PRELOAD_HASHDIR_ZIP: str = os.path.join(
    PRELOAD_FOLDER,
    "hashdir.zip"
    )

PSD_TIFF: tuple = (
    ".psd", ".psb", ".tiff", ".tif",
    ".PSD", ".PSB", ".TIFF", ".TIF"
    )

STYLES_CSS = "styles.css"

NORMAL_STYLE = """
    border: 2px solid transparent;
"""

SOLID_STYLE = """
    border-radius: 6px;
    border: 2px solid transparent;
    background-color: rgb(46, 89, 203);
    color: rgb(255, 255, 255);
"""

BORDER_STYLE = """
    border-radius: 6px;
    border: 2px solid rgb(46, 89, 203);
"""


class Filter:
    filters: list["Filter"] = []
    __slots__ = ["names", "real", "value", "system"]

    def __init__(self, names: list, real: str, value: bool, system: bool):
        self.names = names
        self.real = real
        self.value = value
        self.system = system

    def get_data(self):
        return {
            "names": self.names,
            "real": self.real,
            "value": self.value,
            "system": self.system
        }


class JsonData:
    app_ver: str = APP_VER

    brand_ind = 0
    
    curr_size_ind: int = 0
    curr_coll: str = NAME_ALL_COLLS
    
    imgview_g: dict = {
        "aw": 700,
        "ah": 500
        }

    root_g: dict = {
        "aw": 700,
        "ah": 500
        }
    
    scaner_minutes: int = 5

    stop_colls: list = [
        "_Archive_Commerce_Брендинг",
        "Chosed",
        "LEVIEV"
        ]
    
    lang_ind = 0

    down_folder: str = os.path.join(os.path.expanduser("~"), "Downloads")

    udpdate_file_paths = [
        '/Volumes/Shares/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        '/Volumes/Shares-3/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        ]

    coll_folder_list = [
        '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-3/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares/Collections',
        '/Volumes/Shares-1/Collections',
        '/Volumes/Shares-2/Collections',
        '/Volumes/Shares-3/Collections'
        ]

    coll_folder: str = coll_folder_list[0]

    filters = [
        {
            "names": ("Продукт", "Product"),
            "real": "1 IMG", 
            "value": False,
            "system": False
        },
        {
            "names": ("Модели", "Model"),
            "real": "2 MODEL IMG", 
            "value": False,
            "system": False
        },
        {
            "names": ("Остальное", "Other"),
            "real": None, 
            "value": False,
            "system": True
        },
    ]

    @classmethod
    def _get_data(cls):
        """returns user attibutes and values"""
        return {
            k: v
            for k, v in vars(cls).items()
            if not k.startswith("__")
            and
            not callable(getattr(cls, k))
        }

    @classmethod
    def _read_json_data(cls) -> dict:

        if os.path.exists(JSON_FILE):

            with open(JSON_FILE, 'r', encoding="utf-8") as f:
                try:
                    json_data: dict = json.load(f)

                except json.JSONDecodeError:
                    print("Ошибка чтения json")
                    json_data: dict = cls._get_data()
                
            for k, v in json_data.items():
                if hasattr(cls, k):
                    setattr(cls, k, v)

    @classmethod
    def write_json_data(cls):
        cls.filters = cls._get_filters()

        with open(JSON_FILE, 'w', encoding="utf-8") as f:
            json.dump(
                obj=cls._get_data(),
                fp=f,
                indent=4,
                ensure_ascii=False
            )

    @classmethod
    def _init_filters(cls):
        for i in cls.filters:
            Filter.filters.append(
                Filter(**i)
            )

    @classmethod
    def _get_filters(cls):
        return [
            i.get_data()
            for i in Filter.filters
        ]

    @classmethod
    def _check_app_dirs(cls):
        if not os.path.exists(APP_SUPPORT_DIR):
            os.makedirs(name=APP_SUPPORT_DIR, exist_ok=True)

        if not os.path.exists(DB_FILE):
            cls.copy_db_file()

        if not os.path.exists(HASH_DIR):
            cls.copy_hashdir()

        if not os.path.exists(JSON_FILE):
            cls.write_json_data()

    @classmethod
    def copy_hashdir(cls):
        if os.path.exists(HASH_DIR):
            print("Удаляю пользовательскую HASH_DIR")
            shutil.rmtree(HASH_DIR)

        if os.path.exists(PRELOAD_HASHDIR_ZIP):
            print("копирую предустановленную HASH_DIR")
            dest = shutil.copy2(PRELOAD_HASHDIR_ZIP, APP_SUPPORT_DIR)
            shutil.unpack_archive(dest, APP_SUPPORT_DIR)
            os.remove(dest)

        else:
            t = "нет предустановленной HASH_DIR: " + PRELOAD_HASHDIR_ZIP
            webbrowser.open(LINK_DB)
            raise Exception(t)

    @classmethod
    def copy_db_file(cls):
        if os.path.exists(DB_FILE):
            print("Удаляю пользовательский DB_FILE")
            os.remove(DB_FILE)

        if os.path.exists(PRELOAD_DB):
            print("Копирую предустановленный DB_FILE")
            shutil.copyfile(src=PRELOAD_DB, dst=DB_FILE)

        else:
            t = "Нет предуставновленного DB_FILE: " + DB_FILE
            webbrowser.open(LINK_DB)
            raise Exception(t)

    @classmethod
    def _compare_versions(cls):
        try:
            json_app_ver = float(cls.app_ver)
        except Exception:
            json_app_ver = APP_VER

        if APP_VER > json_app_ver:
            print("Пользовательская версия приложения ниже необходимой")
            cls.copy_db_file()
            cls.copy_hashdir()
            cls.app_ver = APP_VER
            cls.write_json_data()

    @classmethod
    def init(cls):
        cls._check_app_dirs()
        cls._read_json_data()
        cls._compare_versions()
        cls._init_filters()


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    date_start_text: str = None # 1 january 1991
    date_end_text: str = None # 31 january 1991
    grid_offset: int = 0
    search_widget_text: str = None