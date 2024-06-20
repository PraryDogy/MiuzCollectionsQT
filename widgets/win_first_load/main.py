import os
from typing import Literal

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFileDialog, QLabel, QSpacerItem,
                             QWidget)

from base_widgets import Btn, LayoutH, LayoutV, WinStandartBase
from cfg import cnf
from signals import gui_signals_app, utils_signals_app
from styles import Names, Themes
from utils import MainUtils


class Manager:
    coll_folder = cnf.coll_folder


class BrowseColl(QWidget):
    def __init__(self):
        super().__init__()

        layout_v = LayoutV()
        self.setLayout(layout_v)

        descr = QLabel(cnf.lng.browse_coll_first)
        layout_v.addWidget(descr)

        h_wid = QWidget()
        h_wid.setFixedHeight(50)
        layout_v.addWidget(h_wid)

        h_layout = LayoutH()
        h_wid.setLayout(h_layout)

        self.browse_btn = Btn(cnf.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        h_layout.addWidget(self.browse_btn)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel(self.cut_text(Manager.coll_folder))
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setFixedHeight(35)
        h_layout.addWidget(self.coll_path_label)

    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if not os.path.exists(Manager.coll_folder):
            file_dialog.setDirectory(cnf.down_folder)
        else:
            file_dialog.setDirectory(Manager.coll_folder)

        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            Manager.coll_folder = selected_folder
            self.coll_path_label.setText(self.cut_text(Manager.coll_folder))

    def cut_text(self, text: str, max_ln: int = 70):
        if len(text) > max_ln:
            return text[:max_ln] + "..."
        else:
            return text
        
    def finalize(self):
        cnf.coll_folder = Manager.coll_folder

        utils_signals_app.scaner_stop.emit()
        utils_signals_app.scaner_start.emit()


class ChangeLang(QWidget, QObject):
    change_lang = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout_h = LayoutH()
        self.setLayout(layout_h)

        self.lang = cnf.user_lng

        self.lang_btn = Btn(self.get_lng_text())
        self.lang_btn.mouseReleaseEvent = self.lng_cmd
        layout_h.addWidget(self.lang_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.lang_label = QLabel(cnf.lng.lang_label)
        layout_h.addWidget(self.lang_label)

    def get_lng_text(self):
        return "🇷🇺 Ru" if self.lang == "ru" else "🇺🇸 En"
          
    def lng_cmd(self, e):
        if self.lang == "ru":
            self.lang = "en"
        else:
            self.lang = "ru"

        self.lang_btn.setText(self.get_lng_text())

        cnf.set_language(self.lang)

        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_stbar.emit()
        gui_signals_app.reload_filters_bar.emit()
        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.reload_title.emit()
        gui_signals_app.reload_search_wid.emit()
        gui_signals_app.reload_menubar.emit()

        self.change_lang.emit()


class WinFirstLoad(WinStandartBase):
    def __init__(self):
        MainUtils.close_same_win(WinFirstLoad)

        super().__init__(close_func=self.cancel_cmd)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.disable_min_max()
        self.disable_close()

        self.init_ui()
        self.setFixedSize(350, 220)
        self.center()
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def cancel_cmd(self, event):
        pass

    def init_ui(self):
        self.change_lang = ChangeLang()
        self.change_lang.change_lang.connect(self.reload_ui)
        self.content_layout.addWidget(self.change_lang)

        self.content_layout.addSpacerItem(QSpacerItem(0, 20))

        self.browse_coll = BrowseColl()
        self.content_layout.addWidget(self.browse_coll)

        self.content_layout.addSpacerItem(QSpacerItem(0, 20))

        self.ok_btn = Btn(cnf.lng.ok)
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        self.content_layout.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def reload_ui(self):
        MainUtils.clear_layout(self.content_layout)
        self.init_ui()

    def ok_cmd(self, e):
        self.browse_coll.finalize()
        self.deleteLater()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        return
        return super().keyPressEvent(a0)
