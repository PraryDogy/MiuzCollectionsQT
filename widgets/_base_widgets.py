import os
import re

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QContextMenuEvent, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QFileDialog, QFrame, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QProgressBar, QPushButton,
                             QScrollArea, QSlider, QSpacerItem, QSpinBox,
                             QStackedWidget, QTextEdit, QTreeWidget,
                             QVBoxLayout, QWidget)
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
                border: 1px solid palette(button);
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

        self.setStyleSheet(
            f"""
                border: 1px solid palette(button);
            """
        )

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


class UGroupBox(QGroupBox):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setStyleSheet(
            """
            QGroupBox {
                background-color: palette(tooltip-base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                margin-top: 12px; 
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
            }
            """
        )

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
    icon_size = 16

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setIconSize(QSize(self.icon_size, self.icon_size))


class UTreeWidget(QTreeWidget):
    icon_size = 16
    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(self.icon_size, self.icon_size))


class UPushButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setFixedHeight(20)
        self.setStyleSheet(
            """
            font-size: 11pt;
            background: palette(button);
            border: 1px solid palette(link-visited);
            border-radius: 4px;
            """
        )
        self.setFixedWidth(80)


class HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
                background: palette(mid);
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
    clicked = pyqtSignal()
    arrow_svg = os.path.join(Static.common_icons, "next.svg")
    warning_svg = os.path.join(Static.common_icons, "yellow_warning.svg")
    hh = 26
    svg_size = 16

    # обычно эти виджеты помещаются в QGroupBox
    # Это правильные отступы чтобы все красиво смотрелось
    group_margings = (5, 3, 5, 3)
    group_spacing = 5

    def __init__(self, text: str):
        super().__init__()
        self.setFixedHeight(self.hh)
        
        # Один прямой горизонтальный слой
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # Иконка слева
        self.left_icon = QSvgWidget()
        self.left_icon.setFixedSize(self.svg_size, self.svg_size)
        self.left_icon.hide()
        
        # Текст
        self.text_widget = QLabel(text)
        
        # Стрелка справа
        self.arrow_wid = QSvgWidget()
        self.arrow_wid.setFixedSize(self.svg_size, self.svg_size)
        self.arrow_wid.load(self.arrow_svg)
        
        # Сборка в один ряд
        self.main_layout.addWidget(self.left_icon)
        self.main_layout.addWidget(self.text_widget)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.arrow_wid)
        
        self.adjustSize()

    def set_left_icon(self, svg_path: str):
        self.left_icon.load(svg_path)
        self.left_icon.show()

    def replace_arrow_widget(self, widget: QWidget):
        self.arrow_wid.hide()
        self.main_layout.addWidget(widget)

    def hide_arrow(self):
        self.arrow_wid.hide()

    def show_warning(self):
        self.set_left_icon(self.warning_svg)

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
                    background-color: palette(mid);
                }
                QSlider::handle:horizontal {
                    background-color: palette(link);
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


class USpinBox(QSpinBox):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setFixedHeight(26)
        self.setStyleSheet(
            """
            QSpinBox {
                background: palette(button);
                color: palette(text);
                border: 1px solid palette(link-visited);
                border-radius: 4px;
            }

            QSpinBox::up-button {
                width: 17px;
                height: 10px;
                background: palette(link-visited);
                margin-top: 2px;
                margin-right: 2px;
                
                /* Закругляем только верхние углы */
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }

            QSpinBox::down-button {
                width: 17px;
                height: 10px;
                background: palette(link-visited);
                margin-bottom: 2px;
                margin-right: 2px;
                
                /* Закругляем только нижние углы */
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QSpinBox::up-arrow {
                image: url("icons/common/arrow_up.svg");
                width: 9px;
                height: 9px;
            }

            QSpinBox::down-arrow {
                image: url("icons/common/arrow_down.svg");
                width: 9px;
                height: 9px;
            }
            """
        )






class WinProgressbar(UMainWidget):
    cancel = pyqtSignal()
    files_icon_path = os.path.join(Static.common_icons, "copy_files.svg")
    images_icon_path = os.path.join(Static.common_icons, "cancel.svg")
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
        left_side_icon.setFixedSize(50, 50)
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
        progressbar_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progressbar = QProgressBar()
        self.progressbar.setTextVisible(False)
        self.progressbar.setFixedHeight(6)
        self.progressbar.adjustSize()
        progressbar_lay.addWidget(self.progressbar)

        self.cancel_btn = QSvgWidget(self.images_icon_path)
        self.cancel_btn.setFixedSize(13, 13)
        self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
        progressbar_lay.addWidget(self.cancel_btn)

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
                color: palette(midlight);
                font-size: {self.font_size_px}px;
            """
        )

    def set_text_size(self, size_px: int = 9):
        self.font_size_px = size_px
        self._update_stylesheet()


# class HoverGrayLabel(GrayLabel):
#     def __init__(self, text: str):
#         super().__init__(text)

#     def _update_stylesheet(self):
#         self.setStyleSheet(
#             f"""
#                 HoverGrayLabel {{
#                     color: rgba(128, 128, 128, 1.0);
#                     font-size: {self.font_size_px}px;
#                 }}
#                 HoverGrayLabel:hover {{
#                     color: rgba(255, 255, 255, 1.0);
#                 }}
#             """
#         )


class ConfirmWindow(UMainWidget):
    ok_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    icon_path = os.path.join(Static.common_icons, "yellow_warning.svg")
    icon_size = 40

    def __init__(self, text: str, w: int, h: int):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.attention[JsonData.lng_index])

        self.central_layout.setContentsMargins(15, 5, 5, 0)
        self.central_layout.setSpacing(0)

        text_container = QWidget()
        self.central_layout.addWidget(text_container)

        text_layout = QHBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(15)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(self.icon_path)
        self.svg_widget.setFixedSize(self.icon_size, self.icon_size)
        text_layout.addWidget(self.svg_widget)

        self.text_wid = SelectableLabel(text)
        self.text_wid.setWordWrap(True)
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
    

class SuperConfirmWindow(ConfirmWindow):
    icon_path = os.path.join(Static.common_icons, "red_warning.svg")

    def __init__(self, text: str, w: int, h: int):
        super().__init__(text, w, h)
        self.svg_widget.load(self.icon_path)


class WarningWindow(ConfirmWindow):
    def __init__(self, text, w, h):
        super().__init__(text, w, h)
        self.cancel_btn.hide()


class SaveRowArrowWidget(RowArrowWidget):
    save_svg = os.path.join(Static.common_icons, "save.svg")

    def __init__(self, lng_index: int):
        super().__init__(Lng.save[lng_index])
        self.set_left_icon(self.save_svg)


class MfAliasWidget(UGroupBox):
    changed = pyqtSignal()

    def __init__(self, lng_index: int):
        super().__init__()
        self.lng_index = lng_index

        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(5, 2, 5, 2)
        v_layout.setSpacing(5)

        name_text = QLabel(Lng.folder_name[lng_index])
        v_layout.addWidget(name_text)

        self.line_edit = ULineEdit()
        self.line_edit.textChanged.connect(self.changed.emit)
        self.line_edit.setPlaceholderText(Lng.alias_immutable[lng_index])
        v_layout.addWidget(self.line_edit)

    def validate(self):

        def show_warn(text: str, w, h):
            win_warn = WarningWindow(text, w, h)
            win_warn.ok_clicked.connect(win_warn.deleteLater)
            win_warn.setFixedSize(w, h)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        pattern = r'^[A-Za-zА-Яа-яЁё0-9 ]+$'
        mf_alias = self.line_edit.text()
        result = None
        if not mf_alias:
            show_warn(Lng.enter_alias_warning[self.lng_index], 260, 90)
        elif len(mf_alias) < 5 or len(mf_alias) > 50:
            show_warn(f'{Lng.string_limit[self.lng_index]}', 280, 90)
        elif not re.fullmatch(pattern, mf_alias):
            show_warn(f'{Lng.valid_message[self.lng_index]}', 310, 90)
        else:
            result = mf_alias
        return result


class MfPathWidget(UGroupBox):
    changed = pyqtSignal()
    magnifier = os.path.join(Static.common_icons, "magnifier.svg")
    green_checkmark = os.path.join(Static.common_icons, "green_checkmark.svg")
    hh = 70
    icon_size = 35

    def __init__(self, lng_index: int, mf_path: str = None):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedHeight(self.hh)

        self.mf_path = mf_path
        self.lng_index = lng_index
        
        # Таймер инициализируем один раз как атрибут класса
        self.watch_timer = QTimer(self)
        self.watch_timer.timeout.connect(self.check_path_by_timer)
    
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(10, 2, 2, 2)
        self.main_lay.setSpacing(0)

        # Используем QStackedWidget для безопасного переключения экранов
        self.stack = QStackedWidget()
        self.main_lay.addWidget(self.stack)

        # Создаем обе панели заранее
        self.init_no_path_ui()
        self.init_ok_path_ui()

        if self.mf_path and os.path.exists(self.mf_path):
            self.show_ok_path()
        else:
            self.show_no_path()

    def init_no_path_ui(self):
        """Создание панели 'Путь не выбран' (индекс 0 в стеке)"""
        widget = QWidget()
        h_lay = QHBoxLayout(widget)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(self.magnifier)
        right_btn.setFixedSize(self.icon_size, self.icon_size)
        h_lay.addWidget(right_btn)
        
        lines = (
            f"{Lng.folder_path[self.lng_index]}:",
            Lng.path_hint_texts[self.lng_index].lower()
        )
        self.no_path_label = QLabel("\n".join(lines))
        self.no_path_label.setWordWrap(True)
        h_lay.addWidget(self.no_path_label)
        h_lay.addStretch()
        
        self.stack.addWidget(widget)

    def init_ok_path_ui(self):
        """Создание панели 'Путь корректен' (индекс 1 в стеке)"""
        widget = QWidget()
        h_lay = QHBoxLayout(widget)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(self.green_checkmark)
        right_btn.setFixedSize(35, 35)
        h_lay.addWidget(right_btn)

        self.ok_path_label = SelectableLabel("")
        h_lay.addWidget(self.ok_path_label)
        h_lay.addStretch()

        self.stack.addWidget(widget)

    def show_no_path(self):
        """Включение режима ожидания пути"""
        self.stack.setCurrentIndex(0)
        if not self.watch_timer.isActive():
            self.watch_timer.start(1000)  # Проверка каждую секунду

    def show_ok_path(self):
        """Включение режима успешного пути"""
        self.watch_timer.stop()  # Важно: останавливаем таймер сразу
        lines = (f"{Lng.folder_path[self.lng_index]}:", self.mf_path)
        self.ok_path_label.setText('\n'.join(lines))
        self.stack.setCurrentIndex(1)

    def check_path_by_timer(self):
        """Срабатывание таймера"""
        if self.mf_path and os.path.exists(self.mf_path):
            self.changed.emit()
            self.show_ok_path()

    def update_path(self, new_path: str):
        """Единый метод обновления пути из любых событий"""
        self.mf_path = new_path.rstrip(os.sep)
        self.changed.emit()
        self.show_ok_path()

    def validate(self):
        def show_warn(text: str, w, h):
            win_warn = WarningWindow(text, w, h)
            win_warn.ok_clicked.connect(win_warn.deleteLater)
            win_warn.setFixedSize(w, h)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        if not self.mf_path:
            show_warn(Lng.select_folder_path[self.lng_index], 260, 90)
            return None
        if not os.path.exists(self.mf_path):
            show_warn(Lng.path_not_exists[self.lng_index], 260, 90)
            return None
        return self.mf_path

    def mouseReleaseEvent(self, a0: QMouseEvent):
        if a0.button() != Qt.MouseButton.LeftButton:  # Исправлена проверка кнопки мыши
            return super().mouseReleaseEvent(a0)
        
        dialog = QFileDialog()
        url = dialog.getExistingDirectory()
        if url and os.path.isdir(url):
            self.update_path(url)
        return super().mouseReleaseEvent(a0)
        
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile()
            if url and os.path.isdir(url):
                self.update_path(url)
        return super().dropEvent(a0)
    
    def dragEnterEvent(self, a0):
        if a0.mimeData().hasUrls():  # Принимаем дроп только если это ссылки/файлы
            a0.accept()
        return super().dragEnterEvent(a0)


class MfStopListWidget(UGroupBox):
    changed = pyqtSignal()

    def __init__(self, lng_index: int, mf_stop_list: list[str]):
        super().__init__()
        self.lng_index = lng_index

        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(5, 2, 5, 2)
        v_layout.setSpacing(5)

        name_text = QLabel(Lng.ignore_list_descr[lng_index])
        v_layout.addWidget(name_text)

        self.text_edit = UTextEdit()
        self.text_edit.setPlaceholderText(Lng.ignore_list[lng_index])
        self.text_edit.textChanged.connect(self.changed.emit)
        v_layout.addWidget(self.text_edit)

        if mf_stop_list:
            self.text_edit.setPlainText("\n".join(mf_stop_list))
