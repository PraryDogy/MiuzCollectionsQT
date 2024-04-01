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
        self.addWidget(h_wid)

        h_layout = LayoutH()
        h_wid.setLayout(h_layout)

        self.browse_btn = Btn(cnf.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        h_layout.addWidget(self.browse_btn)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel(Manager.coll_folder)
        self.coll_path_label.setWordWrap(True)
        self.set_label_h()
        h_layout.addWidget(self.coll_path_label)

    def set_label_h(self):
        lbl_h = 30
        num_lines = self.coll_path_label.text().count('\n') + 1
        self.coll_path_label.setFixedHeight(lbl_h * num_lines)

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
            self.coll_path_label.setText(Manager.coll_folder)
        
        self.set_label_h()

    def finalize(self):
        cnf.coll_folder = Manager.coll_folder

        utils_signals_app.watcher_stop.emit()
        utils_signals_app.watcher_start.emit()

        utils_signals_app.scaner_stop.emit()
        utils_signals_app.scaner_start.emit()

class WinSmb(WinStandartBase):
    def __init__(self):
        MainUtils.close_same_win(WinSmb)

        super().__init__(close_func=self.cancel_cmd)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.set_title(cnf.lng.no_connection)
        self.disable_min_max()

        self.resize(320, 150)
        self.init_ui()
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
        self.browse_coll = BrowseColl()
        self.content_layout.addLayout(self.browse_coll)

        self.content_layout.addSpacerItem(QSpacerItem(0, 20))

        self.ok_btn = Btn(cnf.lng.ok)
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        self.content_layout.addWidget(self.ok_btn, alignment=Qt.AlignCenter)

    def reload_ui(self):
        MainUtils.clear_layout(self.content_layout)
        self.init_ui()

    def ok_cmd(self, e):
        self.browse_coll.finalize()

        self.delete_win.emit()
        self.deleteLater()

    def keyPressEvent(self, event):
        event.ignore()

    def resizeEvent(self, event):
        self.browse_coll.set_label_h()
        return super().resizeEvent(event)