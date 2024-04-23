import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QFileDialog, QLabel, QSizePolicy, QSpacerItem,
                             QWidget)

from base_widgets import Btn, LayoutH, LayoutV, WinStandartBase
from cfg import cnf
from signals import utils_signals_app
from utils import MainUtils


class Manager:
    coll_folder = cnf.coll_folder


class BrowseColl(LayoutV):
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        descr = QLabel(cnf.lng.choose_coll_smb)
        self.addWidget(descr)
        
        self.addSpacerItem(QSpacerItem(0, 5))

        self.h_wid = QWidget()
        self.h_wid.setFixedSize(375, 60)
        self.addWidget(self.h_wid)

        h_layout = LayoutH()
        self.h_wid.setLayout(h_layout)

        self.browse_btn = Btn(cnf.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        h_layout.addWidget(self.browse_btn)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel()

        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setText(self.cut_text(text=Manager.coll_folder))
        h_layout.addWidget(self.coll_path_label)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

    def cut_text(self, text: str, limit: int = 130):
        if len(text) > limit:
            return text[:limit] + "..."
        return text

    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if not os.path.exists(Manager.coll_folder):
            file_dialog.setDirectory(cnf.down_folder)
        else:
            file_dialog.setDirectory(Manager.coll_folder)

        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            self.changed.emit()
            Manager.coll_folder = selected_folder
            self.coll_path_label.setText(self.cut_text(text=Manager.coll_folder))

    def finalize(self):        
        cnf.coll_folder = Manager.coll_folder

        utils_signals_app.watcher_stop.emit()
        utils_signals_app.watcher_start.emit()

        utils_signals_app.scaner_stop.emit()
        utils_signals_app.scaner_start.emit()


class WinSmb(WinStandartBase):
    def __init__(self, parent = None):
        MainUtils.close_same_win(WinSmb)

        super().__init__(close_func=self.cancel_cmd)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.set_title(cnf.lng.no_connection)
        self.disable_min_max()

        self.init_ui()
        self.setFixedSize(375, 170)
        self.center_win(parent=parent)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def cancel_cmd(self, event):
        pass

    def init_ui(self):
        self.browse_coll = BrowseColl()
        self.content_layout.addLayout(self.browse_coll)
        self.content_layout.addSpacerItem(QSpacerItem(0, 20))
        self.content_layout.addStretch()
        self.ok_btn = Btn(cnf.lng.ok)
        self.ok_btn.setDisabled(True)
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        self.content_layout.addWidget(self.ok_btn, alignment=Qt.AlignCenter)

        self.browse_coll.changed.connect(self.on_coll_changed)

    def on_coll_changed(self):
        self.adjustSize()
        self.ok_btn.setDisabled(False)

    def reload_ui(self):
        MainUtils.clear_layout(self.content_layout)
        self.init_ui()

    def ok_cmd(self, e):
        self.browse_coll.finalize()
        # print("finalize disabled")

        self.delete_win.emit()
        self.deleteLater()

    def keyPressEvent(self, event):
        event.ignore()
