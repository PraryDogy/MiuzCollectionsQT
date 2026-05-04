from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QColor, QContextMenuEvent, QPalette
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QPushButton, QScrollArea,
                             QTextEdit, QVBoxLayout, QWidget)
from typing_extensions import Optional

from cfg import Cfg
from system.lang import Lng
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
        text_color = palette.color(QPalette.ColorRole.WindowText).name().lower()

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

    def __init__(self, event: Optional[QContextMenuEvent]):
        super().__init__()
        self.event_ = event

    def show_menu(self):
        if self.event_:
            self.exec_(self.event_.globalPos())
        else:
            self.exec_()


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
    menu_width = 200

    def __init__(self):
        super().__init__()

        self.setFixedHeight(self.hh)
        style = f"""
            padding-left: {self.padding[0]}px;
            padding-right: {self.padding[1]}px;
        """
        # border-radius: 6px;
        self.setStyleSheet(self.styleSheet() + style)

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
            (Lng.cut[Cfg.lng_index], self.cut_selection),
            (Lng.copy[Cfg.lng_index], lambda: Utils.copy_text(self.selectedText())),
            (Lng.paste[Cfg.lng_index], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=self.menu_)
            act.triggered.connect(slot)
            self.menu_.addAction(act)

        self.menu_.show_menu()


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
        # background-color: palette(base);

    def copy_selection(self):
        cur = self.textCursor()
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
            (Lng.cut[Cfg.lng_index], self.cut_selection),
            (Lng.copy[Cfg.lng_index], self.copy_selection),
            (Lng.paste[Cfg.lng_index], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=menu_)
            act.triggered.connect(slot)
            menu_.addAction(act)

        menu_.show_menu()


class WinManager:
    win_list: list[QMainWindow] = []


class WindowMixin:
    def register_window(self):
        WinManager.win_list.append(self)

    def unregister_window(self):
        try:
            WinManager.win_list.remove(self)
        except ValueError:
            pass

    def center_to_parent(self, parent: QWidget):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except Exception as e:
            print("center error:", e)


class UMainWindow(QMainWindow, WindowMixin):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        central_widget = QWidget(self)
        central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)
        self.central_layout = UVBoxLayout(central_widget)
        self.register_window()

    def set_always_on_top(self):
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def set_close_only(self):
        flags = Qt.WindowType.CustomizeWindowHint
        flags |= Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.unregister_window()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.unregister_window()
        return super().deleteLater()


class UListWidgetItem(QListWidgetItem):
    def __init__(self, parent: QListWidget, height: int = 30, text: str | None = None):
        super().__init__(parent)
        self.setSizeHint(QSize(parent.width(), height))
        if text:
            self.setText(text)


class UListSpacerItem(QListWidgetItem):
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
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

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

        # self.setFixedHeight(20)
        self.setStyleSheet("""
        font-size: 11pt;
        """)


class HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: rgba(128, 128, 128, 0.2)")
        self.setFixedHeight(1)