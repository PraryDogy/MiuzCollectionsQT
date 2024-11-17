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

HASH_DIR: str = os.path.join(
    APP_SUPPORT_DIR,
    "hashdir"
    )
PRELOADED_HASHDIR: str = "_hashdir"

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
    lng_name: str = Eng.name_
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

    dynamic_filters = [
        {
            Eng.name_: "Product",
            Rus.name_: "Предметка",
            "real": "1 IMG",
            "value": False
        },
        {
            Eng.name_: "Model",
            Rus.name_: "Модели",
            "real": "2 MODEL IMG",
            "value": False
        },
        {
            Eng.name_: "Testing",
            Rus.name_: "Тестинг",
            "real": "TEST",
            "value": False
        }
    ]
  
    static_filter = {
        Eng.name_: "Other",
        Rus.name_: "Остальное",
        "real": "other_flag",
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
                
            filters = json_data.get("dynamic_filters")

            for k, v in json_data.items():
                if hasattr(cls, k):
                    setattr(cls, k, v)

        else:
            print("файла не существует, устанавливаю настройки по умолчанию")
            cls.write_json_data()

        if cls.coll_folder not in cls.coll_folder_list:
            print("\ncoll folder в json не из coll folder list")
            print("исправь вручную json файл")
            print("coll folder:\n", cls.coll_folder)
            print("coll folder list:\n", *[i + "\n" for i in cls.coll_folder_list], "\n")

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
        if key_ == Rus.name_:
            Dynamic.lng = Rus
            cls.lng_name = Rus.name_

        elif key_ == Eng.name_:
            Dynamic.lng = Eng
            cls.lng_name = Eng.name_

        else:
            print("cfg > set lang > неверный ключ, ставлю по умолчанию русский", key_)
            Dynamic.lng = Rus
            cls.lng_name = Rus.name_

    @classmethod
    def check_app_dirs(cls):

        os.makedirs(name=APP_SUPPORT_DIR, exist_ok=True)
        os.makedirs(HASH_DIR, exist_ok=True)

        if not os.path.exists(path="db.db"):
            print("please, download db.db.zip")
            print("extract and move to project root directory")
            webbrowser.open(LINK_DB)
            quit()

        if not os.path.exists(path=JSON_FILE):
            cls.write_json_data()

        if not os.path.exists(path=DB_FILE):
            shutil.copyfile(src="db.db", dst=DB_FILE)

    @classmethod
    def copy_hashdir(cls):
        print("копирую предустановленную HASH_DIR")

        if os.path.exists(HASH_DIR):
            shutil.rmtree(HASH_DIR)

        shutil.copytree(PRELOADED_HASHDIR, HASH_DIR)

    @classmethod
    def copy_db_file(cls):
        print("Копирую предустановленную БД")

        os.makedirs(HASH_DIR, exist_ok=True)

        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

        shutil.copyfile(src="db.db", dst=DB_FILE)


    @classmethod
    def init(cls):
        cls.check_app_dirs()
        cls.read_json_data()
        Themes.set_theme(cls.theme)
        cls.dynamic_set_lang(cls.lng_name)
        print(
            "Json data init",
            f"версии: json/внутренняя: {cls.app_ver}/{APP_VER}",
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
    lng: Eng | Rus = None
    image_viewer = None
    copy_threads: list = []
