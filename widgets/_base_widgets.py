from dataclasses import dataclass

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QColor, QContextMenuEvent, QPalette
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QPushButton, QScrollArea,
                             QTextEdit, QVBoxLayout, QWidget)
from typing_extensions import Literal, Optional

from cfg import Static, cfg
from system.lang import Lng
from system.main_folder import Mf
from system.utils import Utils


class UHBoxLayout(QHBoxLayout):
    """QHBoxLayout с нулевыми отступами и нулевым расстоянием между виджетами."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class UVBoxLayout(QVBoxLayout):
    """QVBoxLayout с нулевыми отступами и нулевым расстоянием между виджетами."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class UMenuBase(QMenu):
    """
    Базовый QMenu с кастомной окраской разделителей, подстроенной под цвет текста приложения.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- палитра ---
        palette = QApplication.palette()
        text_color = palette.color(QPalette.WindowText).name().lower()

        # --- соответствие цвета текста и разделителя ---
        color_data = {
            "#000000": "#8a8a8a",
            "#ffffff": "#5a5a5a",
        }
        sep_color = color_data.get(text_color, "#8a8a8a")  # дефолт

        # --- стили ---
        self.setStyleSheet(f"""
            QMenu::separator {{
                height: 1px;
                background: {sep_color};
                margin: 4px 10px;
            }}
        """)

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.RightButton:
            a0.ignore()
        else:
            super().mouseReleaseEvent(a0)


class UMenu(UMenuBase):
    """
    Контекстное меню для главного окна.
    
    Аргументы:
        event (QContextMenuEvent): Событие контекстного меню.
    """

    def __init__(self, event: QContextMenuEvent):
        super().__init__()
        self.ev = event

    def show_umenu(self):
        self.exec_(self.ev.globalPos())


class USubMenu(UMenuBase):
    """
    Подменю с тем же стилем, что и UMenu.
    """

    def __init__(self, title: str, parent: QMenu):
        super().__init__(title, parent)


class ULineEdit(QLineEdit):
    """
    QLineEdit с фиксированной высотой, кастомными отступами и шириной контекстного меню.
    
    Атрибуты:
        hh (int): высота виджета.
        padding (tuple[int, int]): отступы слева и справа.
        menu_width (int): ширина контекстного меню.
    """
    hh = 30
    padding = (2, 28)
    menu_width = 120

    def __init__(self):
        super().__init__()

        self.setFixedHeight(self.hh)
        self.setStyleSheet(f"""
            padding-left: {self.padding[0]}px;
            padding-right: {self.padding[1]}px;
        """)

    def cut_selection(self, *args):
        text = self.selectedText()
        Utils.copy_text(text)

        new_text = self.text().replace(text, "")
        self.setText(new_text)

    def paste_text(self, *args):
        text = Utils.paste_text()
        self.insert(text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.menu_ = UMenu(event=a0)
        self.menu_.setFixedWidth(self.menu_width)

        actions = [
            (Lng.cut[cfg.lng], self.cut_selection),
            (Lng.copy[cfg.lng], lambda: Utils.copy_text(self.selectedText())),
            (Lng.paste[cfg.lng], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=self.menu_)
            act.triggered.connect(slot)
            self.menu_.addAction(act)

        self.menu_.show_umenu()


class USvgSqareWidget(QSvgWidget):
    def __init__(self, src: str, size: int):
        """
        Квадратный Svg виджет
        """
        super().__init__()
        self.setStyleSheet(f"""background-color: transparent;""")
        self.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.setFixedSize(size, size)
        if src:
            self.load(src)


class UTextEdit(QTextEdit):
    """QTextEdit с кастомным контекстным меню для копирования/вставки"""

    def __init__(self):
        super().__init__()

    def copy_selection(self):
        cur = self.parent_.textCursor()
        text = cur.selectedText().strip()
        Utils.copy_text(text)

    def cut_selection(self):
        cur = self.textCursor()
        text = cur.selectedText().strip()
        Utils.copy_text(text)
        cur.removeSelectedText()

    def paste_text(self):
        text = Utils.paste_text()
        new_text = self.toPlainText() + text
        self.setPlainText(new_text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        menu_ = UMenu(event=a0)
        menu_.setFixedWidth(120)

        actions = [
            (Lng.cut[cfg.lng], self.cut_selection),
            (Lng.copy[cfg.lng], self.copy_selection),
            (Lng.paste[cfg.lng], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=menu_)
            act.triggered.connect(slot)
            menu_.addAction(act)

        menu_.show_umenu()


class WinManager:
    win_list: list[QMainWindow] = []


class UMainWindow(QMainWindow):
    """
    Базовое главное окно приложения с центральным виджетом и вертикальным layout.

    Атрибуты:
        central_layout (QVBoxLayout): вертикальный layout центрального виджета.
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # --- Центральный виджет ---
        central_widget = QWidget(self)
        central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        # --- Компоновка ---
        self.central_layout = UVBoxLayout(central_widget)

        # --- Регистрация окна в менеджере ---
        WinManager.win_list.append(self)

    def center_to_parent(self, parent: QMainWindow):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except Exception as e:
            print("base widgets, u main window, center error", e)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        try:
            WinManager.win_list.remove(self)
        except Exception as e:
            Utils.print_error()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        try:
            WinManager.win_list.remove(self)
        except ValueError as e:
            # Utils.print_error()
            print("remove win from list err", e)
        return super().deleteLater()


class SingleActionWindow(UMainWindow):
    """
    Окно с пользовательскими флагами отображения:
    - Модальность: блокирует другие окна приложения (ApplicationModal)
    - Заголовок с кнопкой закрытия, остальные кнопки неактивны
    - Внутренние отступы центрального layout'а: (10, 5, 10, 5)
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # --- Модальность окна ---
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # --- Флаги окна: только кнопка закрытия ---
        flags = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
        flags |= Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)

        # --- Отступы центрального layout'а ---
        self.central_layout.setContentsMargins(10, 5, 10, 5)


class AppModalWindow(UMainWindow):
    def __init__(self, parent: QWidget = None):
        """
        Окно с пользовательскими флагами отображения:
        - Модальность: блокирует другие окна приложения (ApplicationModal)
        """

        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)


class UListWidgetItem(QListWidgetItem):
    """
    QListWidgetItem с фиксированной высотой и шириной, совпадающей с родителем.
    """

    def __init__(self, parent: QListWidget, height: int = 30, text: str | None = None):
        super().__init__(parent)

        # фиксированный размер
        self.setSizeHint(QSize(parent.width(), height))

        # текст, если указан
        if text:
            self.setText(text)


class UListSpacerItem(QListWidgetItem):
    """
    Пустой элемент списка QListWidget, используемый как разделитель/отступ.

    Аргументы:
        parent (QListWidget): родительский список.
        height (int, optional): высота элемента. По умолчанию 15.
    """


    def __init__(self, parent: QListWidget, height: int = 15):
        super().__init__()
        self.setSizeHint(QSize(parent.width(), height))
        self.setFlags(Qt.ItemFlag.NoItemFlags)


class VScrollArea(QScrollArea):
    """QScrollArea с вертикальной прокруткой, без горизонтальной и без границ."""

    def __init__(self):
        super().__init__()

        # --- Настройка области прокрутки ---
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)

        # --- Вертикальная прокрутка только ---
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # --- Убираем границы ---
        self.setStyleSheet("QScrollArea { border: none; }")


class VListWidget(QListWidget):
    """QListWidget с вертикальной прокруткой, без горизонтальной."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # --- Отключаем горизонтальную прокрутку ---
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


@dataclass(slots=True)
class Buffer:
    type_: Literal["cut", "copy"]

    src_dirs: Optional[list[str]]
    src_mf: Optional[Mf]
    src_files: Optional[list[str]]

    dst_dir: Optional[str]
    dst_mf: Optional[Mf]
    dst_files: Optional[list[str]]
   

class NotifyWid(QFrame):
    blue = "rgb(70, 130, 240)"
    yy = 10

    def __init__(self, parent: QWidget, text: str, svg_path: str, ms: int = 2000):
        super().__init__(parent=parent)

        self.ms = ms
        self.setStyleSheet(
            f"""
                background: {self.blue};
                border-radius: 10px;
                font-size: 14px;
                color: black;
            """
        )

        # иконка
        self.icon = QSvgWidget(svg_path, self)
        self.icon.setFixedSize(20, 20)

        # текст
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # лейаут
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addWidget(self.icon)
        layout.addWidget(self.label)

        # тень
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        self.adjustSize()

    def _show(self):
        self.adjustSize()
        pw, ph = self.parent().width(), self.parent().height()
        x = (pw - self.width()) // 2
        y = self.yy
        self.move(x, y)
        self.show()
        QTimer.singleShot(self.ms, self._close)

    def _close(self):
        self.setGraphicsEffect(None)
        self.hide()
        self.deleteLater()


class SmallBtn(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet("""
        font-size: 11pt;
        """)