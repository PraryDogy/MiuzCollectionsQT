import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class Themes:
    macos = "macos"
    dark = "dark"
    light = "light"


class Static:
    app_ver = 5.4
    app_name = "Collections"
    thumbs_load_limit = 100
    
    external_dir = os.path.expanduser(
        os.path.join("~", "Library", "Application Support", app_name)
    )

    external_json_data = os.path.join(external_dir, "cfg.json")
    external_db = os.path.join(external_dir, "db.db")
    external_hashdir = os.path.join(external_dir, "hashdir")
    external_mf = os.path.join(external_dir, "mf.json")
    external_filters = os.path.join(external_dir, "filters.json")
    external_servers = os.path.join(external_dir, "servers.json")

    internal_files = "./_preload"
    internal_icons = "./images"

    max_thumb_size = 210
    pixmap_sizes = [50, 70, 100, 170]

    apps = [
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


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    loaded_thumbs: int = 0
    search_widget_text: str = None
    thumb_size_index: int = 2
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
    theme = Themes.macos
    scaner_minutes = 20
    hide_digits_mf_lst = []

    @classmethod
    def get_data(cls):
        return {
            k: v
            for k, v in vars(JsonData).items()
            if not k.startswith("__")
            and
            not callable(getattr(JsonData, k))
        }
    
    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.external_json_data, "r", encoding="utf-8") as file:
                data: dict = json.load(file)
            for k, v in data.items():
                setattr(cls, k, v) if hasattr(cls, k) else None
            if JsonData.theme not in (Themes.macos, Themes.dark, Themes.light):
                JsonData.theme = Themes.macos
        except Exception as e:
            print("Cfg json to app error",e)
    
    @classmethod
    def write_json_data(cls):
        with open(Static.external_json_data, "w", encoding="utf-8") as file:
            json.dump(cls.get_data(), file, ensure_ascii=False, indent=4)

    @classmethod
    def check_files(cls):
        """
        Проверяет наличие файлов
        """
        dirs = (
            Static.external_dir,
            Static.external_json_data,
            Static.external_db,
            Static.external_filters,
            Static.external_hashdir,
            Static.external_mf,
            Static.external_servers
        )
        for i in dirs:
            if not os.path.exists(i):
                return None
        return True
    
    @classmethod
    def remake_external_dir(cls):
        if os.path.exists(Static.external_dir):
            shutil.rmtree(Static.external_dir)
        os.makedirs(Static.external_dir, exist_ok=True)

    @classmethod
    def copy_preloaded_zip(cls):
        zip_file = os.listdir(Static.internal_files)[0]
        zip_file = Path(Static.internal_files) / zip_file
        dst  = shutil.copy2(zip_file, Static.external_dir)
        shutil.unpack_archive(dst, Static.external_dir)
        os.remove(dst)

    @classmethod
    def make_empty_external_files(cls):
        os.makedirs(Static.external_hashdir, exist_ok=True)
        files = (
            Static.external_json_data,
            Static.external_db,
            Static.external_filters,
            Static.external_mf,
            Static.external_servers
        )
        for i in files:
            with open(i, "w") as file:
                ...
