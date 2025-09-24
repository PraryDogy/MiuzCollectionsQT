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
    APP_VER = 3.50
    APP_NAME = "Collections"
    thumbnails_step = 100
    NAME_FAVS = "___favorites___"
    NAME_RECENTS = "___recents___"
    FOLDER_HASHDIR = "hashdir"
    FOLDER_PRELOAD = "_preload"
    APP_SUPPORT_DIR = os.path.expanduser(f"~/Library/Application Support/{APP_NAME}")
    APP_SUPPORT_JSON = f"{APP_SUPPORT_DIR}/cfg.json"
    APP_SUPPORT_DB = f"{APP_SUPPORT_DIR}/db.db"
    APP_SUPPORT_HASHDIR = f"{APP_SUPPORT_DIR}/{FOLDER_HASHDIR}"
    PRELOAD_DB = f"{FOLDER_PRELOAD}/db.db"
    PRELOAD_HASHDIR = f"{FOLDER_PRELOAD}/{FOLDER_HASHDIR}"
    PRELOAD_HASHDIR_ZIP = f"{FOLDER_PRELOAD}/hashdir.zip"

    ext_jpeg = (
        ".jpg", ".JPG",
        ".jpeg", ".JPEG",
        ".jpe", ".JPE",
        ".jfif", ".JFIF",
        ".bmp", ".BMP",
        ".dib", ".DIB",
        ".webp", ".WEBP",
        ".ppm", ".PPM",
        ".pgm", ".PGM",
        ".pbm", ".PBM",
        ".pnm", ".PNM",
        ".gif", ".GIF",
        ".ico", ".ICO",
    )

    ext_tiff = (
        ".tif", ".TIF",
        ".tiff", ".TIFF",
    )

    ext_psd = (
        ".psd", ".PSD",
        ".psb", ".PSB",
    )

    ext_png = (
        ".png", ".PNG",
    )

    ext_raw = (
        ".nef", ".NEF",
        ".cr2", ".CR2",
        ".cr3", ".CR3",
        ".arw", ".ARW",
        ".raf", ".RAF",
        ".dng", ".DNG",
        ".rw2", ".RW2",
        ".orf", ".ORF",
        ".srw", ".SRW",
        ".pef", ".PEF",
        ".rwl", ".RWL",
        ".mos", ".MOS",
        ".kdc", ".KDC",
        ".mrw", ".MRW",
        ".x3f", ".X3F",
    )

    ext_video = (
        ".avi", ".AVI",
        ".mp4", ".MP4",
        ".mov", ".MOV",
        ".mkv", ".MKV",
        ".wmv", ".WMV",
        ".flv", ".FLV",
        ".webm", ".WEBM",
    )

    ext_all = (
        *ext_jpeg,
        *ext_tiff,
        *ext_psd,
        *ext_png,
        *ext_raw,
        *ext_video,
    )

    ext_non_layers = (
        *ext_jpeg,
        *ext_png,
        *ext_raw,
        *ext_video
    )

    ext_layers = (
        *ext_psd,
        *ext_tiff
    )

    rgba_blue = "rgba(46, 89, 203, 1.0)"
    rgba_gray = "rgba(125, 125, 125, 0.5)"
    border_transparent = "2px solid transparent"
    border_blue = f"2px solid {rgba_blue}"

    border_transparent_style = f"""
        border: {border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """

    blue_bg_style = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: {rgba_blue};
        border: {border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """

    gray_bg_style = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: {rgba_gray};
        border: {border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """

class Cfg:
    app_ver: str = Static.APP_VER
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
        with open(Static.APP_SUPPORT_JSON, "r", encoding="utf-8") as file:
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
        with open(Static.APP_SUPPORT_JSON, "w", encoding="utf-8") as file:
            json.dump(cls.get_data(), file, ensure_ascii=False, indent=4)

    @classmethod
    def check_dirs(cls):
        dirs = (Static.FOLDER_PRELOAD, Static.PRELOAD_HASHDIR_ZIP, Static.PRELOAD_DB)
        if not all(os.path.exists(p) for p in dirs):
            cls.make_internal_files()
        os.makedirs(Static.APP_SUPPORT_DIR, exist_ok=True)
        if not os.path.exists(Static.APP_SUPPORT_DB):
            cls.copy_preload_db()
        if not os.path.exists(Static.APP_SUPPORT_HASHDIR):
            cls.copy_preload_hashdir_zip()
        if not os.path.exists(Static.APP_SUPPORT_JSON):
            cls.write_json_data()

    @classmethod
    def make_internal_files(cls):
        print("Создаю пустую базу данных")
        print("Создаю пустую hashdir")
        os.makedirs(Static.FOLDER_PRELOAD, exist_ok=True)
        open(Static.PRELOAD_DB, "w").close()

        os.makedirs(Static.PRELOAD_HASHDIR, exist_ok=True)
        dummy_file = os.path.join(Static.PRELOAD_HASHDIR, 'dummy.keep')
        open(dummy_file, 'a').close()

        shutil.make_archive(
            base_name=os.path.join(Static.FOLDER_PRELOAD, Static.FOLDER_HASHDIR), 
            format="zip",
            root_dir=Static.FOLDER_PRELOAD,
            base_dir=Static.FOLDER_HASHDIR
        )
        shutil.rmtree(Static.PRELOAD_HASHDIR)

    @classmethod
    def copy_preload_hashdir_zip(cls):
        # удаляем пользовательскую hashdir из ApplicationSupport
        if os.path.exists(Static.APP_SUPPORT_HASHDIR):
            print("Удаляю пользовательскую HASH_DIR")
            shutil.rmtree(Static.APP_SUPPORT_HASHDIR)

        print("копирую предустановленную HASH_DIR")
        dest = shutil.copy2(Static.PRELOAD_HASHDIR_ZIP, Static.APP_SUPPORT_DIR)
        shutil.unpack_archive(dest, Static.APP_SUPPORT_DIR)
        os.remove(dest)

    @classmethod
    def copy_preload_db(cls):
        # удаляем пользовательный db.db из Application Support если он есть
        if os.path.exists(Static.APP_SUPPORT_DB):
            print("Удаляю пользовательский DB_FILE")
            os.remove(Static.APP_SUPPORT_DB)

        print("Копирую предустановленный DB_FILE")
        shutil.copy2(Static.PRELOAD_DB, Static.APP_SUPPORT_DIR)

    @classmethod
    def init(cls):
        cls.check_dirs()
        cls.set_json_data()


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    f_date_start: str = None # 1 january 1991
    f_date_end: str = None # 31 january 1991
    thumbnails_count: int = 0
    search_widget_text: str = None

    # индекс соответствующий STATIC > IMG_LABEL_SIZE
    # от индекса зависит размер Thumbnail и всех его внутренних виджетов
    thumb_size_index: int = 0
    current_dir: str = None
    sort_by_mod: bool = True
    show_all_images: bool = True
    enabled_filters: list[str] = []
    favs: bool = False