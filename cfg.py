import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class Themes:
    dark = "dark"
    light = "light"


class Static:
    app_ver = 5.7
    app_name = "Collections"
    thumbs_load_limit = 100
    
    # 1. Базовая папка данных приложения
    APP_DATA_DIR = Path(os.path.expanduser("~")) / "Library" / "Application Support" / app_name

    # 2. Файлы и папки внутри APP_DATA_DIR
    CFG_JSON = APP_DATA_DIR / "cfg.json"
    DB_DB = APP_DATA_DIR / "db.db"
    HASHDIR = APP_DATA_DIR / "hashdir"
    MF_JSON = APP_DATA_DIR / "mf.json"
    FILTERS_JSON = APP_DATA_DIR / "filters.json"
    SERVERS_JSON = APP_DATA_DIR / "servers.json"

    # 3. Локальные ресурсы приложения
    SCRIPTS = Path("./scripts")
    ICONS = Path("./icons")
    MIUZ_ZIP = Path("./_miuz.zip")
    
    # 4. Подпапки с иконками (собираются от базовой папки ICONS)
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
    app_ver = Static.app_ver
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
            with open(Static.cfg_json, "r", encoding="utf-8") as file:
                data: dict = json.load(file)
            for k, v in data.items():
                setattr(cls, k, v) if hasattr(cls, k) else None
            if JsonData.theme not in (Themes.dark, Themes.light):
                JsonData.theme = Themes.dark
        except Exception as e:
            print("Cfg json to app error",e)
    
    @classmethod
    def write_json_data(cls):
        with open(Static.cfg_json, "w", encoding="utf-8") as file:
            json.dump(cls.get_data(), file, ensure_ascii=False, indent=4)
