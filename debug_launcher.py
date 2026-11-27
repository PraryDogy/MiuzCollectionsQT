"""
debug_launcher.py: отладочный запуск окон проекта с применённой темой.

Запуск из папки проекта (рядом с start.py):
    python debug_launcher.py                  # окно с кнопками
    python debug_launcher.py --all            # сразу открыть все окна
    python debug_launcher.py --theme dark     # тема при старте: dark, light, auto
    python debug_launcher.py --main --geo     # + главное окно и окна GeoFinder

Данные приложения не затрагиваются: используется песочница (см. make_sandbox).
Тема меняется кнопками и применяется ко всем открытым окнам сразу,
cfg.json при этом не записывается.
Escape закрывает активное окно; Escape в лаунчере закрывает все окна.
Закрытие лаунчера крестиком закрывает все окна и завершает приложение.
"""
import argparse
import atexit
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout

from cfg import JsonData, Static
from system.themes import ThemeChanger
from widgets._base_widgets import (ActiveButton, TransparentLabel,
                                   TransparentWidget, UMainWindow, UPushButton)

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = Path(__file__).resolve()

THEME_CHOICES = [
    ("Тёмная", "dark"),
    ("Светлая", "light"),
    ("Авто", "auto"),
]

YY = 100  # верхний отступ лаунчера на экране

# Лаунчер нужен фабрикам диалогов как родитель. Заполняется в main().
_LAUNCHER = None


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
    """Подменяет пути данных до первого обращения к БД и конфигам."""
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
    from system.database import Dbase
    from system.items import Filters, Mf
    from system.lang import Lng
    from system.runnable import UThreadPool

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
# Тестовые данные и фабрики окон
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
    """Импортирует класс по имени модуля и создаёт экземпляр.
    Импорт внутри фабрики: после reload_window_modules берётся свежий класс."""
    cls = getattr(importlib.import_module(module), name)
    return cls(*args, **kwargs)


def _new_nonmodal(module: str, name: str, *args, **kwargs):
    """Создаёт окно без ApplicationModal.

    VerticalWin вызывает set_always_on_top() в __init__, а тот делает окно
    ApplicationModal. Подменяем метод только на время конструктора.
    """
    cls = getattr(importlib.import_module(module), name)
    original = cls.set_always_on_top
    cls.set_always_on_top = lambda self: None
    try:
        return cls(*args, **kwargs)
    finally:
        cls.set_always_on_top = original


def _lng(key: str) -> str:
    from system.lang import Lng
    return getattr(Lng, key)


def _confirm(btn: str, icon: str, text: str):
    def make():
        return _new_nonmodal("widgets._base_widgets", "ConfirmWin", text, btn, icon)
    return make


def _alert(btn: str, icon: str, text: str):
    def make():
        return _new_nonmodal("widgets._base_widgets", "AllertWin", text, btn, icon)
    return make


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


LONG_TEXT = ("Длинный текст предупреждения в несколько строк для теста длины "
             "б бкбкбк цуфкцубук ")


def build_factories(root: Path, mf, items, with_main: bool, with_geo: bool):
    copy_src = [items[0].abs_path]
    copy_dest = str(root / "catalog" / "Копия")

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
        ("Отмена изменений", lambda: _new("widgets.win_settings", "CancelChangesWin", _LAUNCHER, _lng("unsaved_changes_confirm"))),
        ("Подключение SMB", lambda: _new("widgets.win_smb", "WinSmb", mf)),
        ("О программе", lambda: _new("widgets.bar_macos", "AboutWin", parent=_LAUNCHER)),

        # серверы и файлы
        ("Серверы", lambda: _new("widgets.win_servers", "ServersWin")),
        ("Вход на сервер", lambda: _new("widgets.win_servers", "LoginWin")),
        ("Загрузка файлов", lambda: _new("widgets.win_upload", "UploadWin", _LAUNCHER, dest=copy_dest)),
        ("Копирование (песочница)", lambda: _new("widgets.win_copy_files", "WinCopyFiles",
                                                 target_dir=copy_dest, files_to_copy=copy_src)),
        ("Замена файла", lambda: _new_nonmodal("widgets.win_copy_files", "ReplaceWin",
                                            "sample_red_very long filename_sample_red_very_long_filename.jpg", True)),
        ("Замена файла без чекбокса", lambda: _new_nonmodal("widgets.win_copy_files", "ReplaceWin",
                                                            _LAUNCHER,
                                                            "sample_red_very_long_filename_sample_red_very_long_filename.jpg", False)),
        ("Первый запуск", lambda: _new("widgets.win_first_load", "FirstLoadWin")),

        # диалоги с короткими и длинными текстами
        ("Подтверждение: короткий текст", _confirm("blue", "yellow", "Короткий текст")),
        ("Подтверждение: длинный текст", _confirm("blue", "yellow", LONG_TEXT)),
        ("Алерт: короткий текст", _alert("blue", "yellow", "Короткий текст")),
        ("Алерт: длинный текст", _alert("blue", "yellow", LONG_TEXT)),
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
# Перезагрузка и фильтры событий
# ---------------------------------------------------------------------------

def reload_window_modules() -> None:
    """Перечитывает модули окон из widgets/, чтобы подхватить правки без перезапуска.

    Базовые классы (widgets/_base_widgets.py) и system/* не перечитываются:
    их изменения требуют перезапуска лаунчера (кнопка «Перезапустить»).
    """
    skip = {"widgets", "widgets._base_widgets"}
    for name in sorted(list(sys.modules)):
        if name.startswith("widgets.") and name not in skip:
            try:
                importlib.reload(sys.modules[name])
            except Exception:
                print(f"[перезагрузка] ошибка в {name}\n{traceback.format_exc()}", flush=True)


class CloseFilter(QObject):
    """Перехватывает закрытие окна и закрывает его принудительно.

    Часть окон в closeEvent() вызывает event.ignore() (несохранённые изменения,
    ожидание потоков). В лаунчере владельца нет, поэтому такие окна не закрылись
    бы. Для отладки логику из closeEvent() пропускаем.
    """

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Close:
            print(f"[закрыто] {obj.windowTitle()}", flush=True)
            obj.hide()
            obj.deleteLater()
            return True
        return False


class EscapeFilter(QObject):
    """Application-level фильтр: Escape закрывает активное окно.

    Перехватывает нажатие до виджета, поэтому работает независимо от фокуса.
    В лаунчере Escape закрывает все окна.
    """

    def __init__(self, launcher):
        super().__init__()
        self.launcher = launcher

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            win = QApplication.activeWindow()
            if win is None:
                return False
            if win is self.launcher:
                self.launcher.close_all()
            else:
                win.close()
            return True
        return False


# ---------------------------------------------------------------------------
# Лаунчер
# ---------------------------------------------------------------------------

class Launcher(UMainWindow):
    def __init__(self, factories, flags: list[str]):
        super().__init__()
        self.setWindowTitle("Отладка: окна проекта")
        self.setMinimumWidth(620)
        self.factories = factories
        self.flags = flags        # --main / --geo, передаются при перезапуске
        self.opened = []          # ссылки на окна, иначе их соберёт сборщик мусора

        self.central_layout.setSpacing(10)
        self.central_layout.addWidget(self._build_theme_row())
        self.central_layout.addWidget(self._build_windows_grid())
        self.central_layout.addWidget(self._build_bottom_row())

        self.status = TransparentLabel("")
        self.status.set_style("gray", "regular", "regular")
        self.central_layout.addWidget(self.status)
        self.update_status()

        self._esc_filter = EscapeFilter(self)
        QApplication.instance().installEventFilter(self._esc_filter)

    # --- построение интерфейса ---

    def _build_theme_row(self):
        row = TransparentWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        lay.addWidget(TransparentLabel("Тема:"))
        for title, value in THEME_CHOICES:
            btn = UPushButton(title)
            btn.clicked.connect(lambda _=False, v=value: self.set_theme(v))
            lay.addWidget(btn)
        lay.addStretch()
        return row

    def _build_windows_grid(self):
        wid = TransparentWidget()
        grid = QGridLayout(wid)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        rows = (len(self.factories) + 1) // 2      # высота каждого столбца
        for i, (name, _) in enumerate(self.factories):
            col, row = divmod(i, rows)             # заполняем столбец сверху вниз
            btn = UPushButton(name)
            btn.clicked.connect(lambda _=False, idx=i: self.open_one(idx))
            grid.addWidget(btn, row, col)
        return wid

    def _build_bottom_row(self):
        row = TransparentWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        close_all_btn = UPushButton("Закрыть все окна")
        close_all_btn.clicked.connect(self.close_all)
        lay.addWidget(close_all_btn)
        restart_btn = UPushButton("Перезапустить")
        restart_btn.clicked.connect(self.restart_app)
        lay.addWidget(restart_btn)
        lay.addStretch()
        open_all_btn = ActiveButton("Открыть все")
        open_all_btn.clicked.connect(self.open_all)
        lay.addWidget(open_all_btn)
        return row

    # --- действия ---

    def set_theme(self, value: str):
        JsonData.theme = value           # только в памяти, cfg.json не пишется
        ThemeChanger.init()              # применяет стиль ко всему приложению
        self.update_status()

    def update_status(self):
        app = QApplication.instance()
        self.status.setText(f"Тема: {JsonData.theme}, стиль приложения: {len(app.styleSheet())} симв.")

    def center_screen(self, win) -> None:
        screen = QGuiApplication.primaryScreen().geometry()
        size = win.geometry()
        win.move((screen.width() - size.width()) // 2,
                 (screen.height() - size.height()) // 2)

    def open_one(self, index: int, pos: tuple[int, int] | None = None):
        name, factory = self.factories[index]
        reload_window_modules()              # свежий код окна при каждом открытии
        try:
            win = factory()
        except Exception:
            print(f"[ОШИБКА] {name}\n{traceback.format_exc()}", flush=True)
            self.status.setText(f"Ошибка при открытии: {name}. Смотрите консоль.")
            return

        win.installEventFilter(CloseFilter(win))   # parent=win: живёт вместе с окном
        win.show()
        win._launcher_index = index                # номер фабрики, нужен для перезапуска

        if pos is None:
            self.center_screen(win)                # обычное открытие: по центру
        else:
            win.move(*pos)                         # восстановление: в сохранённую позицию
        win.raise_()
        self.opened.append(win)
        print(f"[ок] {name}", flush=True)

    def _alive_windows(self):
        """Оставляет только видимые окна. Закрытые не занимают место."""
        alive = []
        for w in self.opened:
            try:
                if w.isVisible():
                    alive.append(w)
            except RuntimeError:     # окно уже удалено
                pass
        self.opened = alive
        return alive

    def open_all(self, *_):
        for i in range(len(self.factories)):
            self.open_one(i)

    def close_all(self, *_):
        for win in self.opened:
            try:
                win.close()          # пройдёт через CloseFilter
            except RuntimeError:
                pass                 # окно уже удалено
        self.opened.clear()

    def restart_app(self, *_):
        """Перезапускает лаунчер и восстанавливает открытые окна и их позиции."""
        open_spec = ",".join(
            f"{w._launcher_index}:{w.x()}:{w.y()}" for w in self._alive_windows()
        )
        launcher_pos = f"{self.x()},{self.y()}"
        self.close_all()
        # Флаги собираем явно: --all, --open и --theme из старого запуска не копируем,
        # иначе окна открылись бы дважды
        cmd = [
            sys.executable,
            str(SCRIPT_PATH),
            *self.flags,
            f"--theme={JsonData.theme}",
            f"--open={open_spec}",
            f"--launcher-pos={launcher_pos}",
        ]
        subprocess.Popen(cmd, cwd=str(PROJECT_DIR))
        QApplication.quit()

    def closeEvent(self, event):
        # Крестик лаунчера: закрываем окна и завершаем приложение
        self.close_all()
        super().closeEvent(event)
        QApplication.quit()


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------

def parse_pos(text: str) -> tuple[int, int]:
    x, y = text.split(",")
    return int(x), int(y)


def main() -> int:
    global _LAUNCHER

    parser = argparse.ArgumentParser(description="Отладочный запуск окон с темой")
    parser.add_argument("--all", action="store_true", help="сразу открыть все окна")
    parser.add_argument("--theme", choices=["dark", "light", "auto"], default="auto",
                        help="тема при старте")
    parser.add_argument("--main", action="store_true", help="добавить главное окно (без сканера)")
    parser.add_argument("--geo", action="store_true", help="добавить окна geo_finder.py")
    parser.add_argument("--open", default="",
                        help="окна для открытия при старте: индекс:x:y через запятую")
    parser.add_argument("--launcher-pos", default="", help="позиция лаунчера x,y")
    args = parser.parse_args()

    os.chdir(PROJECT_DIR)    # темы и иконки ищутся относительно папки проекта
    sys.path.insert(0, str(PROJECT_DIR))

    root = make_sandbox()
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    patch_static(root)

    app = QApplication(sys.argv)

    JsonData.theme = args.theme      # до init_app: там вызывается ThemeChanger.init()
    mf = init_app(root)
    items = make_data_items(root)

    flags = [f for f, on in (("--main", args.main), ("--geo", args.geo)) if on]
    factories = build_factories(root, mf, items, args.main, args.geo)

    launcher = Launcher(factories, flags)
    _LAUNCHER = launcher
    if args.launcher_pos:
        launcher.move(*parse_pos(args.launcher_pos))
    else:
        launcher.center_screen(launcher)
        launcher.move(launcher.x(), YY)
    launcher.show()

    if args.all:
        launcher.open_all()
    elif args.open:
        for part in args.open.split(","):
            if part.strip():
                idx, x, y = part.split(":")
                launcher.open_one(int(idx), (int(x), int(y)))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())