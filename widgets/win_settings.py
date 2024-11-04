import os
import subprocess

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel, QSpacerItem,
                             QTextEdit, QWidget)

from base_widgets import Btn, CustomTextEdit, InputBase, LayoutHor, LayoutVer
from base_widgets.wins import WinChild
from cfg import APP_SUPPORT_DIR, Dynamic, JsonData
from database import Dbase
from utils.main_utils import MainUtils
from utils.scaner import Scaner
from utils.updater import Updater

from .win_smb import WinSmb


class BrowseColl(QWidget):
    def __init__(self):
        super().__init__()
        self.new_coll_path = None

        layout_h = LayoutHor()
        self.setLayout(layout_h)

        self.browse_btn = Btn(Dynamic.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        layout_h.addWidget(self.browse_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel(self.cut_text(JsonData.coll_folder))
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setFixedHeight(35)
        layout_h.addWidget(self.coll_path_label)

    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if self.new_coll_path:
            file_dialog.setDirectory(self.new_coll_path)

        elif not os.path.exists(JsonData.coll_folder):
            file_dialog.setDirectory(JsonData.down_folder)

        else:
            file_dialog.setDirectory(JsonData.coll_folder)

        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            self.new_coll_path = selected_folder
            self.coll_path_label.setText(self.cut_text(self.new_coll_path))

    def cut_text(self, text: str, max_ln: int = 70):
        if len(text) > max_ln:
            return text[:max_ln] + "..."
        else:
            return text


class CollFolderListInput(CustomTextEdit):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(100)
        self.setLineWrapMode(QTextEdit.NoWrap)
        h_bar = self.horizontalScrollBar()
        h_bar.setFixedHeight(0)

        text = "\n".join(JsonData.coll_folder_list)
        self.setText(text)

    def get_text(self):
        text = self.toPlainText()
        coll_folder_list = text.split("\n")


        coll_folder_list = [
            os.sep + i.strip().strip(os.sep)
            for i in coll_folder_list
            ]
        
        return coll_folder_list


class ChangeLang(QWidget):
    _pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.lang = JsonData.lng_name

        layout_h = LayoutHor()
        self.setLayout(layout_h)

        self.lang_btn = Btn(self.get_lng_text())
        self.lang_btn.mouseReleaseEvent = self.lng_cmd
        layout_h.addWidget(self.lang_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.lang_label = QLabel(Dynamic.lng.lang_label)
        layout_h.addWidget(self.lang_label)

    def get_lng_text(self):
        return "🇷🇺 Ru" if self.lang == "ru" else "🇺🇸 En"
          
    def lng_cmd(self, e):
        if self.lang == "ru":
            self.lang = "en"
        else:
            self.lang = "ru"

        self.lang_btn.setText(self.get_lng_text())

        if self.lang != JsonData.lng_name:
            setattr(self, "flag", True)
            self._pressed.emit()


class CustFilters(QWidget):
    def __init__(self):
        super().__init__()

        layout_h = LayoutHor()
        self.setLayout(layout_h)

        left_wid = QWidget()
        self.v_left = LayoutVer()
        left_wid.setLayout(self.v_left)
        layout_h.addWidget(left_wid)

        self.prod_label = QLabel(Dynamic.lng.cust_fltr_names["prod"])
        self.v_left.addWidget(self.prod_label)

        self.v_left.addSpacerItem(QSpacerItem(0, 10))

        self.prod_input = InputBase()
        self.prod_input.insert(JsonData.cust_fltr_names["prod"])
        self.v_left.addWidget(self.prod_input)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        r_wid = QWidget()
        self.v_right = LayoutVer()
        r_wid.setLayout(self.v_right)
        layout_h.addWidget(r_wid)

        self.mod_label = QLabel(Dynamic.lng.cust_fltr_names["mod"])
        self.v_right.addWidget(self.mod_label)

        self.v_right.addSpacerItem(QSpacerItem(0, 10))

        self.mod_input = InputBase()
        self.mod_input.insert(JsonData.cust_fltr_names["mod"])
        self.v_right.addWidget(self.mod_input)

    def get_inputs(self) -> dict:
        return {
            "prod": self.prod_input.text(),
            "mod": self.mod_input.text()
            }
    

class StopWords(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_v = LayoutVer()
        self.setLayout(layout_v)

        self.label = QLabel(Dynamic.lng.sett_stopwords)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(JsonData.stop_words))
        layout_v.addWidget(self.input)

    def get_stopwords(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class StopColls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_v = LayoutVer()
        self.setLayout(layout_v)

        self.label = QLabel(Dynamic.lng.sett_stopcolls)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(JsonData.stop_colls))
        layout_v.addWidget(self.input)

    def get_stopcolls(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class UpdaterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        self.btn = Btn(Dynamic.lng.download_update)
        self.btn.setFixedWidth(150)
        self.btn.mouseReleaseEvent = self.update_btn_cmd
        self.v_layout.addWidget(self.btn)

    def update_btn_cmd(self, e):
        self.task = Updater()
        self.btn.setText(Dynamic.lng.wait_update)
        self.task.no_connection.connect(self.no_connection_win)
        self.task.finished.connect(self.finalize)
        self.task.start()

    def finalize(self):
        self.btn.setText(Dynamic.lng.download_update)

    def no_connection_win(self):
        QTimer.singleShot(1000, lambda: self.btn.setText(Dynamic.lng.download_update))
        self.smb_win = WinSmb(text=Dynamic.lng.connect_sb06)
        self.smb_win.center_relative_parent(self)
        self.smb_win.show()

    def no_connection_btn_style(self):
        self.btn.setText(Dynamic.lng.no_connection)
        QTimer.singleShot(1500, lambda: self.btn.setText(Dynamic.lng.download_update))


class ShowFiles(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        self.btn = Btn(Dynamic.lng.show_app_support)
        self.btn.setFixedWidth(150)
        self.btn.mouseReleaseEvent = self.btn_cmd
        self.v_layout.addWidget(self.btn)

    def btn_cmd(self, e):
        try:
            subprocess.Popen(["open", APP_SUPPORT_DIR])
        except Exception as e:
            print(e)


class RestoreBtn(Btn):
    _pressed = pyqtSignal()

    def __init__(self):
        super().__init__(Dynamic.lng.restore_db)
        self.setFixedWidth(150)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        self._pressed.emit()
        setattr(self, "flag", True)
        return super().mouseReleaseEvent(ev)


class WinSettings(WinChild):
    def __init__(self):
        super().__init__()

        self.close_btn_cmd(self.cancel_cmd)
        self.min_btn_disable()
        self.max_btn_disable()
        self.set_titlebar_title(Dynamic.lng.settings)

        QTimer.singleShot(10, self.init_ui)
        self.setFixedSize(420, 550)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        self.change_lang = ChangeLang()
        self.change_lang._pressed.connect(lambda: self.ok_btn.setText(Dynamic.lng.apply))
        self.content_lay_v.addWidget(self.change_lang)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        h_wid = QWidget()
        self.content_lay_v.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 25))

        self.update_wid = UpdaterWidget()
        h_layout.addWidget(self.update_wid)

        show_files = ShowFiles()
        h_layout.addWidget(show_files)

        self.restore_db_btn = RestoreBtn()
        self.restore_db_btn._pressed.connect(lambda: self.ok_btn.setText(Dynamic.lng.apply))
        self.content_lay_v.addWidget(self.restore_db_btn)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        self.cust_filters = CustFilters()
        self.content_lay_v.addWidget(self.cust_filters)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        # self.stopwords = StopWords()
        # self.content_layout.addWidget(self.stopwords)
        # self.content_layout.addSpacerItem(QSpacerItem(0, 30))

        self.stopcolls = StopColls()
        self.content_lay_v.addWidget(self.stopcolls)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        coll_folder_list_label = QLabel(text=Dynamic.lng.where_to_look_coll_folder)
        self.content_lay_v.addWidget(coll_folder_list_label)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 10))

        self.coll_folder_list_input = CollFolderListInput()
        self.content_lay_v.addWidget(self.coll_folder_list_input)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        self.content_lay_v.addStretch()

        btns_wid = QWidget()
        btns_layout = LayoutHor()
        btns_wid.setLayout(btns_layout)
        self.content_lay_v.addWidget(btns_wid)

        btns_layout.addStretch(1)

        self.ok_btn = Btn(Dynamic.lng.ok)
        self.ok_btn.setFixedSize(90, self.ok_btn.height())
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        btns_layout.addWidget(self.ok_btn)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        self.cancel_btn = Btn(Dynamic.lng.cancel)
        self.cancel_btn.setFixedSize(90, self.cancel_btn.height())
        self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
        btns_layout.addWidget(self.cancel_btn)

        btns_layout.addStretch(1)

    def reload_ui(self):
        MainUtils.clear_layout(self.content_lay_v)
        self.init_ui()

    def cancel_cmd(self, *args):
        self.close()

    def ok_cmd(self, e):
        coll_folder_list = self.coll_folder_list_input.get_text()
        stop_colls = self.stopcolls.get_stopcolls()

        if hasattr(self.restore_db_btn, "flag"):
            print("settings win restore db")
            JsonData.write_json_data()
            QApplication.quit()
            Dbase.copy_db_file()
            MainUtils.start_new_app()

        elif hasattr(self.change_lang, "flag"):
            print("settings win change lang")
            JsonData.dynamic_set_lang(self.change_lang.lang)
            JsonData.write_json_data()
            QApplication.quit()
            MainUtils.start_new_app()

        elif stop_colls != JsonData.stop_colls:
            print("settings win stop colls updated")
            JsonData.stop_colls = stop_colls
            Scaner.app.stop()
            Scaner.app.start()
            JsonData.write_json_data()

        elif coll_folder_list != JsonData.coll_folder_list:
            print("settings win coll folder list updated")
            JsonData.coll_folder_list = coll_folder_list
            Scaner.app.stop()
            Scaner.app.start()
            JsonData.write_json_data()

        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
