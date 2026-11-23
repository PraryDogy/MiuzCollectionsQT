"""
preview_windows.py: открывает все окна проекта разом для проверки интерфейса.

Запуск из папки проекта (рядом с start.py):
    python preview_windows.py            # все окна виджетов
    python preview_windows.py --main     # + главное окно (без сканера)
    python preview_windows.py --geo      # + окна geo_finder.py
                                         #   (он при старте очистит свою папку
                                         #   в Application Support/GeoFinder)

Безопасность: данные приложения НЕ используются. До импорта рабочих модулей
Static переключается на временную песочницу, поэтому не затрагиваются
ни db.db, ни cfg.json, ни mf.json, ни servers.json. Песочница удаляется
при выходе. Окна копирования работают только с файлами песочницы.
"""
import argparse
import atexit
import importlib
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

# На верхнем уровне только стандартная библиотека. Дочерние процессы (spawn)
# заново импортируют этот файл, и тяжёлые импорты здесь замедлили бы их старт.


# ---------------------------------------------------------------------------
# Песочница
# ---------------------------------------------------------------------------

def make_sandbox() -> Path:
    from PIL import Image

    root = Path(tempfile.mkdtemp(prefix="collections_preview_"))
    (root / "app_data" / "hashdir").mkdir(parents=True)
    (root / "catalog" / "Копия").mkdir(parents=True)
    src = root / "catalog" / "Фото"
    src.mkdir(parents=True)

    Image.new("RGB", (900, 600), (200, 70, 70)).save(src / "sample_red.jpg", quality=90)
    Image.new("RGB", (900, 600), (60, 130, 220)).save(src / "sample_blue.png")
    return root


def patch_static(root: Path) -> None:
    """Подменяет пути данных ДО первого обращения к БД и конфигам."""
    from cfg import Static

    app_data = root / "app_data"
    Static.APP_DATA_DIR = app_data
    Static.CFG_JSON = app_data / "cfg.json"
    Static.DB_FILE = app_data / "db.db"
    Static.HASHDIR = app_data / "hashdir"
    Static.MF_JSON = app_data / "mf.json"
    Static.FILTERS_JSON = app_data / "filters.json"
    Static.SERVERS_JSON = app_data / "servers.json"


def init_app(root: Path):
    """Минимальный аналог App.validate() из start.py, без первого запуска."""
    from cfg import JsonData, Static
    from system.database import Dbase
    from system.items import Filters, Mf
    from system.lang import Lng
    from system.runnable import UThreadPool
    from system.themes import ThemeChanger

    Static.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    Static.HASHDIR.mkdir(parents=True, exist_ok=True)
    Static.DB_FILE.touch(exist_ok=True)

    Lng.init_lang(JsonData.lng_index)
    Filters.json_to_app(Static.DEFAULT_FILTERS)

    mf = Mf(
        mf_alias="Preview",
        mf_paths=[str(root / "catalog" / "Фото")],
        mf_stop_list=[],
    )
    Mf.items = [mf]
    Mf.current_mf = mf

    Dbase.init()
    UThreadPool.init()
    ThemeChanger.init()  # читает ./themes относительно папки проекта
    return mf


# ---------------------------------------------------------------------------
# Тестовые данные для окон
# ---------------------------------------------------------------------------

def make_data_items(root: Path):
    from PyQt6.QtGui import QImage
    from system.items import DataItem

    src = root / "catalog" / "Фото"
    items = []
    for path in sorted(src.iterdir()):
        items.append(DataItem(
            base_qimage=QImage(str(path)),
            resized_qimages=[None] * 4,
            rel_thumb_path="",
            rel_path="/" + path.name,
            abs_path=str(path),
            fav=False,
            day_month_year="18.11.2026",
            hour_min_sec="12:00:00",
            filename=path.name,
            ext=path.suffix.lstrip(".").upper(),
        ))
    return items


def _new(module: str, name: str, *args, **kwargs):
    """Импортирует класс по имени модуля и создаёт экземпляр."""
    cls = getattr(importlib.import_module(module), name)
    return cls(*args, **kwargs)


def _img_view_item(items):
    from widgets.win_image_view import ImgViewItem
    return ImgViewItem(
        start_data_item=items[0],
        data_items=items,
        is_selection=False,
        image_apps={},
    )


def _size_items(mf):
    from system.runnable import HashDirSizeItem
    return [HashDirSizeItem(mf=mf, size=12_345_678, total_images=3)]


# ---------------------------------------------------------------------------
# Список окон
# ---------------------------------------------------------------------------

def build_factories(root: Path, mf, items, with_main: bool, with_geo: bool):
    from PyQt6.QtGui import QPixmap
    copy_src = [items[0].abs_path]
    copy_dest = str(root / "catalog" / "Копия")
    sample_pixmap = QPixmap.fromImage(items[0].base_qimage)

    factories = [
        # поиск и просмотр
        ("Поиск по изображению", lambda: _new("widgets.win_img_search", "WinImgSearch")),
        ("Прогресс поиска", lambda: _new("widgets.win_img_search", "ProgressWin")),
        ("Просмотр изображения", lambda: _new("widgets.win_image_view", "WinImageView", _img_view_item(items))),
        ("Информация о файле", lambda: _new("widgets.win_info", "WinInfo", items[0])),
        ("Коллаж", lambda: _new("widgets.win_collage", "WinCollage", items)),
        ("Текстовый поиск", lambda: _new("widgets.win_text_search", "WinTextSearch")),
        ("Календарь", lambda: _new("widgets.win_calendar", "WinCalendar")),
        ("Фильтры", lambda: _new("widgets.win_filters", "WinFilters")),

        # настройки и каталоги
        ("Настройки", lambda: _new("widgets.win_settings", "WinSettings")),
        ("Размер данных", lambda: _new("widgets.win_settings", "SizesWin", _size_items(mf))),
        ("Новый каталог", lambda: _new("widgets.win_settings", "NewMfWin")),
        ("Стоп-лист", lambda: _new("widgets.win_settings", "IgnoreListWin", mf)),
        ("Восстановление каталога", lambda: _new("widgets.win_settings", "MfRepairWin")),
        ("Отмена изменений", lambda: _new("widgets.win_settings", "CancelChangesWin",
                                          "Отменить несохранённые изменения?")),
        ("Подключение SMB", lambda: _new("widgets.win_smb", "WinSmb", mf)),

        # серверы и файлы
        ("Серверы", lambda: _new("widgets.win_servers", "ServersWin")),
        ("Вход на сервер", lambda: _new("widgets.win_servers", "LoginWin")),
        ("Загрузка файлов", lambda: _new("widgets.win_upload", "UploadWin", copy_src[0])),
        ("Копирование (песочница)", lambda: _new("widgets.win_copy_files", "WinCopyFiles",
                                                 target_dir=copy_dest, files_to_copy=copy_src)),
        ("Замена файла", lambda: _new("widgets.win_copy_files", "ReplaceWin", "sample_red.jpg", True)),
        ("Первый запуск", lambda: _new("widgets.win_first_load", "FirstLoadWin")),

        # базовые диалоги
        ("Подтверждение", lambda: _new("widgets._base_widgets", "ConfirmWindow",
                                       "Длинный текст предупреждения в несколько строк для теста длины hfhfhfhfhhfhfhf")),
        ("Подтверждение опасное", lambda: _new("widgets._base_widgets", "ConfirmWindow",
                                               "Длинный текст предупреждения в несколько строк для теста длины", danger=True)),
        ("Предупреждение", lambda: _new("widgets._base_widgets", "WarningWindow",
                                        "Длинный текст предупреждения в несколько строк для теста длины")),
        ("Ввод текста", lambda: _new("widgets._base_widgets", "InputTextWin", "Новый тег",  "Придумайте название нового тега")),
        ("Индикатор прогресса", lambda: _new("widgets._base_widgets", "WinProgressbar", "Выполняется")),
    ]

    factories.sort(key=lambda x: x[0])

    if with_main:
        # WinMain с аргументом noscan: сканер не запускается, БД только читается
        factories.append(
            ("Главное окно (без сканера)", lambda: _new("widgets.win_main", "WinMain", ["noscan"]))
        )

    if with_geo:
        factories += [
            ("GeoFinder: главное окно", lambda: _new("geo_finder", "MainWindow")),
            ("GeoFinder: процесс", lambda: _new("geo_finder", "ProcessDialog", "Ищу цвета (пример)")),
        ]

    return factories


# ---------------------------------------------------------------------------
# Открытие
# ---------------------------------------------------------------------------

def position(index: int, cols: int = 4) -> tuple[int, int]:
    return 40 + (index % cols) * 360, 40 + (index // cols) * 320


def open_all(factories):
    from PyQt6.QtCore import Qt

    windows, failed = [], []
    for index, (name, factory) in enumerate(factories):
        try:
            win = factory()
        except Exception:
            failed.append(name)
            print(f"[ОШИБКА] {name}\n{traceback.format_exc()}")
            continue

        # Конструкторы UMainWindow ставят ApplicationModal: из-за этого
        # открытые разом окна блокировали бы друг друга. Снимаем модальность.
        win.setWindowModality(Qt.WindowModality.NonModal)
        win.move(*position(index))
        win.show()

        windows.append(win)  # ссылка нужна, иначе окно соберёт сборщик мусора
        print(f"[ок] {name}")
    return windows, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Открыть все окна проекта")
    parser.add_argument("--main", action="store_true", help="добавить главное окно (без сканера)")
    parser.add_argument("--geo", action="store_true", help="добавить окна geo_finder.py")
    args = parser.parse_args()

    os.chdir(PROJECT_DIR)
    sys.path.insert(0, str(PROJECT_DIR))

    root = make_sandbox()
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    patch_static(root)

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    mf = init_app(root)
    items = make_data_items(root)
    factories = build_factories(root, mf, items, args.main, args.geo)

    windows, failed = open_all(factories)
    print(f"\nОткрыто окон: {len(windows)}, с ошибками: {len(failed)}")
    if failed:
        print("Не открылись:", ", ".join(failed))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
