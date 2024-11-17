import json
import os
import shutil
import webbrowser
from datetime import datetime

from lang.eng import Eng
from lang.rus import Rus
from styles import Themes

LINK_DB = "https://disk.yandex.ru/d/gDnB5X9kGqjztA"
APP_NAME: str = "MiuzCollections"
APP_VER = 5.85

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

PRELOADED_DB = "db.db"

HASH_DIR: str = os.path.join(
    APP_SUPPORT_DIR,
    "hashdir"
    )

PRELOADED_HASHDIR: str = "hashdir"

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

PIXMAP_SIZE_MAX = 200
PIXMAP_SIZE: list = [90, 130, 170, PIXMAP_SIZE_MAX]
THUMB_W: list = [110, 140, 170, PIXMAP_SIZE_MAX]
THUMB_MARGIN: int = 15
TEXT_LENGTH: list = [17, 20, 25, 29]

LIMIT: int = 150
MENU_W: int = 210

ALL_COLLS: str = "miuzcollections_all"
FAVS: str = "miuzcollections_fav"

GRAY = "rgba(111, 111, 111, 0.5)"
BLUE = "rgba(0, 122, 255, 1)"
STAR_SYM = "\U00002605" + " "

STATIC_FILTER_REAL_NAME = "other_flag"


class JsonData:
    app_ver: str = APP_VER

    coll_folder: str = "/Volumes/Shares/Collections"
    
    curr_size_ind: int = 0
    curr_coll: str = ALL_COLLS
    
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
    
    theme: str = "dark_theme"
    lang_name: str = Rus.lang_name

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

    dynamic_filters = [
        {
            Eng.lang_name: "Product",
            Rus.lang_name: "Продукт",
            "real": "1 IMG",
            "value": False
        },
        {
            Eng.lang_name: "Model",
            Rus.lang_name: "Модели",
            "real": "2 MODEL IMG",
            "value": False
        }
    ]
  
    static_filter = {
        Eng.lang_name: "Other",
        Rus.lang_name: "Остальное",
        "real": STATIC_FILTER_REAL_NAME,
        "value": False
        }

    @classmethod
    def get_data(cls):
        return [
            i for i in dir(cls)
            if not i.startswith("__")
            and
            not callable(getattr(cls, i))
            ]

    @classmethod
    def read_json_data(cls) -> dict:

        if os.path.exists(JSON_FILE):

            with open(JSON_FILE, 'r', encoding="utf-8") as f:
                try:
                    json_data: dict = json.load(f)

                except json.JSONDecodeError:
                    print("Ошибка чтения json")
                    cls.write_json_data()
                    cls.read_json_data()
                    return
                
            for k, v in json_data.items():
                if hasattr(cls, k):
                    setattr(cls, k, v)

        else:
            print("JSON файла не существует, создаю файл по умолчанию")
            cls.write_json_data()

    @classmethod
    def write_json_data(cls):

        new_data: dict = {
            attr: getattr(cls, attr)
            for attr in cls.get_data()
            }

        with open(JSON_FILE, 'w', encoding="utf-8") as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)

    @classmethod
    def dynamic_set_lang(cls, key_: str):
        if key_ == Rus.lang_name:
            Dynamic.lang = Rus
            cls.lang_name = Rus.lang_name

        elif key_ == Eng.lang_name:
            Dynamic.lang = Eng
            cls.lang_name = Eng.lang_name

        else:
            print("cfg > set lang > неверный ключ, ставлю по умолчанию русский", key_)
            Dynamic.lang = Rus
            cls.lang_name = Rus.lang_name

    @classmethod
    def check_app_dirs(cls):

        if not os.path.exists(APP_SUPPORT_DIR):

            os.makedirs(name=APP_SUPPORT_DIR, exist_ok=True)
            cls.copy_indeed_files()
            cls.write_json_data()

    @classmethod
    def copy_hashdir(cls):
        if os.path.exists(HASH_DIR):
            print("Удаляю пользовательскую HASH_DIR")
            shutil.rmtree(HASH_DIR)

        if os.path.exists(PRELOADED_HASHDIR):
            print("копирую предустановленную HASH_DIR")
            shutil.copytree(PRELOADED_HASHDIR, HASH_DIR)

        else:
            t = "нет предустановленной HASH_DIR"
            raise Exception(t)

    @classmethod
    def copy_db_file(cls):

        if os.path.exists(DB_FILE):
            print("Удаляю пользовательский DB_FILE")
            os.remove(DB_FILE)

        if os.path.exists(PRELOADED_DB):
            print("Копирую предустановленный DB_FILE")
            shutil.copyfile(src="db.db", dst=DB_FILE)

        else:
            t = "Нет предуставновленного DB_FILE"
            raise Exception(t)

    @classmethod
    def compare_versions(cls):
        try:
            float(cls.app_ver)
        except Exception:
            cls.app_ver = 1.0

        if APP_VER > float(cls.app_ver):
            cls.copy_indeed_files()

    @classmethod
    def copy_indeed_files(cls):
        print("версия приложения выше чем пользовательская")
        cls.copy_db_file()
        cls.copy_hashdir()
        cls.app_ver = APP_VER
        cls.write_json_data()

    @classmethod
    def init(cls):
        cls.check_app_dirs()
        cls.read_json_data()
        cls.compare_versions()

        cls.dynamic_set_lang(cls.lang_name)
        Themes.set_theme(cls.theme)

        print(
            "Json data init",
            "check app dirs ok",
            "read json ok",
            "set theme ok",
            "set lang ok",
            sep=", "
            )


class Dynamic:
    current_photo_limit: int = LIMIT
    date_start: datetime = None
    date_end: datetime = None
    search_widget_text: str = None
    date_start_text: str = None # 1 january 1991
    date_end_text: str = None # 31 january 1991
    lang: Eng | Rus = None
    image_viewer = None
    copy_threads: list = []
