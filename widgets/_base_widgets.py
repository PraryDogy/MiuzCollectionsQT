import os

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QContextMenuEvent, QKeyEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMainWindow, QMenu,
                             QProgressBar, QPushButton, QScrollArea, QSlider,
                             QSpacerItem, QTextEdit, QVBoxLayout, QWidget)
from typing_extensions import Optional

from cfg import JsonData, Static
from system.lang import Lng
from system.utils import Utils


class UMenuStyle(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(
            """
            UMenuStyle {
                border-radius: 0px;
            }
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
            self.exec(self.event_.globalPos())
        else:
            self.exec()


class USubMenu(UMenuStyle):
    def __init__(self, title: str, parent: QMenu):
        super().__init__(title, parent)


class ULineEdit(QLineEdit):
    hh = 30

    def __init__(self):
        super().__init__()
        self.setFixedHeight(self.hh)
        self.setStyleSheet(
            f"""
                padding-left: 2px;
                padding-right: 28px;
            """
        )

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
            (Lng.cut[JsonData.lng_index], self.cut_selection),
            (Lng.copy[JsonData.lng_index], lambda: Utils.copy_text(self.selectedText())),
            (Lng.paste[JsonData.lng_index], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=self.menu_)
            act.triggered.connect(slot)
            self.menu_.addAction(act)

        self.menu_.show_menu()


class UTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()

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
            (Lng.cut[JsonData.lng_index], self.cut_selection),
            (Lng.copy[JsonData.lng_index], self.copy_selection),
            (Lng.paste[JsonData.lng_index], self.paste_text),
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
        self.central_layout = QVBoxLayout(central_widget)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setSpacing(0)
        self.register_window()


class UMainWidget(WindowMixin, QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.central_layout = QVBoxLayout(self)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setSpacing(0)
        self.register_window()


class VScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            """
            VScrollArea { 
                border: none; 
            }
            """
        )


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


class UPushButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(
            """
            font-size: 11pt;
            """
        )
        self.setFixedWidth(80)


class HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
                background: rgba(128, 128, 128, 0.2);
            """
        )
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

        label_text = Lng.copy[JsonData.lng_index]
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: Utils.copy_text(text))
        menu_.addAction(sel)

        reveal = QAction(parent=menu_, text=Lng.reveal_in_finder[JsonData.lng_index])
        reveal.triggered.connect(
            lambda: Utils.reveal_files([full_text])
        )
        
        if is_path:
            menu_.addAction(reveal)

        menu_.show_menu()


class RowArrowWidget(QWidget):
    hh = 35
    clicked = pyqtSignal()
    arrow_svg = os.path.join(Static.internal_icons, "next.svg")
    warning_svg = os.path.join(Static.internal_icons, "warning.svg")
    svg_size = 16

    def __init__(self, text: str):
        super().__init__()
        self.setFixedHeight(self.hh)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.above_wid = QWidget()
        self.above_layout = QHBoxLayout(self.above_wid)
        self.above_layout.setContentsMargins(0, 0, 0, 0)
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
        self.setStyleSheet(
            """
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
        )
        self.valueChanged.connect(self._on_value_changed)

    def mousePressEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            ev.ignore()
            return

        ratio = ev.pos().x() / self.width()
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


class WinProgressbar(UMainWidget):
    cancel = pyqtSignal()
    files_icon_path = os.path.join(Static.internal_icons, "files.svg")
    images_icon_path = os.path.join(Static.internal_icons, "clear.svg")
    ww = 370

    def __init__(self, title: str):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(title)
        self.setFixedWidth(self.ww)

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(0)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_lay = QHBoxLayout(h_wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        left_side_icon = QSvgWidget(self.files_icon_path)
        left_side_icon.setFixedSize(40, 40)
        h_lay.addWidget(left_side_icon)

        right_side_wid = QWidget()
        right_side_lay = QVBoxLayout(right_side_wid)
        right_side_lay.setContentsMargins(0, 0, 0, 0)
        right_side_lay.setSpacing(2)
        h_lay.addWidget(right_side_wid)

        self.above_label = QLabel()
        right_side_lay.addWidget(self.above_label)

        progressbar_row = QWidget()
        right_side_lay.addWidget(progressbar_row)
        progressbar_lay = QHBoxLayout(progressbar_row)
        progressbar_lay.setContentsMargins(0, 0, 0, 0)
        progressbar_lay.setSpacing(10)

        self.progressbar = QProgressBar()
        self.progressbar.setTextVisible(False)
        self.progressbar.setFixedHeight(6)
        progressbar_lay.addWidget(self.progressbar)

        self.cancel_btn = QSvgWidget(self.images_icon_path)
        self.cancel_btn.setFixedSize(15, 15)
        self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
        progressbar_lay.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.below_label = QLabel()
        right_side_lay.addWidget(self.below_label)

        self.adjustSize()

    def cancel_cmd(self, *args):
        self.cancel.emit()
        self.deleteLater()

    def closeEvent(self, a0):
        self.cancel.emit()
        return super().closeEvent(a0)


class GrayLabel(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.font_size_px = 9
        self._update_stylesheet()

    def _update_stylesheet(self):
        self.setStyleSheet(
            f"""
                color: rgba(128, 128, 128, 1.0);
                font-size: {self.font_size_px}px;
            """
        )

    def set_text_size(self, size_px: int = 9):
        self.font_size_px = size_px
        self._update_stylesheet()


class HoverGrayLabel(GrayLabel):
    def __init__(self, text: str):
        super().__init__(text)

    def _update_stylesheet(self):
        self.setStyleSheet(
            f"""
                HoverGrayLabel {{
                    color: rgba(128, 128, 128, 1.0);
                    font-size: {self.font_size_px}px;
                }}
                HoverGrayLabel:hover {{
                    color: rgba(255, 255, 255, 1.0);
                }}
            """
        )

class NewSelectableLabel(SelectableLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setWordWrap(True)
        self.adjustSize()


class ConfirmWindow(UMainWidget):
    ok_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    icon_path = os.path.join(Static.internal_icons, "warning.svg")
    icon_size = 50

    def __init__(self, text: str, w: int, h: int):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.attention[JsonData.lng_index])

        self.central_layout.setContentsMargins(5, 5, 5, 0)
        self.central_layout.setSpacing(0)

        text_container = QWidget()
        # text_container.setStyleSheet("background: red;")
        self.central_layout.addWidget(text_container)

        text_layout = QHBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(15)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(self.icon_path)
        self.svg_widget.setFixedSize(self.icon_size, self.icon_size)
        text_layout.addWidget(self.svg_widget)

        self.text_wid = NewSelectableLabel(text)
        text_layout.addWidget(self.text_wid)

        btn_widget = QWidget()
        self.central_layout.addWidget(btn_widget)

        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        self.ok_btn = UPushButton(Lng.ok[JsonData.lng_index])
        self.ok_btn.setFixedWidth(75)
        self.ok_btn.clicked.connect(self.ok_clicked.emit)
        btn_layout.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
        self.cancel_btn.setFixedWidth(75)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self.cancel_btn.clicked.connect(self.deleteLater)
        btn_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setFixedSize(w, h)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_clicked.emit()
        return super().keyPressEvent(a0)
    

class WarningWindow(ConfirmWindow):
    def __init__(self, text, w, h):
        super().__init__(text, w, h)
        self.cancel_btn.hide()
