from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QColor, QContextMenuEvent, QPalette
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QGraphicsDropShadowEffect,
                             QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMainWindow, QMenu, QScrollArea,
                             QTextEdit, QVBoxLayout, QWidget)

from cfg import Cfg, Static
from system.lang import Lng
from system.utils import MainUtils
import re

class UHBoxLayout(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class UVBoxLayout(QVBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class UMenu(QMenu):
    def __init__(self, event: QContextMenuEvent):
        self.ev = event
        super().__init__()

        palette = QApplication.palette()
        text_color = palette.color(QPalette.WindowText).name().lower()

        color_data = {
            "#000000": "#8a8a8a",
            "#ffffff": "#5A5A5A",
        }

        sep_color = color_data.get(text_color)  # дефолт если нет ключа

        self.setStyleSheet(f"""
            QMenu::separator {{
                height: 1px;
                background: {sep_color};
                margin: 4px 10px;
            }}
        """)

    def show_(self):
        self.exec_(self.ev.globalPos())

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.RightButton:
            a0.ignore()
        else:
            super().mouseReleaseEvent(a0)


class ULineEdit(QLineEdit):
    INPUT_H = 28
    LEFT_PADDING = 2
    RIGHT_PADDING = 28

    def __init__(self):
        f"""
        custom context menu
        height 28
        padding left 2
        padding right 28
        """
        super().__init__()
        self.setFixedHeight(self.INPUT_H)
        self.setStyleSheet(
            f"""
            padding-left: {self.LEFT_PADDING};
            padding-right: {self.RIGHT_PADDING};
            """
        )

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
        self.menu_.setFixedWidth(120)

        sel = QAction(text=Lng.cut[Cfg.lng], parent=self.menu_)
        sel.triggered.connect(self.cut_selection)
        self.menu_.addAction(sel)

        sel_all = QAction(text=Lng.copy[Cfg.lng], parent=self.menu_)
        sel_all.triggered.connect(
            lambda: MainUtils.copy_text(self.selectedText())
        )
        self.menu_.addAction(sel_all)

        sel_all = QAction(text=Lng.paste[Cfg.lng], parent=self.menu_)
        sel_all.triggered.connect(self.paste_text)
        self.menu_.addAction(sel_all)

        self.menu_.show_()


class SvgBtn(QWidget):
    def __init__(self, icon_path: str, size: int, parent: QWidget = None):

        self.icon_path = icon_path

        super().__init__(parent=parent)
        self.setStyleSheet(f"""background-color: transparent;""")

        h_layout = UHBoxLayout()
        self.setLayout(h_layout)

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
    def __init__(self, icon_name: str, size: int, shadow_depth: int = 200,
                 parent: QWidget = None):

        super().__init__(icon_name, size, parent)

        effect = QGraphicsDropShadowEffect()
        effect.setOffset(0, 0)
        effect.setColor(QColor(0, 0, 0, shadow_depth))
        effect.setBlurRadius(15)
        self.setGraphicsEffect(effect)


class UTextEdit(QTextEdit):

    def __init__(self):
        """
        custom copy paste context
        """
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

        sel = QAction(text=Lng.cut[Cfg.lng], parent=menu_)
        sel.triggered.connect(self.cut_selection)
        menu_.addAction(sel)

        sel_all = QAction(text=Lng.copy[Cfg.lng], parent=menu_)
        sel_all.triggered.connect(self.copy_selection)
        menu_.addAction(sel_all)

        sel_all = QAction(text=Lng.paste[Cfg.lng], parent=menu_)
        sel_all.triggered.connect(self.paste_text)
        menu_.addAction(sel_all)

        menu_.show_()


class Manager:
    wins: list[QMainWindow] = []


class UMainWindow(QMainWindow):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        self.central_layout = UVBoxLayout()
        central_widget.setLayout(self.central_layout)

        Manager.wins.append(self)

    def center_relative_parent(self, parent: QMainWindow):

        if not isinstance(parent, QMainWindow):
            raise TypeError

        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except (RuntimeError, Exception) as e:
            MainUtils.print_error()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        try:
            Manager.wins.remove(self)
        except Exception as e:
            MainUtils.print_error()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        try:
            Manager.wins.remove(self)
        except Exception as e:
            MainUtils.print_error()
        return super().deleteLater()


class WinSystem(UMainWindow):
    def __init__(self, parent: QWidget = None):
        """
        Окно с пользовательскими флагами отображения:
        - Модальность: блокирует другие окна приложения (ApplicationModal)
        - Заголовок с кнопкой закрытия, остальные кнопки неактивны
        - Внутренние отступы центрального layout'а: (10, 5, 10, 5)
        """
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        fl = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
        fl = fl  | Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(fl)
        self.central_layout.setContentsMargins(10, 5, 10, 5)


class WinChild(UMainWindow):
    def __init__(self, parent: QWidget = None):
        """
        Окно с пользовательскими флагами отображения:
        - Модальность: блокирует другие окна приложения (ApplicationModal)
        """
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)


class UListWidgetItem(QListWidgetItem):
    def __init__(self, parent: QListWidget, height: int = 30, text: str = None):
        """
        - height: 30
        - width: parent (QListWidget) width
        """
        super().__init__()
        self.setSizeHint(QSize(parent.width(), height))
        if text:
            self.setText(text)


class UListSpacerItem(QListWidgetItem):
    def __init__(self, parent: QListWidget, height: int = 15):
        super().__init__()
        self.setSizeHint(QSize(parent.width(), height))
        self.setFlags(Qt.ItemFlag.NoItemFlags)


class VScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; }")


class VListWidget(QListWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
