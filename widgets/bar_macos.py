import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QLabel, QMenu, QMenuBar, QSpacerItem

from base_widgets import ContextCustom
from base_widgets.wins import WinChild
from cfg import APP_NAME, APP_VER, Dynamic
from utils.utils import Utils

from .win_settings import WinSettings


class SelectableLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        txt = "\n".join([
            f"Version {APP_VER}",
            "Developed by Evlosh",
            "email: evlosh@gmail.com",
            "telegram: evlosh",
            ])
        
        self.setText(txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = ContextCustom(ev)

        copy_text = QAction(parent=context_menu, text=Dynamic.lng.copy)
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Dynamic.lng.copy_all)
        select_all.triggered.connect(lambda: Utils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_menu()
        return super().contextMenuEvent(ev)

    def copy_text_md(self):
        Utils.copy_text(self.selectedText())


class AboutWin(WinChild):
    def __init__(self):
        super().__init__()

        self.close_btn_cmd(self.close_)
        self.min_btn_disable()
        self.max_btn_disable()
        self.set_titlebar_title(APP_NAME)
        self.setFixedSize(280, 240)

        icon = QSvgWidget(os.path.join("icon", "icon.svg"))
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(150, 130)
        self.content_lay_v.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.content_lay_v.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        self.content_lay_v.addWidget(lbl)

    def close_(self, *args):
        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
            self.close_()


class BarMacos(QMenuBar):
    def __init__(self):
        super().__init__()
        self.settings_win = None
        self.init_ui()

    def init_ui(self):
        self.mainMenu = QMenu(Dynamic.lng.bar_menu, self)

        # Добавляем пункт "Открыть настройки"
        actionSettings = QAction(Dynamic.lng.open_settings_window, self)
        actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(actionSettings)

        # Добавляем пункт "О приложении"
        actionAbout = QAction(Dynamic.lng.show_about, self)
        actionAbout.triggered.connect(self.open_about_window)
        self.mainMenu.addAction(actionAbout)

        # Добавляем меню в MacMenuBar
        self.addMenu(self.mainMenu)

        self.setNativeMenuBar(True)

    def open_settings_window(self):
        self.win_settings = WinSettings(self)
        self.win_settings.center_relative_parent(self)
        self.win_settings.show()

    def open_about_window(self):
        self.about_win = AboutWin()
        self.about_win.center_relative_parent(self)
        self.about_win.show()
