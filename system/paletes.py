from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from cfg import JsonData, Static, Themes


class ThemeChanger:

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()

        # На всякий случай отключаем предыдущий обработчик
        try:
            app.styleHints().colorSchemeChanged.disconnect(cls._on_system_theme_changed)
        except TypeError:
            pass

        if JsonData.theme == Themes.auto:
            app.styleHints().colorSchemeChanged.connect(
                cls._on_system_theme_changed
            )
            cls._apply_system_theme()

        elif JsonData.theme == Themes.dark:
            cls._apply_theme(Static.THEMES_DARK)

        elif JsonData.theme == Themes.light:
            cls._apply_theme(Static.THEMES_LIGHT)

    @classmethod
    def _on_system_theme_changed(cls):
        cls._apply_system_theme()

    @classmethod
    def _apply_system_theme(cls):
        app: QApplication = QApplication.instance()

        if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            cls._apply_theme(Static.THEMES_DARK)
        else:
            cls._apply_theme(Static.THEMES_LIGHT)

    @classmethod
    def _apply_theme(cls, path):
        app: QApplication = QApplication.instance()

        with open(path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())