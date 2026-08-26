import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class Themes:
    auto = "auto"
    dark = "dark"
    light = "light"


class Static:
    APP_VERSION = 5.7
    APP_NAME = "Collections"
    THUMBS_LOAD_LIMIT = 100
    
    # 1. Базовая папка приложения (сразу делаем объектом Path)
    APP_DATA_DIR = Path(os.path.expanduser("~")) / "Library" / "Application Support" / APP_NAME

    # 2. Файлы и папки внутри APP_DATA_DIR (используем оператор /)
    CFG_JSON = APP_DATA_DIR / "cfg.json"
    DB_FILE = APP_DATA_DIR / "db.db"
    HASHDIR = APP_DATA_DIR / "hashdir"
    MF_JSON = APP_DATA_DIR / "mf.json"
    FILTERS_JSON = APP_DATA_DIR / "filters.json"
    SERVERS_JSON = APP_DATA_DIR / "servers.json"

    # 3. Ресурсы самого приложения (относительные пути)
    SCRIPTS = Path("./scripts")
    SCRIPTS_REVEAL_FILES = SCRIPTS / "reveal_files.scpt"

    ICONS = Path("./icons")
    MIUZ_ZIP = Path("./_miuz.zip")

    THEMES = Path("./themes")
    THEMES_DARK = THEMES / "dark.qss"
    THEMES_LIGHT = THEMES / "light.qss"

    # Подпапки для иконок (красиво собираются от базовой папки icons)
    APP_ICONS = ICONS / "app_icons"
    BAR_TOP_ICONS = ICONS / "bar_top"
    COMMON_ICONS = ICONS / "common"
    JPEG_ICONS = ICONS / "jpeg_icons"


    # максимально возможный размер миниатюры в HASHDIR
    THUMB_MAX_SIZE = 210
    # размеры для QPixmap в виджете Thumb
    THUMB_WID_PIXMAP_SIZE = [65, 80, 135]
    # рамка вокруг QPixmap в виджете Thumb
    THUMB_IMG_WID_BORDER = 15
    # дополнительное пространство к ширине виджета Thumb
    THUMB_WID_EXTRA_W = 40

    IMAGE_APPS = [
        "preview",
        "photos",
        "photoshop",
        "lightroom",
        "affinity photo",
        "pixelmator",
        "gimp",
        "capture one",
        "dxo photolab",
        "luminar neo",
        "sketch",
        "graphicconverter",
        "imageoptim",
        "snapheal",
        "photoscape",
        "preview",
        "просмотр"
    ]
    DEFAULT_FILTERS = [
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".tif",
        ".psd",
        ".psb"
    ]


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    date_index: int = 0
    loaded_thumbs: int = 0
    search_widget_text: str = None
    current_pixmap_size_index: int = 1
    current_dir: str = os.sep
    sort_by_mod: bool = True
    filters_enabled: list[str] = []
    filter_favs: bool = False
    filter_only_folder: bool = False
    history: list[str] = []
    thumb_path_set: set[str] = set()


class JsonData:
    app_ver = Static.APP_VERSION
    lng_index = 0
    theme = Themes.dark
    scaner_minutes = 20
    hide_digits_mf_lst = []

    @classmethod
    def get_data(cls):
        return {
            "app_ver": cls.app_ver,
            "lng_index": cls.lng_index,
            "theme": cls.theme,
            "scaner_minutes": cls.scaner_minutes,
            "hide_digits_mf_lst": cls.hide_digits_mf_lst,   
        }
    
    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.CFG_JSON, "r", encoding="utf-8") as file:
                data: dict = json.load(file)
            for k, v in data.items():
                setattr(cls, k, v) if hasattr(cls, k) else None
            if JsonData.theme not in (Themes.dark, Themes.light):
                JsonData.theme = Themes.dark
        except Exception as e:
            print("Cfg json to app error",e)
    
    @classmethod
    def write_json_data(cls):
        with open(Static.CFG_JSON, "w", encoding="utf-8") as file:
            json.dump(cls.get_data(), file, ensure_ascii=False, indent=4)
