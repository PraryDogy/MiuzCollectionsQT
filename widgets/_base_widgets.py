import os

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QContextMenuEvent, QPalette
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame, QHBoxLayout,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QPushButton, QScrollArea,
                             QSpacerItem, QTextEdit, QVBoxLayout, QWidget, QSlider)
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


class UMenuStyle(QMenu):
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
        self.setStyleSheet(
            f"""
                QMenu::separator {{
                    height: 1px;
                    background: {sep_color};
                    margin: 4px 10px;
                }}
            """
        )

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.RightButton:
            a0.ignore()
        else:
            super().mouseReleaseEvent(a0)


class UMenu(UMenuStyle):
    def __init__(self, event: Optional[QContextMenuEvent]):
        super().__init__()
        self.event_ = event

    def show_menu(self):
        if self.event_:
            self.exec_(self.event_.globalPos())
        else:
            self.exec_()


class USubMenu(UMenuStyle):
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


class WindowMixin:
    win_list: list[QMainWindow] = []

    def register_window(self):
        self.win_list.append(self)

    def unregister_window(self):
        try:
            self.win_list.remove(self)
        except ValueError:
            pass

    def center_to_parent(self: QWidget, parent: QWidget):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except Exception as e:
            print("center error:", e)

    def set_always_on_top(self: QWidget):
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def set_close_only(self: QWidget):
        flags = Qt.WindowType.CustomizeWindowHint
        flags |= Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.unregister_window()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.unregister_window()
        return super().deleteLater()


class UMainWindow(WindowMixin, QMainWindow):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.central_layout = UVBoxLayout(central_widget)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.register_window()


class UMainWidget(WindowMixin, QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.central_layout = UVBoxLayout(self)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.register_window()


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


class VListWidgetItem(QListWidgetItem):
    def __init__(self, parent: QListWidget, height: int = 30, text: str | None = None):
        super().__init__(parent)
        self.setSizeHint(QSize(parent.width(), height))
        if text:
            self.setText(text)

    def set_checkable(self):
        self.setFlags(
            self.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        self.setCheckState(
            Qt.CheckState.Unchecked
        )


class VListSpacerItem(QListWidgetItem):
    def __init__(self, parent: QListWidget, height: int = 15):
        super().__init__()
        self.setSizeHint(QSize(parent.width(), height))
        self.setFlags(
            Qt.ItemFlag.NoItemFlags
        )


class VListWidget(QListWidget):
    """QListWidget с вертикальной прокруткой, без горизонтальной."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # --- Отключаем горизонтальную прокрутку ---
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


class SmallBtn(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet("""font-size: 11pt;""")


class HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: rgba(128, 128, 128, 0.2)")
        self.setFixedHeight(1)


class SelectableLabel(QLabel):
    sym_line_feed = "\u000a"
    sym_paragraph_sep = "\u2029"

    def __init__(self, text: str):
        super().__init__(text)
        fl = Qt.TextInteractionFlag.TextSelectableByMouse
        self.setTextInteractionFlags(fl)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        text = self.selectedText()
        text = text.replace(self.sym_paragraph_sep, "")
        text = text.replace(self.sym_line_feed, "")

        full_text = self.text().replace(self.sym_paragraph_sep, "")
        full_text = full_text.replace(self.sym_line_feed, "")

        is_path = any((os.path.isdir(full_text), os.path.isfile(full_text)))

        menu_ = UMenu(event=ev)

        label_text = Lng.copy[Cfg.lng_index]
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: Utils.copy_text(text))
        menu_.addAction(sel)

        reveal = QAction(parent=menu_, text=Lng.reveal_in_finder[Cfg.lng_index])
        reveal.triggered.connect(
            lambda: Utils.reveal_files([full_text])
        )
        
        if is_path:
            menu_.addAction(reveal)

        menu_.show_menu()


class RowArrowWidget(QWidget):
    hh = 35
    clicked = pyqtSignal()
    arrow_svg = "./images/next.svg"
    warning_svg = "./images/warning.svg"
    svg_size = 16

    def __init__(self, text: str):
        super().__init__()
        self.setFixedHeight(self.hh)
        self.main_layout = UVBoxLayout(self)

        self.above_wid = QWidget()
        self.above_layout = UHBoxLayout(self.above_wid)
        self.above_layout.setSpacing(10)

        self.sep = HSep()

        self.text_widget = QLabel(text)

        self.warning_wid = QSvgWidget()
        self.warning_wid.setFixedSize(self.svg_size, self.svg_size)
        self.warning_wid.load(self.warning_svg)
        self.warning_wid.hide()

        self.arrow_wid = QSvgWidget()
        self.arrow_wid.setFixedSize(self.svg_size, self.svg_size)
        self.arrow_wid.load(self.arrow_svg)

        self.main_layout.addWidget(self.above_wid)
        self.main_layout.addWidget(self.sep)

        self.above_layout.addWidget(self.text_widget)
        self.above_layout.addWidget(self.warning_wid)
        self.above_layout.addStretch()
        self.above_layout.addWidget(self.arrow_wid)

    def replace_arrow_widget(self, widget: QWidget):
        self.arrow_wid.hide()
        self.above_layout.addWidget(widget)

    def hide_sep(self):
        self.sep.hide()
        spacer = QSpacerItem(0, self.sep.height())
        self.main_layout.addSpacerItem(spacer)

    def hide_arrow(self):
        self.arrow_wid.hide()

    def show_warning(self):
        self.warning_wid.show()

    def hide_warning(self):
        self.warning_wid.hide()

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mouseReleaseEvent(a0)
    

class USlider(QSlider):
    clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        style = """
            QSlider::groove:horizontal {
                border-radius: 1px;
                height: 3px;
                margin: 0px;
                background-color: rgba(111, 111, 111, 0.5);
            }
            QSlider::handle:horizontal {
                background-color: rgba(199, 199, 199, 1);
                height: 10px;
                width: 10px;
                border-radius: 5px;
                margin: -4px 0;
                padding: -4px 0px;
            }
        """
        self.setStyleSheet(style)
        self.valueChanged.connect(self._on_value_changed)

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            ev.ignore()
            return

        ratio = ev.x() / self.width()
        value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        ev.accept()
        return super().mousePressEvent(ev)

    def wheelEvent(self, e) -> None:
        if e:
            e.ignore()

    def _on_value_changed(self, value: int):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
        self.clicked.emit(value)