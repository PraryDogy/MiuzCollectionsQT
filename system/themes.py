from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from cfg import JsonData, Static, Themes


class TreeTheme:
    """Базовый класс: параметры выделения строк дерева.

    Синхронизировано с QSS: sel_color = UListWidget::item:selected,
    sel_text = UListWidget::item color. При смене цветов в QSS
    обновите этот файл вручную.
    """
    sel_color = "#000000"
    sel_text = "#ffffff"
    sel_radius = 8
    h_margin = 4
    v_margin = 1


class DarkTreeTheme(TreeTheme):
    # dark.qss: UListWidget::item:selected, UMenu::item:selected
    sel_color = "#1d2833"
    sel_text = "#ffffff"
    sel_radius = 8
    h_margin = 4
    v_margin = 1


class LightTreeTheme(TreeTheme):
    # light.qss: UListWidget::item:selected, UMenu::item:selected
    sel_color = "#e3eaf2"
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
            app.setStyleSheet(f.read())

        cls.tree_theme = tree_theme
        cls._repaint_trees()

    @classmethod
    def _repaint_trees(cls):
        from PyQt6.QtWidgets import QTreeWidget
        app: QApplication = QApplication.instance()
        for w in app.allWidgets():
            if isinstance(w, QTreeWidget):
                w.viewport().update()