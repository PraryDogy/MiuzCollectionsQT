from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from cfg import Cfg


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
        p.setColor(QPalette.Link, QColor("#007aff"))
        p.setColor(QPalette.Highlight, QColor("#007aff"))
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
        p.setColor(QPalette.Link, QColor("#0a84ff"))
        p.setColor(QPalette.Highlight, QColor("#0a84ff"))
        p.setColor(QPalette.HighlightedText, QColor("#000000"))
        return p


class ThemeChanger:

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()
        if Cfg.dark_mode == 0:
            app.setPalette(QPalette())
            app.setStyle("macintosh")
        elif Cfg.dark_mode == 1:
            app.setPalette(UPallete.dark())
            app.setStyle("Fusion")
        elif Cfg.dark_mode == 2:
            app.setPalette(UPallete.light())
            app.setStyle("Fusion")