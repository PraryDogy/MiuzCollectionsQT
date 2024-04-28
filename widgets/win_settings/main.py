import os
from typing import Literal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFileDialog, QLabel, QSpacerItem

from base_widgets import Btn, InputBase, LayoutH, LayoutV, WinStandartBase
from cfg import cnf
from signals import gui_signals_app, utils_signals_app
from styles import Styles
from utils import MainUtils


class BrowseColl(LayoutH):
    def __init__(self):
        super().__init__()
        self.new_coll_path = None

        self.browse_btn = Btn(cnf.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        self.addWidget(self.browse_btn)

        self.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel(self.cut_text(cnf.coll_folder))
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setFixedHeight(35)
        self.addWidget(self.coll_path_label)

    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if self.new_coll_path:
            file_dialog.setDirectory(self.new_coll_path)

        elif not os.path.exists(cnf.coll_folder):
            file_dialog.setDirectory(cnf.down_folder)

        else:
            file_dialog.setDirectory(cnf.coll_folder)

        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            self.new_coll_path = selected_folder
            self.coll_path_label.setText(self.cut_text(self.new_coll_path))

    def cut_text(self, text: str, max_ln: int = 70):
        if len(text) > max_ln:
            return text[:max_ln] + "..."
        else:
            return text
        

class ChangeLang(LayoutH):
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

    def finalize(self):
        if self.lang != cnf.user_lng:

            cnf.set_language(self.lang)

            gui_signals_app.reload_menu.emit()
            gui_signals_app.reload_stbar.emit()
            gui_signals_app.reload_filters_bar.emit()
            gui_signals_app.reload_thumbnails.emit()
            gui_signals_app.reload_title.emit()
            gui_signals_app.reload_search_wid.emit()
            gui_signals_app.reload_menubar.emit()


class CustFilters(LayoutH):
    def __init__(self):
        super().__init__()

        self.v_left = LayoutV()
        self.addLayout(self.v_left)

        self.prod_label = QLabel(cnf.lng.cust_fltr_names["prod"])
        self.v_left.addWidget(self.prod_label)

        self.v_left.addSpacerItem(QSpacerItem(0, 10))

        self.prod_input = InputBase()
        self.prod_input.insert(cnf.cust_fltr_names["prod"])
        self.v_left.addWidget(self.prod_input)

        self.addSpacerItem(QSpacerItem(10, 0))

        self.v_right = LayoutV()
        self.addLayout(self.v_right)

        self.mod_label = QLabel(cnf.lng.cust_fltr_names["mod"])
        self.v_right.addWidget(self.mod_label)

        self.v_right.addSpacerItem(QSpacerItem(0, 10))

        self.mod_input = InputBase()
        self.mod_input.insert(cnf.cust_fltr_names["mod"])
        self.v_right.addWidget(self.mod_input)

    def get_inputs(self) -> dict:
        return {
            "prod": self.prod_input.text(),
            "mod": self.mod_input.text()
            }
    

class StopWords(LayoutV):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.label = QLabel(cnf.lng.sett_stopwords)
        self.addWidget(self.label)

        self.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(cnf.stop_words))
        self.addWidget(self.input)

    def get_stopwords(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class StopColls(LayoutV):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.label = QLabel(cnf.lng.sett_stopcolls)
        self.addWidget(self.label)

        self.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(cnf.stop_colls))
        self.addWidget(self.input)

    def get_stopcolls(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class ThumbMove(LayoutH):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.move_jpg = cnf.move_jpg
        self.move_layers = cnf.move_layers

        self.btn_jpg = Btn("JPG")
        self.btn_jpg.setStyleSheet(self.get_jpg_style())
        self.btn_jpg.mouseReleaseEvent = lambda f: self.btn_cmd("jpg")
        self.addWidget(self.btn_jpg)

        self.addSpacerItem(QSpacerItem(1, 0))

        self.btn_tiff = Btn(cnf.lng.layers)
        self.btn_tiff.mouseReleaseEvent = lambda f: self.btn_cmd("tiff")
        self.btn_tiff.setStyleSheet(self.get_tiff_style())
        
        self.addWidget(self.btn_tiff)

        self.addSpacerItem(QSpacerItem(10, 0))

        descr = QLabel(cnf.lng.thumb_move)
        self.addWidget(descr)

        self.addStretch()

    def btn_cmd(self, flag: Literal["jpg", "tiff"]):
        if flag == "jpg":
            self.move_jpg = not self.move_jpg
            self.btn_jpg.setStyleSheet(self.get_jpg_style())
        
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

class WinSettings(WinStandartBase):
    def __init__(self):
        MainUtils.close_same_win(WinSettings)

        super().__init__(close_func=self.cancel_cmd)
        self.disable_min_max()
        self.set_title(cnf.lng.settings)

        self.setFixedWidth(420)
        temp = QTimer(self)
        temp.setSingleShot(True)
        temp.timeout.connect(self.init_ui)
        temp.start(10)
        self.setFixedSize(420, 550)
        self.center_win()
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        coll_title = QLabel(cnf.lng.browse_colls_descr)
        self.content_layout.addWidget(coll_title)
        self.content_layout.addSpacerItem(QSpacerItem(0, 10))

        self.browse_coll = BrowseColl()
        self.content_layout.addLayout(self.browse_coll)
        self.content_layout.addLayout(self.my_separ())

        self.change_lang = ChangeLang()
        self.content_layout.addLayout(self.change_lang)
        self.content_layout.addLayout(self.my_separ())

        self.thumb_move = ThumbMove()
        self.content_layout.addLayout(self.thumb_move)
        self.content_layout.addLayout(self.my_separ())

        self.cust_filters = CustFilters()
        self.content_layout.addLayout(self.cust_filters)
        self.content_layout.addLayout(self.my_separ())

        self.stopwords = StopWords()
        self.content_layout.addLayout(self.stopwords)
        self.content_layout.addLayout(self.my_separ())

        self.stopcolls = StopColls()
        self.content_layout.addLayout(self.stopcolls)
        self.content_layout.addLayout(self.my_separ())

        btns_layout = LayoutH()
        self.content_layout.addLayout(btns_layout)

        btns_layout.addStretch(1)

        self.ok_btn = Btn(cnf.lng.ok)
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        btns_layout.addWidget(self.ok_btn)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        self.cancel_btn = Btn(cnf.lng.cancel)
        self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
        btns_layout.addWidget(self.cancel_btn)

        btns_layout.addStretch(1)

    def my_separ(self, value=40) -> LayoutV:
        v_layout = LayoutV()
        v_layout.addSpacerItem(QSpacerItem(0, value))
        return v_layout

    def cancel_cmd(self, e):
        self.deleteLater()

    def ok_cmd(self, e):
        scan_again = False

        if self.browse_coll.new_coll_path:
            cnf.coll_folder = self.browse_coll.new_coll_path
            scan_again = True

        if self.stopwords.get_stopwords() != cnf.stop_words:
            cnf.stop_words = self.stopwords.get_stopwords()
            scan_again = True

        if self.stopcolls.get_stopcolls() != cnf.stop_colls:
            cnf.stop_colls = self.stopcolls.get_stopcolls()
            scan_again = True

        if scan_again:
            utils_signals_app.scaner_stop.emit()
            utils_signals_app.scaner_start.emit()

            # utils_signals_app.watcher_stop.emit()
            # utils_signals_app.watcher_start.emit()

        self.change_lang.finalize()
        self.thumb_move.finalize()

        self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.deleteLater()

        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.ok_cmd(event)

        super().keyPressEvent(event)
