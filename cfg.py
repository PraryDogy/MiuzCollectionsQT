import json
import os
import shutil
from datetime import datetime


class Static:
    app_ver = 4.11
    app_name = "Collections"
    thumbs_load_limit = 100

    hashdir = "hashdir"
    _preload = "_preload"
    app_support = os.path.expanduser(f"~/Library/Application Support/{app_name}")
    app_support_cfg = f"{app_support}/cfg.json"
    app_support_db = f"{app_support}/db.db"
    app_support_hashdir = f"{app_support}/{hashdir}"
    _preload_db = f"{_preload}/db.db"
    _preload_hashdir = f"{_preload}/{hashdir}"
    _preload_zip = f"{_preload}/hashdir.zip"
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
            with open(Static.app_support_cfg, "r", encoding="utf-8") as file:
                data: dict = json.load(file)
            for k, v in data.items():
                setattr(self, k, v) if hasattr(self, k) else None
        try:
            cmd()
        except Exception as e:
            print("cfg, set json data error",e)
 
    def write_json_data(self):
        with open(Static.app_support_cfg, "w", encoding="utf-8") as file:
            json.dump(vars(self), file, ensure_ascii=False, indent=4)

    def check_dirs(self):
        dirs = (Static._preload, Static._preload_zip, Static._preload_db)
        if not all(os.path.exists(p) for p in dirs):
            self.make_internal_files()
        os.makedirs(Static.app_support, exist_ok=True)
        if not os.path.exists(Static.app_support_db):
            self.copy_preload_db()
        if not os.path.exists(Static.app_support_hashdir):
            self.copy_preload_hashdir_zip()
        if not os.path.exists(Static.app_support_cfg):
            self.write_json_data()

    def make_internal_files(self):
        print("Создаю пустую базу данных")
        print("Создаю пустую hashdir")
        os.makedirs(Static._preload, exist_ok=True)
        open(Static._preload_db, "w").close()

        os.makedirs(Static._preload_hashdir, exist_ok=True)
        dummy_file = os.path.join(Static._preload_hashdir, 'dummy.keep')
        open(dummy_file, 'a').close()

        shutil.make_archive(
            base_name=os.path.join(Static._preload, Static.hashdir), 
            format="zip",
            root_dir=Static._preload,
            base_dir=Static.hashdir
        )
        shutil.rmtree(Static._preload_hashdir)

    def copy_preload_hashdir_zip(self):
        # удаляем пользовательскую hashdir из ApplicationSupport
        if os.path.exists(Static.app_support_hashdir):
            print("Удаляю пользовательскую HASH_DIR")
            shutil.rmtree(Static.app_support_hashdir)

        print("копирую предустановленную HASH_DIR")
        dest = shutil.copy2(Static._preload_zip, Static.app_support)
        shutil.unpack_archive(dest, Static.app_support)
        os.remove(dest)

    def copy_preload_db(self):
        # удаляем пользовательный db.db из Application Support если он есть
        if os.path.exists(Static.app_support_db):
            print("Удаляю пользовательский DB_FILE")
            os.remove(Static.app_support_db)

        print("Копирую предустановленный DB_FILE")
        shutil.copy2(Static._preload_db, Static.app_support)

    def initialize(self):
        self.check_dirs()
        self.set_json_data()


cfg = Cfg()