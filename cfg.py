import json
import os
import shutil
import webbrowser
from datetime import datetime


class ThumbData:

    # максимальный размер в пикселях по широкой стороне
    # для кешируемого изображения
    DB_PIXMAP_SIZE: int = 200

    # ширина и высота Thumbnail
    THUMB_H = [115, 135, 160, 230]
    THUMB_W = [140, 140, 180, 230]

    # максимальный размер в пикселях по широкой стороне для изображения
    # должен быть меньше высоты и ширины Thumb
    PIXMAP_SIZE: list = [60, 80, 100, 170]

    # ширина текстового виджета ограничивается количеством символов на строку
    MAX_ROW: list = [17, 17, 22, 30]

    # растояние между изображением и текстовым виджетом
    SPACING = 2

    # дополнительное пространство вокруг Pixmap
    OFFSET = 15


class Static:

    APP_VER = 1.3
    APP_NAME: str = "Collections"

    # сколько папок с коллекциями программа будет анализировать
    # для интеграции новой папки с коллекциями нужно
    # добавить в BRANDS новое произвольное имя
    # созависимые аттрибуты:
    # JsonData.collfolders, JsonData.stopcolls
    # при инициации будет проверка на соответствие длин
    BRANDS = ["miuz", "panacea"]

    # в сетке изображений может отображаться за раз 150 штук
    GRID_LIMIT: int = 100
    GRID_SPACING: int = 5

    # скачать системные файлы _preload
    LINK_DB = "https://disk.yandex.ru/d/XKf6xaqzL6om9w"

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

    # ДИРЕКТОРИИ # ДИРЕКТОРИИ # ДИРЕКТОРИИ # ДИРЕКТОРИИ # ДИРЕКТОРИИ 
    APP_SUPPORT_DIR: str = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        APP_NAME
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


    PRELOAD_FOLDER: str = "_preload"

    PRELOAD_DB: str = os.path.join(
        PRELOAD_FOLDER,
        "db.db"
        )

    PRELOAD_HASHDIR_ZIP: str = os.path.join(
        PRELOAD_FOLDER,
        "hashdir.zip"
        )


    # РАСШИРЕНИЯ # РАСШИРЕНИЯ # РАСШИРЕНИЯ # РАСШИРЕНИЯ # РАСШИРЕНИЯ 
    LAYERS_EXT: tuple = (
        ".psd", ".psb", ".tiff", ".tif",
        ".PSD", ".PSB", ".TIFF", ".TIF"
        )

    JPG_EXT: tuple = (
        ".jpg", ".jpeg", ".jfif", ".png",
        ".JPG", ".JPEG", ".JFIF", ".PNG"
        )
    
    IMG_EXT = JPG_EXT + LAYERS_EXT


    # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ # СТИЛИ 
    RGB_BLUE = "rgb(46, 89, 203)"
    RGB_GRAY = "rgba(125, 125, 125, 0.5)"
    BORDER_INV = "2px solid transparent"
    BORDER_BLUE = f"2px solid {RGB_BLUE}"

    NORMAL_STYLE = f"""
        border: {BORDER_INV};
    """

    SOLID_STYLE = f"""
        border-radius: 6px;
        color: rgb(255, 255, 255);
        background: {RGB_BLUE};
        border: {BORDER_INV};
    """

    SOLID_GRAY_STYLE = f"""
        border-radius: 6px;
        color: rgb(255, 255, 255);
        background: {RGB_GRAY};
        border: {BORDER_INV};
    """

    BORDERED_STYLE = f"""
        border-radius: 6px;
        border: {BORDER_BLUE};
    """

    TITLE_NORMAL = f"""
        font-size: 18pt;
        font-weight: bold;
        border: {BORDER_INV};
    """

    TITLE_SOLID = f"""
        font-size: 18pt;
        font-weight: bold;
        color: rgb(255, 255, 255);
        {SOLID_STYLE}
    """


    # папка со всеми CVG
    IMAGES = "images"
    CACHED_IMAGES_COUNT = 50
    IMAGES_GRID_SPACING = 2


class Filters:
    current: list["Filters"] = []
    __slots__ = ["names", "real", "value", "system"]

    def __init__(self, names: list, real: str, value: bool, system: bool):
        self.names = names
        self.real = real
        self.value = value
        self.system = system
    
    @classmethod
    def init_filters(cls):
        # длина names должна соответстовать количеству языков из 
        # lang > Lang
        # real это реальное имя папки по которой будет фильтрация
        # system не трогать, всегда False
        cls.current = [
                    Filters(
                        names=["Продукт", "Product"],
                        real="1 IMG",
                        value=False,
                        system=False
                    ),
                    Filters(
                        names=["Модели", "Model"], 
                        real="2 MODEL IMG", 
                        value=False, 
                        system=False
                    ),
                    Filters(
                        names=["Остальное", "Other"], 
                        real=None, 
                        value=False, 
                        system=True
                    ),
                ]


class JsonData:

    # ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ ЕСЛИ ЕЩЕ НЕТ КОНФИГ ФАЙЛА В APP_SUPPORT

    app_ver: str = Static.APP_VER

    # индекс соответствующий Static > BRANDS
    brand_ind = 0

    # индекс соответствующий Lang
    lang_ind = 0
    
    # как часто utils > scaner будет просматривать collfolders на изменения
    scaner_minutes: int = 5
    
    udpdate_file_paths = [
        '/Volumes/Shares/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        '/Volumes/Shares-3/Studio/MIUZ/Photo/Art/Raw/2024/soft/MiuzCollections.zip',
        ]

    stopcolls: list[list[str]] = [
        [
            "_Archive_Commerce_Брендинг",
            "Chosed",
            "LEVIEV"
        ],
        [], 
    ]

    collfolders: list[list[str]] = [
        # miuz coll folders
        [
            '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
            '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
        ],
        # panacea coll folders
        [
            '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
            '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
            '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
            ]
    ]

    @classmethod
    def _get_data(cls) -> dict[str, str]:
        """returns user attibutes and values"""
        return {
            k: v
            for k, v in vars(cls).items()
            if not k.startswith("__")
            and
            not callable(getattr(cls, k))
        }

    @classmethod
    def _set_json_data(cls) -> dict:

        with open(Static.JSON_FILE, 'r', encoding="utf-8") as f:

            try:
                json_data: dict = json.load(f)

            except json.JSONDecodeError:
                print("Ошибка чтения json")
                json_data = cls._get_data()
            
        for k, v in json_data.items():

            if hasattr(cls, k):

                if type(v) == type(getattr(cls, k)):
                    setattr(cls, k, v)

                else:
                    print("Несоответствие типа, ключ:", k)

    @classmethod
    def write_json_data(cls):

        with open(Static.JSON_FILE, 'w', encoding="utf-8") as f:

            json.dump(
                obj=cls._get_data(),
                fp=f,
                indent=4,
                ensure_ascii=False

            )

    @classmethod
    def _check_dirs(cls):

        if not os.path.exists(Static.PRELOAD_FOLDER):
            t = "скачайте _preload.zip и распакуйте в корень проекта"
            webbrowser.open(Static.LINK_DB)
            raise Exception(t)

        if not os.path.exists(Static.APP_SUPPORT_DIR):
            os.makedirs(name=Static.APP_SUPPORT_DIR, exist_ok=True)

        if not os.path.exists(Static.DB_FILE):
            cls.copy_db_file()

        if not os.path.exists(Static.HASH_DIR):
            cls.copy_hashdir()

        if not os.path.exists(Static.JSON_FILE):
            cls.write_json_data()

    @classmethod
    def copy_hashdir(cls):

        # удаляем пользовательскую hashdir из ApplicationSupport
        if os.path.exists(Static.HASH_DIR):
            print("Удаляю пользовательскую HASH_DIR")
            from utils.utils import Utils
            Utils.rm_rf(Static.HASH_DIR)

        # копируем предустановленную hashdir в AppliactionSupport
        if os.path.exists(Static.PRELOAD_HASHDIR_ZIP):
            print("копирую предустановленную HASH_DIR")
            dest = shutil.copy2(Static.PRELOAD_HASHDIR_ZIP, Static.APP_SUPPORT_DIR)
            shutil.unpack_archive(dest, Static.APP_SUPPORT_DIR)
            os.remove(dest)

        # если нет предустановленной то просим скачать и положить в корень проекта
        else:
            t = "скачайте _preload.zip и распакуйте в корень проекта"
            webbrowser.open(Static.LINK_DB)
            raise Exception(t)

    @classmethod
    def copy_db_file(cls):

        # удаляем пользовательный db.db из Application Support если он есть
        if os.path.exists(Static.DB_FILE):
            print("Удаляю пользовательский DB_FILE")
            os.remove(Static.DB_FILE)

        # копируем предустановленный db.db если он есть
        if os.path.exists(Static.PRELOAD_DB):
            print("Копирую предустановленный DB_FILE")
            shutil.copy2(Static.PRELOAD_DB, Static.APP_SUPPORT_DIR)

        # иначе просим скачать или создать пользовательский db.db 
        # с таблицей database > THUMBS
        else:
            t = "скачайте _preload.zip и распакуйте в корень проекта"
            webbrowser.open(Static.LINK_DB)
            raise Exception(t)

    @classmethod
    def _compare_versions(cls) -> bool:

        if not isinstance(cls.app_ver, float):
            raise Exception("app_ver должна быть float")

        elif Static.APP_VER > cls.app_ver:
            cls.app_ver = Static.APP_VER
            print("Внутренняя версия выше json версии")
            return False
        
        else:
            return True

    @classmethod
    def init(cls):
        cls._check_dirs()
        cls._set_json_data()
        assert len(Static.BRANDS) == len(cls.stopcolls) == len(cls.collfolders)

        # если версии не совпадают то что то нужно сделать
        # например копировать новые файлы или ...
        cls._compare_versions()

        # инициируем пользовательские фильтры
        Filters.init_filters()


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
    types = [
        Static.JPG_EXT,
        Static.LAYERS_EXT
    ]

    # стандартная папка загрузок
    down_folder: str = os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    )

    # размер окна просмотра изображений
    imgview_g: dict = {
        "aw": 700,
        "ah": 500
        }

    # размер главного окна
    root_g: dict = {
        "aw": 700,
        "ah": 500
        }

    # индекс соответствующий STATIC > IMG_LABEL_SIZE
    # от индекса зависит размер Thumbnail и всех его внутренних виджетов
    thumb_size_ind: int = 0