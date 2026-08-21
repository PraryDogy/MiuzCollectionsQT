from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from cfg import JsonData, Themes


class UPallete:

    @classmethod
    def light(cls):
        p = QPalette()
        color = QPalette.ColorRole
        p.setColor(color.Window, QColor("#ffffff"))
        p.setColor(color.WindowText, QColor("#000000"))
        p.setColor(color.Base, QColor("#f5f5f5"))
        p.setColor(color.AlternateBase, QColor("#ffffff"))
        p.setColor(color.ToolTipBase, QColor("#ffffff"))   
        p.setColor(color.ToolTipText, QColor("#000000"))   
        p.setColor(color.Text, QColor("#000000"))
        p.setColor(color.Button, QColor("#f0f0f0"))
        p.setColor(color.ButtonText, QColor("#000000"))
        p.setColor(color.BrightText, QColor("#ff0000"))
        p.setColor(color.Link, QColor("#0059d1"))
        p.setColor(color.Highlight, QColor("#0059d1"))
        p.setColor(color.HighlightedText, QColor("#ffffff"))
        # полупрозрачный серый
        p.setColor(color.LinkVisited, QColor("#ffffff"))
        return p

    @classmethod
    def dark(cls):
        p = QPalette()
        color = QPalette.ColorRole


        # основная заливка окон
        p.setColor(color.Window, QColor("#1e1e1e"))
        # цвет текста везде
        p.setColor(color.Text, QColor("#ffffff"))
        # плейсхолдер
        p.setColor(color.PlaceholderText, QColor("#565656"))
        # выделение элементов (синий как в MacOS)
        p.setColor(color.Highlight, QColor("#0059d1"))
        # цвет шрифта подсказок
        p.setColor(color.ToolTipText, QColor("#ffffff"))
        # цвет подсказок
        p.setColor(color.ToolTipBase, QColor("#2a2a2a"))

        # серый для рамки Thumb image widget
        p.setColor(color.LinkVisited, QColor("#4C4C4C"))

        # серый для дополнительного текста Thumb (дата изменения, коллекция)
        p.setColor(color.Midlight, QColor("#818181"))

        # неиспользуемые роли
        # p.setColor(color.WindowText, QColor("#ffffff"))
        # p.setColor(color.Base, QColor("#191919"))
        # p.setColor(color.AlternateBase, QColor("#2a2a2a"))
        # p.setColor(color.Button, QColor("#2d2d2d"))
        # p.setColor(color.ButtonText, QColor("#ffffff"))
        # p.setColor(color.BrightText, QColor("#ff453a"))
        # p.setColor(color.Link, QColor("#0059d1"))
        # p.setColor(color.HighlightedText, QColor("#000000"))
        return p

    @classmethod
    def macinthosh(cls):
        p = QPalette()
        color = p.ColorRole
        p.setColor(color.Highlight, QColor("#0059d1"))
        return p


class ThemeChanger:

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()
        if JsonData.theme == Themes.macos:
            app.setPalette(UPallete.macinthosh())
            app.setStyle("macos")
        elif JsonData.theme == Themes.dark:
            app.setPalette(UPallete.dark())
            app.setStyle("macos")
        elif JsonData.theme == Themes.light:
            app.setPalette(UPallete.light())
            app.setStyle("macos")