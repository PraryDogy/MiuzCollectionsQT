import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class Static:
    app_ver = 4.25
    app_name = "Collections"
    thumbs_load_limit = 100
    
    external_files_dir = os.path.expanduser(
        f"~/Library/Application Support/{app_name}"
    )
    external_cfg = f"{external_files_dir}/cfg.json"
    external_db = f"{external_files_dir}/db.db"
    external_hashdir = f"{external_files_dir}/hashdir"
    external_mf = f"{external_files_dir}/mf.json"
    external_filters = f"{external_files_dir}/filters.json"
    external_servers = f"{external_files_dir}/servers.json"

    internal_files_dir = "./_preload"

    ww, hh = 1120, 760
    max_img_size = 210
    spacing = 2
    margins = 15
    thumb_heights = [130, 150, 185, 270]
    thumb_widths = [145, 145, 180, 230]
    pixmap_sizes = [50, 70, 100, 170]
    row_limits = [20, 20, 25, 32]
    corner_values = [4, 8, 14, 16]


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    f_date_start: str = None # 1 january 1991
    f_date_end: str = None # 31 january 1991
    loaded_thumbs: int = 0
    search_widget_text: str = None
    thumb_size_index: int = 2
    current_dir: str = ""
    sort_by_mod: bool = True
    filters_enabled: list[str] = []
    filter_favs: bool = False
    filter_only_folder: bool = False
    history: list[str] = []


class Cfg:
    app_ver: str = Static.app_ver
    lng: int = 0
    dark_mode: int = 0
    scaner_minutes: int = 5
    new_scaner: int = True
    hide_digits: bool = True
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

    @classmethod
    def get_data(cls):
        return {
            k: v
            for k, v in vars(Cfg).items()
            if not k.startswith("__")
            and
            not callable(getattr(Cfg, k))
        }
    
    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.external_cfg, "r", encoding="utf-8") as file:
                data: dict = json.load(file)
            for k, v in data.items():
                setattr(cls, k, v) if hasattr(cls, k) else None
        except Exception as e:
            print("cfg, set json data error",e)
    
    @classmethod
    def write_json_data(cls):
        with open(Static.external_cfg, "w", encoding="utf-8") as file:
            json.dump(cls.get_data(), file, ensure_ascii=False, indent=4)

    @classmethod
    def check_files(cls):
        dirs = (
            Static.external_files_dir,
            Static.external_cfg,
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
    def get_file_dirs(cls):
        return {
            Static.internal_cfg: Static.external_cfg,
            Static.internal_db: Static.external_db,
            Static.internal_mf: Static.external_mf,
            Static.internal_filters: Static.external_filters,
            Static.internal_servers: Static.external_servers,
        }

    @classmethod
    def remake_external_dir(cls):
        if os.path.exists(Static.external_files_dir):
            shutil.rmtree(Static.external_files_dir)
        os.makedirs(Static.external_files_dir, exist_ok=True)

    @classmethod
    def copy_miuz_files(cls):
        zip_file = os.listdir(Static.internal_files_dir)[0]
        zip_file = Path(Static.internal_files_dir) / zip_file
        dst  = shutil.copy2(zip_file, Static.external_files_dir)
        shutil.unpack_archive(dst, Static.external_files_dir)
        os.remove(dst)

    @classmethod
    def make_external_empty_files(cls):
        os.makedirs(Static.external_hashdir, exist_ok=True)
        for src, dst in cls.get_file_dirs().items():
            with open(dst, "w") as file:
                ...
