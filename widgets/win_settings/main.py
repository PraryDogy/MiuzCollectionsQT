import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QFileDialog, QLabel, QSpacerItem, QWidget

from base_widgets import Btn, InputBase, LayoutH, LayoutV, WinStandartBase
from cfg import cnf
from signals import gui_signals_app, utils_signals_app
from utils import MainUtils, Updater


class BrowseColl(QWidget):
    def __init__(self):
        super().__init__()
        self.new_coll_path = None

        layout_h = LayoutH()
        self.setLayout(layout_h)

        self.browse_btn = Btn(cnf.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        layout_h.addWidget(self.browse_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel(self.cut_text(cnf.coll_folder))
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setFixedHeight(35)
        layout_h.addWidget(self.coll_path_label)

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
        

class ChangeLang(QWidget):
    def __init__(self):
        super().__init__()
        self.lang = cnf.user_lng

        layout_h = LayoutH()
        self.setLayout(layout_h)

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


class CustFilters(QWidget):
    def __init__(self):
        super().__init__()

        layout_h = LayoutH()
        self.setLayout(layout_h)

        self.v_left = LayoutV()
        layout_h.addLayout(self.v_left)

        self.prod_label = QLabel(cnf.lng.cust_fltr_names["prod"])
        self.v_left.addWidget(self.prod_label)

        self.v_left.addSpacerItem(QSpacerItem(0, 10))

        self.prod_input = InputBase()
        self.prod_input.insert(cnf.cust_fltr_names["prod"])
        self.v_left.addWidget(self.prod_input)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.v_right = LayoutV()
        layout_h.addLayout(self.v_right)

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
    

class StopWords(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_v = LayoutV()
        self.setLayout(layout_v)

        self.label = QLabel(cnf.lng.sett_stopwords)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(cnf.stop_words))
        layout_v.addWidget(self.input)

    def get_stopwords(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class StopColls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_v = LayoutV()
        self.setLayout(layout_v)

        self.label = QLabel(cnf.lng.sett_stopcolls)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(cnf.stop_colls))
        layout_v.addWidget(self.input)

    def get_stopcolls(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class UpdaterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutV()
        self.setLayout(self.v_layout)

        self.btn = Btn(cnf.lng.download_update)
        self.btn.setFixedWidth(150)
        self.btn.mouseReleaseEvent = self.update_btn_cmd
        self.v_layout.addWidget(self.btn)

    def update_btn_cmd(self, e):
        self.task = Updater()
        self.btn.setText(cnf.lng.wait_update)
        self.task.no_connection.connect(self.no_connection_btn)
        self.task.finished.connect(self.finalize)
        self.task.start()

    def finalize(self):
        self.btn.setText(cnf.lng.download_update)

    def no_connection_btn(self):
        QTimer.singleShot(1000, self.no_connection_btn_style)

    def no_connection_btn_style(self):
        self.btn.setText(cnf.lng.no_connection)
        QTimer.singleShot(1500, lambda: self.btn.setText(cnf.lng.download_update))


class WinSettings(WinStandartBase):
    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.cancel_cmd)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.disable_min_max()
        self.set_title(cnf.lng.settings)

        QTimer.singleShot(10, self.init_ui)
        self.setFixedSize(420, 440)
        self.center_win(parent)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        self.change_lang = ChangeLang()
        self.content_layout.addWidget(self.change_lang)
        self.content_layout.addSpacerItem(QSpacerItem(0, 30))

        self.update_wid = UpdaterWidget()
        self.content_layout.addWidget(self.update_wid)
        self.content_layout.addSpacerItem(QSpacerItem(0, 30))

        self.cust_filters = CustFilters()
        self.content_layout.addWidget(self.cust_filters)
        self.content_layout.addSpacerItem(QSpacerItem(0, 30))

        self.stopwords = StopWords()
        self.content_layout.addWidget(self.stopwords)
        self.content_layout.addSpacerItem(QSpacerItem(0, 30))

        self.stopcolls = StopColls()
        self.content_layout.addWidget(self.stopcolls)
        self.content_layout.addSpacerItem(QSpacerItem(0, 30))

        self.content_layout.addStretch()

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

    def cancel_cmd(self, e):
        self.close()

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

        self.change_lang.finalize()

        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
