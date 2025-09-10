import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QLabel, QMenu, QMenuBar, QSpacerItem,
                             QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.utils import MainUtils

from ._base_widgets import SingleActionWindow, UMenu
from .win_settings import WinSettings


class SelectableLabel(QLabel):
    """
    QLabel с возможностью выделения текста и кастомным контекстным меню для копирования.

    Особенности:
        - Текст можно выделять мышью.
        - Контекстное меню позволяет копировать выделенный текст или весь текст.
    """

    INFO_TEXT = "\n".join([
        f"Version {Static.APP_VER}",
        "Developed by Evlosh",
        "email: evlosh@gmail.com",
        "telegram: evlosh",
    ])

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        # --- Текст информации ---
        self.setText(self.INFO_TEXT)

        # --- Настройка взаимодействия с текстом ---
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        """Создаёт кастомное контекстное меню для копирования текста."""
        context_menu = UMenu(ev)

        # --- Копировать выделенный текст ---
        copy_text = QAction(parent=context_menu, text=Lng.copy[Cfg.lng])
        copy_text.triggered.connect(
            lambda: MainUtils.copy_text(self.selectedText())
        )
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        # --- Копировать весь текст ---
        select_all = QAction(parent=context_menu, text=Lng.copy_all[Cfg.lng])
        select_all.triggered.connect(
            lambda: MainUtils.copy_text(self.text())
        )
        context_menu.addAction(select_all)

        # --- Показать контекстное меню ---
        context_menu.show_umenu()


class AboutWin(SingleActionWindow):
    """
    Окно "О программе" с информацией о версии, авторе и контактами.
    
    Особенности:
        - Отображает иконку приложения.
        - Содержит SelectableLabel с информацией, которую можно копировать.
        - Закрывается по Escape или Enter.
    """
    ww, hh = 280, 240
    svg_ww, svg_hh = 150, 130
    svg_icon = "./images/icon.svg"

    def __init__(self):
        super().__init__()

        # --- Настройка окна ---
        self.setWindowTitle(Static.APP_NAME)
        self.setFixedSize(self.ww, self.hh)

        # --- Иконка приложения ---
        icon = QSvgWidget()
        icon.load(self.svg_icon)
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(self.svg_ww, self.svg_hh)
        self.central_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Разделитель ---
        self.central_layout.addSpacerItem(QSpacerItem(0, 20))

        # --- Информационный текст ---
        lbl = SelectableLabel(self)
        self.central_layout.addWidget(lbl)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Закрывает окно по Escape или Enter."""
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
            self.deleteLater()


class BarMacos(QMenuBar):
    """
    Меню-бар для macOS с основными пунктами:
        - Открыть настройки
        - О приложении

    Атрибуты:
        settings_win: экземпляр окна настроек (WinSettings)
        about_win: экземпляр окна "О программе" (AboutWin)
    """

    def __init__(self):
        super().__init__()
        self.mainMenu = QMenu(Lng.menu[Cfg.lng], self)

        # --- Пункт "Открыть настройки" ---
        actionSettings = QAction(Lng.open_settings_window[Cfg.lng], self)
        actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(actionSettings)

        # --- Пункт "О приложении" ---
        actionAbout = QAction(Lng.show_about[Cfg.lng], self)
        actionAbout.triggered.connect(self.open_about_window)
        self.mainMenu.addAction(actionAbout)

        # --- Добавляем меню в меню-бар ---
        self.addMenu(self.mainMenu)
        self.setNativeMenuBar(True)

    def open_settings_window(self):
        """Открывает окно настроек приложения."""
        self.settings_win = WinSettings()
        self.settings_win.center_to_parent(self.window())
        self.settings_win.show()

    def open_about_window(self):
        """Открывает окно 'О программе'."""
        self.about_win = AboutWin()
        self.about_win.center_to_parent(self.window())
        self.about_win.show()
