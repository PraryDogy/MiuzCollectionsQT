import json
import os
import shutil
from datetime import datetime


class Static:
    app_ver = 4.25
    app_name = "Collections"
    thumbs_load_limit = 100
    
    external_files_dir = os.path.expanduser(f"~/Library/Application Support/{app_name}")
    external_cfg = f"{external_files_dir}/cfg.json"
    external_db = f"{external_files_dir}/db.db"
    external_hashdir = f"{external_files_dir}/hashdir"
    external_mf = f"{external_files_dir}/mf.json"
    external_filters = f"{external_files_dir}/filters.json"
    external_servers = f"{external_files_dir}/servers.json"

    internal_files_dir = "./_preload"
    internal_cfg = f"{internal_files_dir}/cfg.json"
    internal_db = f"{internal_files_dir}/db.db"
    internal_hashdir_zip = f"{internal_files_dir}/hashdir.zip"
    internal_mf = f"{internal_files_dir}/mf.json"
    internal_filters = f"{internal_files_dir}/filters.json"
    internal_servers = f"{internal_files_dir}/servers.json"

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
    def __init__(self):
        self.app_ver: str = Static.app_ver
        self.lng: int = 0
        self.dark_mode: int = 0
        self.scaner_minutes: int = 5
        self.new_scaner: int = True
        self.hide_digits: bool = True
        self.apps = [
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

    def set_json_data(self):
        def cmd():
            with open(Static.external_cfg, "r", encoding="utf-8") as file:
                data: dict = json.load(file)
            for k, v in data.items():
                setattr(self, k, v) if hasattr(self, k) else None
        try:
            cmd()
        except Exception as e:
            print("cfg, set json data error",e)
 
    def write_json_data(self):
        with open(Static.external_cfg, "w", encoding="utf-8") as file:
            json.dump(vars(self), file, ensure_ascii=False, indent=4)

    def check_files(self):
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
    
    def copy_files(self):
        if os.path.exists(Static.external_files_dir):
            shutil.rmtree(Static.external_files_dir)
        os.makedirs(Static.external_files_dir, exist_ok=True)

        dirs = {
            Static.internal_cfg: Static.external_cfg,
            Static.internal_db: Static.external_db,
            Static.internal_mf: Static.external_mf,
            Static.internal_filters: Static.external_filters,
            Static.internal_servers: Static.external_servers,
        }
        for src, external_zip in dirs:
            shutil.copy2(src, Static.external_files_dir)

        external_zip = shutil.copy2(
            Static.internal_hashdir_zip,
            Static.external_files_dir
        )
        shutil.unpack_archive(external_zip, Static.external_files_dir)
        os.remove(external_zip)


cfg = Cfg()