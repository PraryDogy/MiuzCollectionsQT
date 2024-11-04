import json
import os
import shutil
from datetime import datetime

from lang import Eng, Rus
from styles import Themes

APP_NAME: str = "MiuzCollections"
APP_VER = "5.8.5"

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
ALL_COLLS: str = "miuzcollections_all"
MENU_W: int = 210

GRAY = "rgba(111, 111, 111, 0.5)"
BLUE = "rgba(0, 122, 255, 1)"


class JsonData:
    app_ver: str = APP_VER

    coll_folder: str = "/Volumes/Shares/Collections"
    
    curr_size_ind: int = 0
    curr_coll: str = ALL_COLLS

    cust_fltr_names: dict = {
        "prod": "1 IMG",
        "mod": "2 Model IMG"
        }

    cust_fltr_vals: dict = {
        "prod": False,
        "mod": False
        }    
    
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

    stop_words: list = [
        "копия",
        "copy",
        "1x1",
        "preview",
        "square"
        ]

    sys_fltr_vals: dict = {
        "other" : False
        }
    
    theme: str = "dark_theme"
    user_lng: str = "en"
    small_menu_view: str = True

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

                    for k, v in json_data.items():
                        if hasattr(cls, k):
                            setattr(cls, k, v)

                except json.JSONDecodeError:
                    print("Ошибка чтения json")
                    cls.write_json_data()

        else:
            print("файла не существует, устанавливаю настройки по умолчанию")
            cls.write_json_data()

        if cls.coll_folder not in cls.coll_folder_list:
            print("\ncoll folder в json не из coll folder list")
            print("исправь вручную json файл")
            print("coll folder:\n", cls.coll_folder)
            print("coll folder list:\n", *[i + "\n" for i in cls.coll_folder_list], "\n")

        if cls.app_ver != APP_VER:
            print("Версии приложения не совпадают: json / внутренняя:", cls.app_ver, os.sep, APP_VER)

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
        """ru, en"""

        data: dict[str, Rus | Eng] = {"ru": Rus, "en": Eng}

        if key_ in data:
            Dynamic.lng = data.get(key_)()
            cls.user_lng = key_

        else:
            raise KeyError("cfg > dymamic set lang > no key (ru, en)", key_)

    @classmethod
    def check_app_dirs(cls):

        os.makedirs(name=APP_SUPPORT_DIR, exist_ok=True)

        if not os.path.exists(path="db.db"):
            print("please, download db.db.zip from")
            print("https://disk.yandex.ru/d/FmwEPA8nS3JsMw")
            print("extract and move to project root directory")
            quit()

        if not os.path.exists(path=JSON_FILE):
            cls.write_json_data()

        if not os.path.exists(path=DB_FILE):
            shutil.copyfile(src="db.db", dst=DB_FILE)

    @classmethod
    def init(cls):
        cls.check_app_dirs()
        cls.read_json_data()
        Themes.set_theme(cls.theme)
        cls.dynamic_set_lang(cls.user_lng)


class Dynamic:
    current_photo_limit: int = LIMIT
    date_start: datetime = None
    date_end: datetime = None
    search_widget_text: str = None
    date_start_text: str = None # 1 january 1991
    date_end_text: str = None # 31 january 1991
    lng: Eng | Rus = None
    image_viewer = None
    copy_threads: list = []
