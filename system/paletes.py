from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from cfg import Cfg


class UPallete:

    @classmethod
    def light(cls):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
        p.setColor(QPalette.ColorRole.Base, QColor("#f5f5f5"))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))   # фон тултипа светлый
        p.setColor(QPalette.ColorRole.ToolTipText, QColor("#000000"))   # текст тултипа тёмный
        p.setColor(QPalette.ColorRole.Text, QColor("#000000"))
        p.setColor(QPalette.ColorRole.Button, QColor("#f0f0f0"))
        p.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
        p.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
        p.setColor(QPalette.ColorRole.Link, QColor("#007aff"))
        p.setColor(QPalette.ColorRole.Highlight, QColor("#007aff"))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        return p

    @classmethod
    def dark(cls):
        p = QPalette()
        p.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
        p.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.Base, QColor("#191919"))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2a2a"))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2a2a2a"))   # фон тултипа тёмный
        p.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))   # текст тултипа светлый
        p.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.Button, QColor("#2d2d2d"))
        p.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.BrightText, QColor("#ff453a"))
        p.setColor(QPalette.ColorRole.Link, QColor("#0a84ff"))
        p.setColor(QPalette.ColorRole.Highlight, QColor("#0a84ff"))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
        return p


class ThemeChanger:

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()
        if Cfg.dark_mode == 0:
            app.setPalette(QPalette())
            app.setStyle("macos")
        elif Cfg.dark_mode == 1:
            app.setPalette(UPallete.dark())
            app.setStyle("Fusion")
        elif Cfg.dark_mode == 2:
            app.setPalette(UPallete.light())
            app.setStyle("Fusion")