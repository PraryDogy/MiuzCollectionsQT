from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from cfg import Cfg, Themes


class UPallete:

    @classmethod
    def light(cls):
        p = QPalette()
        p.setColor(QPalette.Window, QColor("#ffffff"))
        p.setColor(QPalette.WindowText, QColor("#000000"))
        p.setColor(QPalette.Base, QColor("#f5f5f5"))
        p.setColor(QPalette.AlternateBase, QColor("#ffffff"))
        p.setColor(QPalette.ToolTipBase, QColor("#ffffff"))   # фон тултипа светлый
        p.setColor(QPalette.ToolTipText, QColor("#000000"))   # текст тултипа тёмный
        p.setColor(QPalette.Text, QColor("#000000"))
        p.setColor(QPalette.Button, QColor("#f0f0f0"))
        p.setColor(QPalette.ButtonText, QColor("#000000"))
        p.setColor(QPalette.BrightText, QColor("#ff0000"))
        p.setColor(QPalette.Link, QColor("#0059d1"))
        p.setColor(QPalette.Highlight, QColor("#0059d1"))
        p.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        return p

    @classmethod
    def dark(cls):
        p = QPalette()
        p.setColor(QPalette.Window, QColor("#1e1e1e"))
        p.setColor(QPalette.WindowText, QColor("#ffffff"))
        p.setColor(QPalette.Base, QColor("#191919"))
        p.setColor(QPalette.AlternateBase, QColor("#2a2a2a"))
        p.setColor(QPalette.ToolTipBase, QColor("#2a2a2a"))   # фон тултипа тёмный
        p.setColor(QPalette.ToolTipText, QColor("#ffffff"))   # текст тултипа светлый
        p.setColor(QPalette.Text, QColor("#ffffff"))
        p.setColor(QPalette.Button, QColor("#2d2d2d"))
        p.setColor(QPalette.ButtonText, QColor("#ffffff"))
        p.setColor(QPalette.BrightText, QColor("#ff453a"))
        p.setColor(QPalette.Link, QColor("#0059d1"))
        p.setColor(QPalette.Highlight, QColor("#0059d1"))
        p.setColor(QPalette.HighlightedText, QColor("#000000"))
        return p

    @classmethod
    def macinthosh(cls):
        p = QPalette()
        p.setColor(QPalette.Highlight, QColor("#0059d1"))
        return p
        
        # 1. Основной фон окон и текст на нем
        p.setColor(QPalette.Window, QColor("#393D44"))         # Темно-серый фон окна
        p.setColor(QPalette.WindowText, QColor("#FFFFFF"))     # Белый текст на окне
        
        # 2. Поля ввода (QLineEdit) и списки (QListWidget)
        p.setColor(QPalette.Base, QColor("#2A2D33"))           # Фон для полей и списков (чуть темнее окон)
        p.setColor(QPalette.Text, QColor("#FFFFFF"))           # Белый текст внутри полей и списков
        
        # 3. Кнопки и текст на них
        p.setColor(QPalette.Button, QColor("#534F55"))         # Фон кнопок
        p.setColor(QPalette.ButtonText, QColor("#FFFFFF"))     # Белый шрифт кнопок
        
        # 4. Выделение текста и элементов списка
        p.setColor(QPalette.Highlight, QColor("#007AFF"))      # Цвет выделения (акцентный синий)
        p.setColor(QPalette.HighlightedText, QColor("#FFFFFF")) # Цвет текста при выделении
        
        # 5. Вспомогательный текст (подсказки / placeholder)
        p.setColor(QPalette.PlaceholderText, QColor("#8E8E93")) # Серый цвет для подсказок ввода

        p.setColor(QPalette.Inactive, QPalette.Highlight, QColor("#55555A"))     
        p.setColor(QPalette.Inactive, QPalette.HighlightedText, QColor("#FFFFFF"))
        
        return p


class ThemeChanger:

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()
        if Cfg.theme == Themes.macintosh:
            app.setPalette(UPallete.macinthosh())
            app.setStyle("macintosh")
        elif Cfg.theme == Themes.dark:
            app.setPalette(UPallete.dark())
            app.setStyle("macintosh")
        elif Cfg.theme == Themes.light:
            app.setPalette(UPallete.light())
            app.setStyle("macintosh")