import json
import os
import shutil
from datetime import datetime


class ThumbData:

    # размер в пикселях по длинной стороне изображения для базы данных
    DB_IMAGE_SIZE = 210
    # ширина и высота grid.py > Thumb
    THUMB_H = [130, 150, 185, 270]
    THUMB_W = [145, 145, 180, 230]
    # максимальный размер изображения в пикселях для grid.py > Thumb
    PIXMAP_SIZE = [50, 70, 100, 170]
    # максимальное количество символов на строку для grid.py > Thumb
    MAX_ROW = [20, 20, 25, 32]
    CORNER = [4, 8, 14, 16]
    # растояние между изображением и текстом для grid.py > Thumb
    SPACING = 2
    # дополнительное пространство вокруг изображения для grid.py > Thumb
    MARGIN = 15

class Static:
    app_ver = 3.75
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

    img_extensions = (
        ".jpg", ".JPG", ".jpeg", ".JPEG", ".jpe", ".JPE", ".jfif", ".JFIF",
        ".bmp", ".BMP", ".dib", ".DIB", ".webp", ".WEBP", ".ppm", ".PPM",
        ".pgm", ".PGM", ".pbm", ".PBM", ".pnm", ".PNM", ".gif", ".GIF",
        ".ico", ".ICO",
        ".tif", ".TIF", ".tiff", ".TIFF",
        ".psd", ".PSD", ".psb", ".PSB",
        ".png", ".PNG",
        ".nef", ".NEF", ".cr2", ".CR2", ".cr3", ".CR3", ".arw", ".ARW",
        ".raf", ".RAF", ".dng", ".DNG", ".rw2", ".RW2", ".orf", ".ORF",
        ".srw", ".SRW", ".pef", ".PEF", ".rwl", ".RWL", ".mos", ".MOS",
        ".kdc", ".KDC", ".mrw", ".MRW", ".x3f", ".X3F",
        ".avi", ".AVI", ".mp4", ".MP4", ".mov", ".MOV", ".mkv", ".MKV",
        ".wmv", ".WMV", ".flv", ".FLV", ".webm", ".WEBM",
    )


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
    def set_json_data(cls):
        with open(Static.app_support_cfg, "r", encoding="utf-8") as file:
            try:
                data: dict = json.load(file)
                for k, v in data.items():
                    if hasattr(cls, k):
                        setattr(cls, k, v)
            except Exception as e:
                print("cfg, set json data error",e)
                data = {}

    @classmethod
    def get_data(cls, start: int = 2, end: int = 9):
        return {
            i: getattr(Cfg, i)
            for i in list(vars(Cfg))[start:end]
        }
 
    @classmethod
    def write_json_data(cls):
        with open(Static.app_support_cfg, "w", encoding="utf-8") as file:
            json.dump(cls.get_data(), file, ensure_ascii=False, indent=4)

    @classmethod
    def check_dirs(cls):
        dirs = (Static._preload, Static._preload_zip, Static._preload_db)
        if not all(os.path.exists(p) for p in dirs):
            cls.make_internal_files()
        os.makedirs(Static.app_support, exist_ok=True)
        if not os.path.exists(Static.app_support_db):
            cls.copy_preload_db()
        if not os.path.exists(Static.app_support_hashdir):
            cls.copy_preload_hashdir_zip()
        if not os.path.exists(Static.app_support_cfg):
            cls.write_json_data()

    @classmethod
    def make_internal_files(cls):
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

    @classmethod
    def copy_preload_hashdir_zip(cls):
        # удаляем пользовательскую hashdir из ApplicationSupport
        if os.path.exists(Static.app_support_hashdir):
            print("Удаляю пользовательскую HASH_DIR")
            shutil.rmtree(Static.app_support_hashdir)

        print("копирую предустановленную HASH_DIR")
        dest = shutil.copy2(Static._preload_zip, Static.app_support)
        shutil.unpack_archive(dest, Static.app_support)
        os.remove(dest)

    @classmethod
    def copy_preload_db(cls):
        # удаляем пользовательный db.db из Application Support если он есть
        if os.path.exists(Static.app_support_db):
            print("Удаляю пользовательский DB_FILE")
            os.remove(Static.app_support_db)

        print("Копирую предустановленный DB_FILE")
        shutil.copy2(Static._preload_db, Static.app_support)

    @classmethod
    def init(cls):
        cls.check_dirs()
        cls.set_json_data()


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    f_date_start: str = None # 1 january 1991
    f_date_end: str = None # 31 january 1991
    loaded_thumbs: int = 0
    search_widget_text: str = None

    # индекс соответствующий STATIC > IMG_LABEL_SIZE
    # от индекса зависит размер Thumbnail и всех его внутренних виджетов
    thumb_size_index: int = 0
    current_dir: str = ""
    sort_by_mod: bool = True
    filters_enabled: list[str] = []
    filter_favs: bool = False
    filter_only_folder: bool = False