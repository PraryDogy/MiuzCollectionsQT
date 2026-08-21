from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from cfg import JsonData, Themes


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
        # только HSep
        p.setColor(color.Mid, QColor("#d4d4d4"))

        # серый для рамки Thumb image widget
        p.setColor(color.LinkVisited, QColor("#e0e0e0"))
        # слабо видимый серый (серый без акцента)
        p.setColor(color.Midlight, QColor("#707070"))

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
        # цвет меню списков QListWidget и подобных
        p.setColor(color.Base, QColor("#191919"))
        # цвет шрифта GroupBox
        p.setColor(color.WindowText, QColor("#ffffff"))
        # цвет шрифта кнопок QPushButton и выпадающего списка QMenu
        p.setColor(color.ButtonText, QColor("#ffffff"))

        # HSep, полоска QSlider
        p.setColor(color.Mid, QColor("#353535"))
        # серый для рамки Thumb image widget
        p.setColor(color.LinkVisited, QColor("#4C4C4C"))
        # слабо видимый серый (серый без акцента)
        # BarTop, PathBar, BarBottom, ползунок QSlider
        p.setColor(color.Midlight, QColor("#818181"))

        return p

    @classmethod
    def macintosh(cls):
        p = QPalette()
        color = p.ColorRole
        p.setColor(color.Highlight, QColor("#0059d1"))
        # серый для рамки Thumb image widget
        p.setColor(color.LinkVisited, QColor("#6D6D6D"))
        # слабо видимый серый (серый без акцента)
        p.setColor(color.Midlight, QColor("#909090"))
        # только HSep
        p.setColor(color.Mid, QColor("#3E3E3E"))

        return p


class ThemeChanger:

    @classmethod
    def init(cls):
        app: QApplication = QApplication.instance()
        if JsonData.theme == Themes.macos:
            app.setPalette(UPallete.macintosh())
            app.setStyle("macos")
        elif JsonData.theme == Themes.dark:
            app.setPalette(UPallete.dark())
            app.setStyle("macos")
        elif JsonData.theme == Themes.light:
            app.setPalette(UPallete.light())
            app.setStyle("macos")