import os
import re
import sys

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QContextMenuEvent, QIcon, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QFileDialog, QFrame, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QMenu,
                             QPushButton, QSpacerItem, QVBoxLayout, QWidget)
from typing_extensions import Optional

from cfg import Static
from system.lang import Lng
from system.main_folder import Mf
from system.utils import Utils

# from widgets.win_warn import ConfirmWindow, WarningWindow


def restart_app():
    os.execl(sys.executable, sys.executable, *sys.argv)
    QApplication.exit(0)


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


class UPushButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet(
            """
            font-size: 11pt;
            """
        )
        self.setFixedWidth(80)


class ULineEdit(QLineEdit):
    hh = 30

    def __init__(self, lng_index: int):
        super().__init__()
        self.lng_index = lng_index
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
            (Lng.cut[self.lng_index], self.cut_selection),
            (Lng.copy[self.lng_index], lambda: Utils.copy_text(self.selectedText())),
            (Lng.paste[self.lng_index], self.paste_text),
        ]

        for text, slot in actions:
            act = QAction(text=text, parent=self.menu_)
            act.triggered.connect(slot)
            self.menu_.addAction(act)

        self.menu_.show_menu()


class SelectableLabel(QLabel):
    sym_line_feed = "\u000a"
    sym_paragraph_sep = "\u2029"

    def __init__(self, text: str, lng_index: int):
        super().__init__(text)
        self.lng_index = lng_index
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

        label_text = Lng.copy[self.lng_index]
        sel = QAction(text=label_text, parent=self)
        sel.triggered.connect(lambda: Utils.copy_text(text))
        menu_.addAction(sel)

        reveal = QAction(parent=menu_, text=Lng.reveal_in_finder[self.lng_index])
        reveal.triggered.connect(
            lambda: Utils.reveal_files([full_text])
        )
        
        if is_path:
            menu_.addAction(reveal)

        menu_.show_menu()


class HSep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
                background: rgba(128, 128, 128, 0.2);
            """
        )
        self.setFixedHeight(1)


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


class PathWidget(QGroupBox):
    mf_path_avaiable = pyqtSignal(str)
    magnifier = os.path.join(Static.internal_icons, "magnifier.svg")
    green_checkmark = os.path.join(Static.internal_icons, "green_checkmark.svg")
    hh = 70
    icon_size = 35

    def __init__(self, lng_index: int):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedHeight(self.hh)

        self.current_path = None
        self.lng_index = lng_index
    
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(2, 2, 2, 2)
        self.main_lay.setSpacing(0)

        self.main_wid = QWidget()
        self.main_lay.addWidget(self.main_wid)

        self.no_path_widget()

    def no_path_widget(self):
        self.main_wid.deleteLater()
        self.main_wid = QWidget()
        self.main_lay.addWidget(self.main_wid)

        h_lay = QHBoxLayout(self.main_wid)
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
        left_label = QLabel("\n".join(lines))
        left_label.setWordWrap(True)
        h_lay.addWidget(left_label)

        h_lay.addStretch()

    def ok_path_widget(self):
        self.main_wid.deleteLater()
        self.main_wid = QWidget()
        self.main_lay.addWidget(self.main_wid)

        h_lay = QHBoxLayout(self.main_wid)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(self.green_checkmark)
        right_btn.setFixedSize(35, 35)
        h_lay.addWidget(right_btn)

        lines = (
            f"{Lng.folder_path[self.lng_index]}:",
            self.current_path
        )
        left_label = SelectableLabel('\n'.join(lines))
        h_lay.addWidget(left_label)

        h_lay.addStretch()

    def mouseReleaseEvent(self, a0: QMouseEvent):
        if not a0.button() != 2:
            return
        dialog = QFileDialog()
        url = dialog.getExistingDirectory()
        if url and os.path.isdir(url):
            self.current_path = url.rstrip(os.sep)
            self.mf_path_avaiable.emit(self.current_path)
            self.ok_path_widget()
        return super().mouseReleaseEvent(a0)
        
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile()
            if url and os.path.isdir(url):
                self.current_path = url.rstrip(os.sep)
                self.mf_path_avaiable.emit(self.current_path)
                self.ok_path_widget()
        return super().dropEvent(a0)
    
    def dragEnterEvent(self, a0):
        a0.accept()
        return super().dragEnterEvent(a0)


class FirstLoadWin(QWidget):
    rus_flag = os.path.join(Static.internal_icons, "rus_flag.svg")
    eng_flag = os.path.join(Static.internal_icons, "eng_flag.svg")

    def __init__(self):
        super().__init__()
        self.resize(500, 500)

        self.central_layout = QVBoxLayout(self)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setSpacing(10)
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lng_index = 0
        self.margins = 3
        self.init_ui()

    def remove_ui(self):
        self.lng_container.deleteLater()
        self.mf_container.deleteLater()
        self.path_widget.deleteLater()
        self.last_block_container.deleteLater()

    def init_ui(self):
        self.setWindowTitle(Lng.settings[self.lng_index])
        self.init_lang_widget()
        self.init_mf_alias_widget()
        self.init_path_widget()
        self.init_last_block()

    def lng_action(self, value: int):
        if self.lng_index == value:
            return
        self.lng_index = value
        self.remove_ui()
        self.init_ui()

    def init_lang_widget(self):
        rus_action_text = Lng.rus[self.lng_index]
        eng_action_text = Lng.eng[self.lng_index]

        if self.lng_index == 0:
            lng_label_text = f"{Lng.app_lang[0]} ({Lng.app_lang[1]})"
            lng_btn_text = rus_action_text
            lng_btn_icon = QIcon(self.rus_flag)
        else:
            lng_label_text = f"{Lng.app_lang[1]} ({Lng.app_lang[0]})"
            lng_btn_text = eng_action_text
            lng_btn_icon  = QIcon(self.eng_flag)

        # Сохраняем ссылку в self.lng_container
        self.lng_container = QGroupBox()
        self.central_layout.addWidget(self.lng_container)
        
        lng_layout = QHBoxLayout(self.lng_container)
        lng_layout.setContentsMargins(2, 2, 2, 2)
        lng_layout.setSpacing(0)

        lng_label = QLabel(lng_label_text)
        lng_layout.addWidget(lng_label)
        lng_layout.addStretch()

        lng_btn = UPushButton(lng_btn_text)
        lng_btn.setFixedWidth(100)
        lng_btn.setIcon(lng_btn_icon)
        lng_layout.addWidget(lng_btn)

        lng_menu = QMenu(lng_btn)
        lng_btn.setMenu(lng_menu)

        rus_icon = QIcon(self.rus_flag)
        rus_action = QAction(rus_icon, rus_action_text, lng_menu)
        rus_action.setIconVisibleInMenu(True)
        rus_action.triggered.connect(lambda e, val=0: self.lng_action(val))
        lng_menu.addAction(rus_action)

        eng_icon = QIcon(self.eng_flag)
        eng_action = QAction(eng_icon, eng_action_text, lng_menu)
        eng_action.setIconVisibleInMenu(True)
        eng_action.triggered.connect(lambda e, val=1: self.lng_action(val))
        lng_menu.addAction(eng_action)

    def init_mf_alias_widget(self):
        self.mf_container = QGroupBox()
        self.central_layout.addWidget(self.mf_container)

        mf_layout = QVBoxLayout(self.mf_container)
        mf_layout.setContentsMargins(2, 2, 2, 2)
        mf_layout.setSpacing(5)

        name_text = QLabel(Lng.folder_name[self.lng_index])
        mf_layout.addWidget(name_text)

        self.name_line_edit = ULineEdit(self.lng_index)
        self.name_line_edit.setPlaceholderText(Lng.alias_immutable[self.lng_index])
        mf_layout.addWidget(self.name_line_edit)

    def init_path_widget(self):

        def mf_avaiable(path: str):
            dir_name = os.path.basename(path)
            if not self.name_line_edit.text():
                self.name_line_edit.setText(dir_name)

        self.path_widget = PathWidget(self.lng_index)
        self.path_widget.mf_path_avaiable.connect(mf_avaiable)
        self.central_layout.addWidget(self.path_widget)

    def init_last_block(self):
        self.last_block_container = QGroupBox()
        self.central_layout.addWidget(self.last_block_container)

        last_block_layout = QVBoxLayout(self.last_block_container)
        last_block_layout.setContentsMargins(2, 0, 2, 0)
        last_block_layout.setSpacing(0)

        self.backup_widget = RowArrowWidget("Бекап")
        last_block_layout.addWidget(self.backup_widget)

        save_widget = RowArrowWidget(Lng.save[self.lng_index])
        save_widget.hide_sep()
        save_widget.clicked.connect(self.save_cmd)
        last_block_layout.addWidget(save_widget)

    def save_cmd(self, *args):

        def show_warn(text: str, w, h):
            return
            win_warn = WarningWindow(text)
            win_warn.setFixedSize(w, h)
            win_warn.center_to_parent(self.window())
            win_warn.show()

        def save_fin(folder_name: str, paths: list[str]):
            mf = Mf(
                mf_alias=folder_name,
                mf_paths=paths,
                mf_stop_list=[],
                mf_current_path=paths[0]
            )
            Mf.items.clear()
            Mf.items.append(mf)
            Mf.write_json_data()
            restart_app()

        pattern = r'^[A-Za-zА-Яа-яЁё0-9 ]+$'
        folder_name = self.name_line_edit.text()
        paths = []
        if self.path_widget.current_path:
            paths.append(self.path_widget.current_path)

        if not folder_name:
            show_warn(Lng.enter_alias_warning[self.lng_index], 260, 90)
            return

        elif len(folder_name) < 5 or len(folder_name) > 30:
            show_warn(f'{Lng.string_limit[self.lng_index]}', 280, 90)
            return

        elif not re.fullmatch(pattern, folder_name):
            show_warn(f'{Lng.valid_message[self.lng_index]}', 310, 90)
            return

        elif not paths:
            show_warn(Lng.select_folder_path[self.lng_index])
            return

        # win = ConfirmWindow(Lng.save_text_long[self.lng_index])
        # win.setFixedSize(300, 90)
        # win.ok_clicked.connect(
        #     lambda: save_fin(folder_name, paths)
        # )
        # win.center_to_parent(self.window())
        # win.show()

# app = QApplication(sys.argv)
# win = FirstLoadWin()
# win.show()
# app.exec()