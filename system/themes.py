# system/themes.py
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTreeWidget

from cfg import JsonData, Static, Themes


class TreeTheme:
    """Параметры выделения строк дерева и списков.

    Значения должны совпадать с UListWidget::item:selected в QSS.
    """
    sel_color = "#000000"
    sel_text = "#ffffff"
    sel_radius = 8
    h_margin = 4
    v_margin = 1

    @classmethod
    def open_dark_qss(cls):
        with open(Static.THEME_DARK_QSS, "r", encoding="utf-8") as file:
            return file.read()

    @classmethod
    def open_light_qss(cls):
        with open(Static.THEME_LIGHT_QSS, "r", encoding="utf-8") as file:
            return file.read()


class DarkTreeTheme(TreeTheme):
    sel_color = "#1d2833"   # UListWidget::item:selected в dark.qss
    sel_text = "#ffffff"
    sel_radius = 6          # border-radius у UListWidget::item:selected
    h_margin = 4
    v_margin = 1


class LightTreeTheme(TreeTheme):
    sel_color = "#000000"   # TODO: взять из UListWidget::item:selected в light.qss
    sel_text = "#1a2430"
    sel_radius = 8
    h_margin = 4
    v_margin = 1


class ThemeChanger:
    tree_theme: type[TreeTheme] = DarkTreeTheme

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()

        try:
            app.styleHints().colorSchemeChanged.disconnect(cls._on_system_theme_changed)
        except TypeError:
            pass

        if JsonData.theme == Themes.theme_auto:
            app.styleHints().colorSchemeChanged.connect(cls._on_system_theme_changed)
            cls._apply_system_theme()

        elif JsonData.theme == Themes.theme_dark:
            cls._apply_theme(Static.THEME_DARK_QSS, DarkTreeTheme)

        elif JsonData.theme == Themes.theme_light:
            cls._apply_theme(Static.THEME_LIGHT_QSS, LightTreeTheme)

    @classmethod
    def _on_system_theme_changed(cls):
        cls._apply_system_theme()

    @classmethod
    def _apply_system_theme(cls):
        app: QApplication = QApplication.instance()

        if app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            cls._apply_theme(Static.THEME_DARK_QSS, DarkTreeTheme)
        else:
            cls._apply_theme(Static.THEME_LIGHT_QSS, LightTreeTheme)

    @classmethod
    def _apply_theme(cls, qss_path, tree_theme):
        app: QApplication = QApplication.instance()

        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

        cls.tree_theme = tree_theme
        cls._repaint_trees()

    @classmethod
    def _repaint_trees(cls):
        app: QApplication = QApplication.instance()
        for w in app.allWidgets():
            if isinstance(w, QTreeWidget):
                w.viewport().update()