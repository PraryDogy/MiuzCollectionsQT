import os
import sys

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QFileDialog, QGroupBox, QHBoxLayout,
                             QLabel, QMenu, QSizePolicy, QVBoxLayout, QWidget)

from cfg import Static
from widgets._base_widgets import (RowArrowWidget, SelectableLabel, ULineEdit,
                                   UMainWidget, UPushButton)
from widgets.win_warn import WarningWindow


class Lng:
    app_lang = (
        "Язык приложения",
        "Application language"
    )
    lang = (
        "Язык",
        "Language"
    )
    rus = (
        "Русский",
        "Russian"
    )
    eng = (
        "Английский",
        "English"
    )
    folder_name = (
        "Имя:\n"
        "• уникальное\n"
        "• 5-30 символов\n"
        "• русские и английские буквы, цифры и пробелы",
        "Folder name:\n"
        "• unique\n"
        "• up to 5-30 characters\n"
        "• Russian and English letters, digits, and spaces",
    )
    alias_immutable = (
        "Имя (нельзя изменить после сохранения)",
        "Name (cannot be changed after saving)"
    )
    settings = (
        "Настройка",
        "Setup"
    )
    folder_path = (
        "Путь к каталогу",
        "Catalog path"
    )
    path_hint_texts = (
        "Перетащите каталог сюда или нажмите для выбора",
        "Drag and drop a catalog here or click to browse"
    )
    bad_smb = (
        "Путь к каталогу изображений указан неверно.",
        "The image directory path is incorrect."
    )


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


class FirstLoadWin(UMainWidget):
    rus_flag = os.path.join(Static.internal_icons, "rus_flag.svg")
    eng_flag = os.path.join(Static.internal_icons, "eng_flag.svg")

    def __init__(self):
        super().__init__()
        self.resize(500, 500)
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

    def init_ui(self):
        self.setWindowTitle(Lng.settings[self.lng_index])
        self.init_lang_widget()
        self.init_mf_alias_widget()
        self.init_path_widget()

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

        self.name_line_edit = ULineEdit()
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


app = QApplication(sys.argv)
win = FirstLoadWin()
win.show()
app.exec()