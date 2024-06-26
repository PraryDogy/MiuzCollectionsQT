import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QFileDialog, QLabel, QSpacerItem, QWidget

from base_widgets import Btn, LayoutH, LayoutV, WinStandartBase
from cfg import cnf
from signals import utils_signals_app
from styles import Names, Themes
from utils import MainUtils


class BrowseColl(QWidget):
    coll_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.coll_folder = cnf.coll_folder

        my_layout = LayoutV()
        self.setLayout(my_layout)

        descr = QLabel(cnf.lng.choose_coll_smb)
        my_layout.addWidget(descr)
        
        my_layout.addSpacerItem(QSpacerItem(0, 5))

        self.h_wid = QWidget()
        self.h_wid.setFixedSize(375, 60)
        my_layout.addWidget(self.h_wid)

        h_layout = LayoutH()
        self.h_wid.setLayout(h_layout)

        self.browse_btn = Btn(cnf.lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        h_layout.addWidget(self.browse_btn)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel()

        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setText(self.cut_text(text=self.coll_folder))
        h_layout.addWidget(self.coll_path_label)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.blue_count = 0

    def blue_browse_btn(self):
        try:
            self.browse_btn.setObjectName(Names.smb_browse_btn_selected)
            self.browse_btn.setStyleSheet(Themes.current)
                    
            QTimer.singleShot(200, self.default_browse_btn)
            self.blue_count += 1
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def default_browse_btn(self):
        try:
            self.browse_btn.setObjectName(Names.smb_browse_btn)
            self.browse_btn.setStyleSheet(Themes.current)
            
            if self.blue_count == 3:
                self.blue_count = 0
                return

            QTimer.singleShot(200, self.blue_browse_btn)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)


    def cut_text(self, text: str, limit: int = 130):
        if len(text) > limit:
            return text[:limit] + "..."
        return text

    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setViewMode(QFileDialog.ViewMode.List)

        file_dialog.setDirectory(cnf.down_folder)
        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            self.coll_changed.emit()
            self.coll_folder = selected_folder
            self.coll_path_label.setText(self.cut_text(text=self.coll_folder))

    def finalize(self):
        if self.coll_folder != cnf.coll_folder:
            cnf.old_coll_folder = cnf.coll_folder
            cnf.coll_folder = self.coll_folder
            utils_signals_app.scaner_stop.emit()
            utils_signals_app.scaner_start.emit()


class WinSmb(WinStandartBase):
    finished = pyqtSignal()

    def __init__(self, parent: QWidget):
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

    def pass_btn_cmd(self, event):
        self.finished.emit()
        self.close()

    def init_ui(self):
        self.browse_coll = BrowseColl()
        self.content_layout.addWidget(self.browse_coll)
        self.content_layout.addSpacerItem(QSpacerItem(0, 20))
        self.content_layout.addStretch()

        btns_layout = LayoutH()
        self.content_layout.addLayout(btns_layout)

        btns_layout.addStretch()

        self.ok_btn = Btn(cnf.lng.ok)
        self.ok_btn.mouseReleaseEvent = lambda e: self.browse_coll.blue_browse_btn()
        btns_layout.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        self.pass_btn = Btn(cnf.lng.close)
        self.pass_btn.mouseReleaseEvent = self.pass_btn_cmd
        btns_layout.addWidget(self.pass_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        btns_layout.addStretch()

        self.browse_coll.coll_changed.connect(self.on_coll_changed)

        self.browse_coll.blue_browse_btn()

    def on_coll_changed(self):
        self.adjustSize()
        self.ok_btn.mouseReleaseEvent = self.ok_cmd

    def reload_ui(self):
        MainUtils.clear_layout(self.content_layout)
        self.init_ui()

    def ok_cmd(self, e):
        self.browse_coll.finalize()
        self.finished.emit()
        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        return
        return super().keyPressEvent(a0)
