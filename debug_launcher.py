"""
debug_launcher.py: отладочный запуск окон проекта с применённой темой.

Запуск из папки проекта (рядом с start.py):
    python debug_launcher.py                  # окно с кнопками
    python debug_launcher.py --all            # сразу открыть все окна
    python debug_launcher.py --theme dark     # тема при старте: dark, light, auto
    python debug_launcher.py --main --geo     # + главное окно и окна GeoFinder

Данные приложения не затрагиваются: используется песочница из preview_windows.py.
Тема меняется кнопками в окне и применяется ко всем открытым окнам сразу,
cfg.json при этом не записывается.
"""
import argparse
import atexit
import importlib
import os
import shutil
import sys
import traceback

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout

import preview_windows as pw
from cfg import JsonData
from system.themes import ThemeChanger
from widgets._base_widgets import (ActiveButton, TransparentLabel,
                                   TransparentWidget, UMainWindow, UPushButton)

THEME_CHOICES = [
    ("Тёмная", "dark"),
    ("Светлая", "light"),
    ("Авто", "auto"),
]

YY = 100

def reload_window_modules() -> None:
    """Перечитывает модули окон из widgets/, чтобы подхватить правки без перезапуска.

    Базовые классы (widgets/_base_widgets.py) и system/* не трогаются: их изменения
    требуют перезапуска debug_launcher.py. Перезапуск быстрый, песочница создаётся заново.
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

    Нужен потому, что часть окон в closeEvent() вызывает event.ignore()
    (ProgressWin, WinMain, WinImgSearch, окна настроек с несохранёнными
    изменениями). Такие окна рассчитывают на владельца, которого в лаунчере нет,
    поэтому крестик и кнопка «закрыть» для них не работали бы.
    Для отладки это допустимо: логика закрытия из closeEvent() здесь не выполняется.
    """

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Close:
            print(f"[закрыто] {obj.windowTitle()}", flush=True)
            obj.hide()
            obj.deleteLater()
            return True          # событие съедено: closeEvent() окна не вызывается
        return False


class Launcher(UMainWindow):
    def __init__(self, factories):
        super().__init__()
        self.setWindowTitle("Отладка: окна проекта")
        self.setMinimumWidth(620)
        self.factories = factories
        self.opened = []          # ссылки на окна, иначе их соберёт сборщик мусора

        self.central_layout.setSpacing(10)
        self.central_layout.addWidget(self._build_theme_row())
        self.central_layout.addWidget(self._build_windows_grid())
        self.central_layout.addWidget(self._build_bottom_row())

        self.status = TransparentLabel("")
        self.status.set_style("gray", "regular", False)
        self.central_layout.addWidget(self.status)
        self.update_status()

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
            col, row = divmod(i, rows)             # сначала заполняем столбец сверху вниз
            btn = UPushButton(name)
            btn.clicked.connect(lambda _=False, idx=i: self.open_one(idx))
            grid.addWidget(btn, row, col)
        return wid

    def _build_bottom_row(self):
        row = TransparentWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)
        close_all = UPushButton("Закрыть все окна")
        close_all.clicked.connect(self.close_all)
        lay.addWidget(close_all)
        lay.addStretch()
        open_all = ActiveButton("Открыть все")
        open_all.clicked.connect(self.open_all)
        lay.addWidget(open_all)
        return row

    # --- действия ---

    def set_theme(self, value: str):
        JsonData.theme = value           # только в памяти, cfg.json не пишется
        ThemeChanger.init()              # применяет стиль ко всему приложению
        self.update_status()

    def update_status(self):
        app = QApplication.instance()
        self.status.setText(
            f"Тема: {JsonData.theme}, стиль приложения: {len(app.styleSheet())} симв."
        )

    def center_screen(self, win) -> None:
        """Центрирует окно на главном экране (та же логика, что в методе center_screen)."""
        screen = QGuiApplication.primaryScreen().geometry()
        size = win.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        win.move(x, y)

    def open_one(self, index: int):
        name, factory = self.factories[index]
        reload_window_modules()              # свежий код окна при каждом открытии
        try:
            win = factory()
        except Exception:
            print(f"[ОШИБКА] {name}\n{traceback.format_exc()}", flush=True)
            self.status.setText(f"Ошибка при открытии: {name}. Смотрите консоль.")
            return

        # UMainWindow по умолчанию модальное: снимаем, чтобы окна не блокировали друг друга
        win.setWindowModality(Qt.WindowModality.NonModal)
        close_filter = CloseFilter(win)      # parent=win: фильтр живёт вместе с окном
        win.installEventFilter(close_filter)

        win.show()
        self.center_screen(win)                   # центрируем после show(): размер окна уже известен
        self.move(self.x(), YY)
        win.raise_()
        self.opened.append(win)
        print(f"[ок] {name}", flush=True)

    def _alive_windows(self):
        """Оставляет только окна, которые ещё видны. Закрытые не занимают место."""
        alive = []
        for w in self.opened:
            try:
                if w.isVisible():
                    alive.append(w)
            except RuntimeError:     # окно уже удалено
                pass
        self.opened = alive
        return alive

    def _next_slot(self) -> tuple[int, int]:
        """Координаты следующего окна: справа от лаунчера, по сетке в пределах экрана."""
        area = QApplication.primaryScreen().availableGeometry()
        step_x, step_y = 380, 320
        left = area.x() + 700                       # правее лаунчера (он у x=40)
        cols = max(1, (area.right() - left) // step_x)
        rows = max(1, (area.bottom() - area.y()) // step_y)
        index = len(self._alive_windows())
        col = index % cols
        row = (index // cols) % rows                # после заполнения экрана начинаем сверху
        return left + col * step_x, area.y() + 40 + row * step_y

    def open_all(self, *_):
        for i in range(len(self.factories)):
            self.open_one(i)

    def close_all(self, *_):
        for win in self.opened:
            try:
                win.close()      # пройдёт через CloseFilter и закроет окно
            except RuntimeError:
                pass             # окно уже удалено
        self.opened.clear()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.close_all()
        return super().keyPressEvent(a0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Отладочный запуск окон с темой")
    parser.add_argument("--all", action="store_true", help="сразу открыть все окна")
    parser.add_argument("--theme", choices=["dark", "light", "auto"], default="auto",
                        help="тема при старте")
    parser.add_argument("--main", action="store_true", help="добавить главное окно (без сканера)")
    parser.add_argument("--geo", action="store_true", help="добавить окна geo_finder.py")
    args = parser.parse_args()

    os.chdir(pw.PROJECT_DIR)   # темы и иконки ищутся относительно папки проекта
    sys.path.insert(0, str(pw.PROJECT_DIR))

    root = pw.make_sandbox()
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    pw.patch_static(root)

    app = QApplication(sys.argv)

    JsonData.theme = args.theme      # выставляем до init_app: там вызывается ThemeChanger.init()
    mf = pw.init_app(root)
    items = pw.make_data_items(root)
    factories = pw.build_factories(root, mf, items, args.main, args.geo)

    launcher = Launcher(factories)
    launcher.center_screen(launcher)
    launcher.move(launcher.x(), YY)
    launcher.show()
    if args.all:
        launcher.open_all()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
