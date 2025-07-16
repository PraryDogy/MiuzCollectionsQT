import json
import os
import shutil
import traceback
from datetime import datetime

from pydantic import BaseModel


class ThumbData:

    # максимальный размер в пикселях по широкой стороне
    # для кешируемого изображения
    DB_PIXMAP_SIZE: int = 200

    # ширина и высота Thumbnail
    THUMB_H = [150, 185, 270]
    THUMB_W = [150, 190, 240]

    # максимальный размер в пикселях по широкой стороне для изображения
    # должен быть меньше высоты и ширины Thumb
    PIXMAP_SIZE: list = [70, 100, 170]

    # ширина текстового виджета ограничивается количеством символов на строку
    MAX_ROW: list = [19, 25, 32]

    CORNER: list = [9, 12, 15]

    # растояние между изображением и текстовым виджетом
    SPACING = 0

    # дополнительное пространство вокруг Pixmap
    OFFSET = 15


class Static:

    APP_VER = "2.25"
    APP_NAME: str = "Collections"

    # в сетке изображений может отображаться за раз 150 штук
    GRID_LIMIT: int = 100

    # ширина главного меню...
    MENU_LEFT_WIDTH: int = 210

    # внутренние имена для "все коллекции", "избранное", "недавние"
    # можно задавать произвольные имена
    NAME_ALL_COLLS: str = "___collections___"
    NAME_FAVS: str = "___favorites___"
    NAME_RECENTS: str = "___recents___"

    # для метки "избранное", произвольный
    STAR_SYM = "\U00002605" + " "

    # это символ новой строки в QLabel
    PARAGRAPH_SEP = "\u2029"
    LINE_FEED  = "\u000a"

    HASHDIR_NAME = "hashdir"
    PRELOAD_NAME: str = "_preload"
    INNER_IMAGES = "images"

    # ДИРЕКТОРИИ # ДИРЕКТОРИИ # ДИРЕКТОРИИ # ДИРЕКТОРИИ # ДИРЕКТОРИИ 
    APP_SUPPORT_DIR: str = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        APP_NAME
        )

    APP_SUPPORT_JSON_DATA: str = os.path.join(APP_SUPPORT_DIR, "cfg.json")
    APP_SUPPORT_DB: str = os.path.join(APP_SUPPORT_DIR, "db.db")
    APP_SUPPORT_HASHDIR: str = os.path.join(APP_SUPPORT_DIR, HASHDIR_NAME)
    APP_SUPPORT_BACKUP: str = os.path.join(APP_SUPPORT_DIR, "backup")

    PRELOAD_DB: str = os.path.join(PRELOAD_NAME, "db.db")
    PRELOAD_HASHDIR: str = os.path.join(PRELOAD_NAME, HASHDIR_NAME)
    PRELOAD_HASHDIR_ZIP: str = os.path.join(PRELOAD_NAME, "hashdir.zip")

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

    # РАСШИРЕНИЯ # РАСШИРЕНИЯ # РАСШИРЕНИЯ # РАСШИРЕНИЯ # РАСШИРЕНИЯ     

    # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ 
    blue_color = "rgb(46, 89, 203)"
    gray_color = "rgba(125, 125, 125, 0.5)"
    border_transparent = "2px solid transparent"
    border_blue = f"2px solid {blue_color}"

    border_transparent_style = f"""
        border: {border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """

    blue_bg_style = f"""
        border-radius: 7px;
        color: rgb(255, 255, 255);
        background: {blue_color};
        border: {border_transparent};
        padding-left: 2px;
        padding-right: 2px;
    """


class JsonDataModel(BaseModel):
    app_ver: str
    lang_ind: int
    dark_mode: int
    scaner_minutes: int
    apps: list[str]


class JsonData:
    app_ver: str = Static.APP_VER
    lang_ind: int = 0
    dark_mode: int = 0
    scaner_minutes: int = 5
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
    def set_json_data(cls) -> None:
        model = cls.load_json_data()
        if model:
            cls.app_ver = model.app_ver
            cls.lang_ind = model.lang_ind
            cls.dark_mode = model.dark_mode
            cls.scaner_minutes = model.scaner_minutes
            cls.apps = model.apps
        else:
            # cls.set_attributes()
            cls.write_json_data()

    @classmethod
    def set_attributes(cls) -> None:
        try:
            with open(Static.APP_SUPPORT_JSON_DATA, "r", encoding="utf-8") as f:
                data: dict = json.load(f)
            for k, v in data.items():
                if hasattr(cls, k) and type(v) == type(getattr(cls, k)):
                    setattr(cls, k, v)
        except Exception as e:
            print("Ошибка чтения json файла в set_attributes")

    @classmethod
    def write_json_data(cls) -> None:
        model = JsonDataModel(
            app_ver=cls.app_ver,
            lang_ind=cls.lang_ind,
            dark_mode=cls.dark_mode,
            scaner_minutes=cls.scaner_minutes,
            apps=cls.apps
        )
        with open(Static.APP_SUPPORT_JSON_DATA, "w", encoding="utf-8") as f:
            json.dump(model.model_dump(), f, indent=4, ensure_ascii=False)

    @classmethod
    def load_json_data(cls) -> JsonDataModel | None:
        try:
            with open(Static.APP_SUPPORT_JSON_DATA, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                return JsonDataModel(**raw_data)
        except Exception as e:
            try:
                # Пытаемся подмержить с дефолтами, если ошибка валидации
                with open(Static.APP_SUPPORT_JSON_DATA, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                defaults = JsonDataModel(
                    app_ver=cls.app_ver,
                    lang_ind=cls.lang_ind,
                    dark_mode=cls.dark_mode,
                    scaner_minutes=cls.scaner_minutes,
                    apps=cls.apps
                ).model_dump()
                merged = {**defaults, **raw_data}
                return JsonDataModel(**merged)
            except Exception as e:
                print("Ошибка при чтении и объединении JSON:", e)
                return None

    @classmethod
    def check_dirs(cls):
        if not all(os.path.exists(p) for p in (
            Static.PRELOAD_NAME,
            Static.PRELOAD_HASHDIR_ZIP,
            Static.PRELOAD_DB
        )):
            cls.make_internal_files()

        os.makedirs(Static.APP_SUPPORT_DIR, exist_ok=True)
        os.makedirs(Static.APP_SUPPORT_BACKUP, exist_ok=True)

        if not os.path.exists(Static.APP_SUPPORT_DB):
            cls.copy_preload_db()

        if not os.path.exists(Static.APP_SUPPORT_HASHDIR):
            cls.copy_preload_hashdir_zip()

        if not os.path.exists(Static.APP_SUPPORT_JSON_DATA):
            cls.write_json_data()

    @classmethod
    def make_internal_files(cls):
        print("Создаю пустую базу данных")
        print("Создаю пустую hashdir")
        os.makedirs(Static.PRELOAD_NAME, exist_ok=True)
        open(Static.PRELOAD_DB, "w").close()

        os.makedirs(Static.PRELOAD_HASHDIR, exist_ok=True)
        dummy_file = os.path.join(Static.PRELOAD_HASHDIR, 'dummy.keep')
        open(dummy_file, 'a').close()

        shutil.make_archive(
            base_name=os.path.join(Static.PRELOAD_NAME, Static.HASHDIR_NAME), 
            format="zip",
            root_dir=Static.PRELOAD_NAME,
            base_dir=Static.HASHDIR_NAME
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
    def _compare_versions(cls) -> bool:
        ...

    @classmethod
    def init(cls):
        cls.check_dirs()
        cls.set_json_data()
        cls._compare_versions()


class Dynamic:
    date_start: datetime = None
    date_end: datetime = None
    f_date_start: str = None # 1 january 1991
    f_date_end: str = None # 31 january 1991
    grid_offset: int = 0
    search_widget_text: str = None
    curr_coll_name = Static.NAME_ALL_COLLS
    resents: bool = False

    # какие расширения отображать по умолчанию (и джепеги и послойники)
    types = [Static.ext_non_layers, Static.ext_layers]

    # индекс соответствующий STATIC > IMG_LABEL_SIZE
    # от индекса зависит размер Thumbnail и всех его внутренних виджетов
    thumb_size_ind: int = 0