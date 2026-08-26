from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from cfg import JsonData, Static, Themes


class UPallete:

    @classmethod
    def light(cls):
        p = QPalette()
        color = QPalette.ColorRole

        # основная заливка окон (чистый белый)
        p.setColor(color.Window, QColor("#ffffff"))
        # цвет текста везде (чистый черный)
        p.setColor(color.Text, QColor("#000000"))
        # плейсхолдер (светло-серый, стандартный для светлых тем)
        p.setColor(color.PlaceholderText, QColor("#b0b0b0"))
        # выделение элементов (тот же синий для единообразия интерфейса)
        p.setColor(color.Highlight, QColor("#0059d1"))
        # цвет шрифта подсказок
        p.setColor(color.ToolTipText, QColor("#000000"))
        # цвет подсказок
        p.setColor(color.ToolTipBase, QColor("#ffffff"))
        # цвет меню списков QListWidget и подобных
        p.setColor(color.Base, QColor("#f1f0f0"))
        # цвет шрифта GroupBox
        p.setColor(color.WindowText, QColor("#000000"))
        # цвет шрифта кнопок QPushButton и выпадающего списка QMenu
        p.setColor(color.ButtonText, QColor("#000000"))

        # HSep, полоска QSlider
        p.setColor(color.Mid, QColor("#d4d4d4"))
        # серый для рамки Thumb image widget
        p.setColor(color.LinkVisited, QColor("#e0e0e0"))
        # слабо видимый серый (серый без акцента)
        # BarTop, PathBar, BarBottom
        p.setColor(color.Midlight, QColor("#707070"))
        # Кружок QSlider
        p.setColor(color.Link, QColor("#7a7a7a"))

        return p

    @classmethod
    def dark(cls):
        p = QPalette()
        color = QPalette.ColorRole
        p.setColor(color.Window, QColor("#1e1e1e"))
        p.setColor(color.Text, QColor("#ffffff"))
        p.setColor(color.PlaceholderText, QColor("#565656"))
        p.setColor(color.Highlight, QColor("#0059d1"))
        p.setColor(color.ToolTipText, QColor("#ffffff"))
        p.setColor(color.ToolTipBase, QColor("#2a2a2a"))
        p.setColor(color.Base, QColor("#191919"))
        p.setColor(color.WindowText, QColor("#ffffff"))
        p.setColor(color.ButtonText, QColor("#ffffff"))
        p.setColor(color.Mid, QColor("#353535"))
        p.setColor(color.LinkVisited, QColor("#4C4C4C"))
        p.setColor(color.Midlight, QColor("#818181"))
        p.setColor(color.Link, QColor("#A2A2A2"))
        p.setColor(color.Button, QColor("#3E3E3E"))
        p.setColor(color.HighlightedText, QColor("#ffffff"))

       # --- ТЕСТОВЫЕ КРАСНЫЕ РОЛИ ---
        p.setColor(color.AlternateBase, QColor("#727272"))
        p.setColor(color.Dark, QColor("#ff0000"))
        p.setColor(color.Shadow, QColor("#ff0000"))
        p.setColor(color.Light, QColor("#ff0000"))
        p.setColor(color.BrightText, QColor("#ff0000"))

        return p

    def get_palette_text(cls, role: str):
        return f"palette({role})"


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