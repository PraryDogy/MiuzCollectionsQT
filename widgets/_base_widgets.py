from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QColor, QContextMenuEvent, QPalette
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QScrollArea, QTextEdit,
                             QVBoxLayout, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.main_folder import MainFolder
from system.utils import MainUtils


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
    hh = 28
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
        MainUtils.copy_text(text)

        new_text = self.text().replace(text, "")
        self.setText(new_text)

    def paste_text(self, *args):
        text = MainUtils.paste_text()
        self.insert(text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        self.menu_ = UMenu(event=a0)
        self.menu_.setFixedWidth(self.menu_width)

        actions = [
            (Lng.cut[Cfg.lng], self.cut_selection),
            (Lng.copy[Cfg.lng], lambda: MainUtils.copy_text(self.selectedText())),
            (Lng.paste[Cfg.lng], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=self.menu_)
            act.triggered.connect(slot)
            self.menu_.addAction(act)

        self.menu_.show_umenu()


class SvgBtn(QWidget):
    """
    Виджет кнопки с SVG-иконкой.

    Аргументы:
        icon_path (str): путь к SVG-файлу.
        size (int): размер кнопки (ширина и высота).
        parent (QWidget, optional): родительский виджет.
    """

    def __init__(self, icon_path: str, size: int, parent: QWidget = None):
        super().__init__(parent)

        self.icon_path = icon_path
        self.setStyleSheet("background-color: transparent;")

        h_layout = UHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        self.svg_btn = QSvgWidget()
        self.svg_btn.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.svg_btn.setFixedSize(size, size)
        self.set_icon(icon_path)

        h_layout.addWidget(self.svg_btn)
        self.adjustSize()

    def set_icon(self, icon_path):
        self.svg_btn.load(icon_path)

    def get_icon_path(self):
        return self.icon_path


class SvgShadowed(SvgBtn):
    """
    Виджет кнопки с SVG-иконкой и тенью.

    Аргументы:
        icon_name (str): путь к SVG-файлу.
        size (int): размер кнопки (ширина и высота).
        shadow_depth (int, optional): прозрачность тени (0–255). По умолчанию 200.
        parent (QWidget, optional): родительский виджет.
    """

    def __init__(self, icon_name: str, size: int, shadow_depth: int = 200,
                 parent: QWidget = None):
        super().__init__(icon_name, size, parent)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, shadow_depth))
        shadow.setBlurRadius(15)
        self.setGraphicsEffect(shadow)


class UTextEdit(QTextEdit):
    """QTextEdit с кастомным контекстным меню для копирования/вставки"""

    def __init__(self):
        super().__init__()

    def copy_selection(self):
        cur = self.parent_.textCursor()
        text = cur.selectedText().strip()
        MainUtils.copy_text(text)

    def cut_selection(self):
        cur = self.textCursor()
        text = cur.selectedText().strip()
        MainUtils.copy_text(text)
        cur.removeSelectedText()

    def paste_text(self):
        text = MainUtils.paste_text()
        new_text = self.toPlainText() + text
        self.setPlainText(new_text)

    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        menu_ = UMenu(event=a0)
        menu_.setFixedWidth(120)

        actions = [
            (Lng.cut[Cfg.lng], self.cut_selection),
            (Lng.copy[Cfg.lng], self.copy_selection),
            (Lng.paste[Cfg.lng], self.paste_text),
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
            MainUtils.print_error()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        try:
            WinManager.win_list.remove(self)
        except Exception as e:
            MainUtils.print_error()
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


class SettingsItem:
    type_general = "general"
    type_filters = "filters"
    type_new_folder = "new_folder"
    type_edit_folder = "edit_folder"

    def __init__(self):
        self.action_type: str
        self.content: None | str | MainFolder


class ClipBoardItem:
    type_cut = "cut"
    type_copy = "copy"
    
    def __init__(self):
        self.action_type: str

        self.source_dirs: list[str]
        self.source_main_folder: MainFolder
        self.files_to_copy: list[str]

        self.target_dir: str
        self.target_main_folder: MainFolder
        self.files_copied: list[str]
   
    def set_files_copied(self, files: list[str]):
        self.files_copied = files


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