import os
from typing import Literal

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import (QDesktopWidget, QFileDialog, QLabel, QSpacerItem,
                             QWidget)

from base_widgets import Btn, LayoutH, LayoutV, WinStandartBase
from cfg import cnf
from signals import gui_signals_app, utils_signals_app
from styles import Styles
from utils import MainUtils
from widgets.win_err import WinErr


class Manager:
    coll_folder = cnf.coll_folder


class BrowseColl(LayoutV):
    def __init__(self):
        super().__init__()
        descr = QLabel(cnf.lng.browse_coll_first)
        self.addWidget(descr)

        h_wid = QWidget()
        h_wid.setFixedHeight(50)
        self.addWidget(h_wid)

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
        cnf.migrate_data["old_coll"] = cnf.coll_folder
        cnf.migrate_data["new_coll"] = Manager.coll_folder
        cnf.coll_folder = Manager.coll_folder

        utils_signals_app.watcher_stop.emit()
        utils_signals_app.watcher_start.emit()

        utils_signals_app.scaner_stop.emit()
        utils_signals_app.scaner_start.emit()

        if not MainUtils.smb_check():

            Manager.smb_win = WinErr()
            Manager.smb_win.show()



class ChangeLang(LayoutH, QObject):
    change_lang = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lang = cnf.user_lng

        self.lang_btn = Btn(self.get_lng_text())
        self.lang_btn.mouseReleaseEvent = self.lng_cmd
        self.addWidget(self.lang_btn)

        self.addSpacerItem(QSpacerItem(10, 0))

        self.lang_label = QLabel(cnf.lng.lang_label)
        self.addWidget(self.lang_label)

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


class ChooseUserType(LayoutV):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.move_jpg = cnf.move_jpg
        self.move_layers = cnf.move_layers

        descr = QLabel(cnf.lng.choose_user_first)
        self.addWidget(descr)

        h_wid = QWidget()
        h_wid.setFixedHeight(50)
        self.addWidget(h_wid)

        self.addSpacerItem(QSpacerItem(0, 10))

        h_layout = LayoutH()
        h_wid.setLayout(h_layout)

        h_layout.addStretch()

        self.btn_standart = Btn(cnf.lng.user_standart)
        self.btn_standart.setStyleSheet(self.get_jpg_style())
        self.btn_standart.mouseReleaseEvent = lambda f: self.btn_cmd("jpg")
        h_layout.addWidget(self.btn_standart)

        h_layout.addSpacerItem(QSpacerItem(1, 0))

        self.btn_tiff = Btn(cnf.lng.user_designer)
        self.btn_tiff.mouseReleaseEvent = lambda f: self.btn_cmd("tiff")
        self.btn_tiff.setStyleSheet(self.get_tiff_style())
        h_layout.addWidget(self.btn_tiff)

        h_layout.addStretch()

    def btn_cmd(self, flag: Literal["jpg", "tiff"]):
        if flag == "jpg":
            self.move_jpg = not self.move_jpg
            self.btn_standart.setStyleSheet(self.get_jpg_style())
        
        elif flag == "tiff":
            self.move_layers = not self.move_layers
            self.btn_tiff.setStyleSheet(self.get_tiff_style())

    def finalize(self):
        if self.move_jpg != cnf.move_jpg or self.move_layers != cnf.move_layers:
            cnf.move_jpg = self.move_jpg
            cnf.move_layers = self.move_layers
            gui_signals_app.reload_stbar.emit()

    def get_bg(self, flag: Literal["jpg", "tiff"]):
        if flag == "jpg":
            return Styles.blue_color if self.move_jpg else Styles.btn_base_color
        
        elif flag == "tiff":
            return Styles.blue_color if self.move_layers else Styles.btn_base_color

    def get_jpg_style(self):
        return f"""
                background: {self.get_bg("jpg")};
                border-top-left-radius: {Styles.small_radius}px;
                border-bottom-left-radius: {Styles.small_radius}px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                """

    def get_tiff_style(self):
        return f"""
                background: {self.get_bg("tiff")};
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: {Styles.small_radius}px;
                border-bottom-right-radius: {Styles.small_radius}px;
                """

class WinFirstLoad(WinStandartBase):
    def __init__(self):
        MainUtils.close_same_win(WinFirstLoad)

        super().__init__(close_func=self.cancel_cmd)
        self.disable_min_max()

        self.init_ui()
        self.setFixedSize(350, 340)
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
        self.content_layout.addLayout(self.change_lang)

        self.content_layout.addSpacerItem(QSpacerItem(0, 20))

        self.browse_coll = BrowseColl()
        self.content_layout.addLayout(self.browse_coll)

        self.content_layout.addSpacerItem(QSpacerItem(0, 20))

        self.user_type = ChooseUserType()
        self.content_layout.addLayout(self.user_type)

        self.ok_btn = Btn(cnf.lng.ok)
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        self.content_layout.addWidget(self.ok_btn, alignment=Qt.AlignCenter)

    def reload_ui(self):
        MainUtils.clear_layout(self.content_layout)
        self.init_ui()

    def ok_cmd(self, e):
        self.user_type.finalize()
        self.browse_coll.finalize()

        self.delete_win.emit()
        self.deleteLater()

    def keyPressEvent(self, event):
        event.ignore()

