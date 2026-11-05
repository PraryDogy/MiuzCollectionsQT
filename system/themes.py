from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from cfg import JsonData, Static, Themes
import re


class TreeTheme:
    """Параметры выделения строк дерева.

    sel_color берётся из QSS (UListWidget::item:selected) при загрузке темы.
    """
    sel_color = "#000000"
    sel_text = "#ffffff"
    sel_radius = 8
    h_margin = 4
    v_margin = 1

    _COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
    _SEL_RE = re.compile(
        r"UListWidget::item:selected\b[^{}]*\{\s*background:\s*(#[0-9a-fA-F]{3,8})\s*;\s*\}"
    )

    @classmethod
    def parse_sel_color(cls, qss_text: str) -> str:
        qss_no_comments = cls._COMMENT_RE.sub("", qss_text)
        m = cls._SEL_RE.search(qss_no_comments)
        if not m:
            raise ValueError("TreeTheme: не могу найти цвет UListWidget::item:selected в QSS")
        return m.group(1)

    @classmethod
    def load_from_qss(cls, qss_text: str) -> None:
        cls.sel_color = cls.parse_sel_color(qss_text)

    @classmethod
    def open_dark_qss(cls):
        with open(Static.THEME_DARK_QSS, "r") as file:
            return file.read()

    @classmethod
    def open_light_qss(cls):
        with open(Static.THEME_LIGHT_QSS, "r") as file:
            return file.read()


class DarkTreeTheme(TreeTheme):
    sel_text = "#ffffff"
    sel_radius = 6
    h_margin = 4
    v_margin = 1


class LightTreeTheme(TreeTheme):
    sel_text = "#1a2430"
    sel_radius = 8
    h_margin = 4
    v_margin = 1


class ThemeChanger:
    tree_theme: type[TreeTheme] = DarkTreeTheme  # текущая тема дерева

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
            qss_text = f.read()

        app.setStyleSheet(qss_text)

        tree_theme.load_from_qss(qss_text)
        cls.tree_theme = tree_theme
        cls._repaint_trees()

    @classmethod
    def _repaint_trees(cls):
        from PyQt6.QtWidgets import QTreeWidget
        app: QApplication = QApplication.instance()
        for w in app.allWidgets():
            if isinstance(w, QTreeWidget):
                w.viewport().update()