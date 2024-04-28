from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QProgressBar, QSpacerItem

from base_widgets import Btn, WinStandartBase
from cfg import cnf
from utils import CopyFilesThread, MainUtils

from ..win_smb import WinSmb


class Manager:
    win_smb: WinSmb = None


class WinCopyFilesThread(WinStandartBase, QObject):
    finished = pyqtSignal()

    def __init__(self, files: list, dest: str):
        super().__init__(close_func=self.my_close)
        self.set_title(cnf.lng.copying_title)
        self.disable_min_max()
        self.setFixedSize(270, 130)

        label = QLabel(cnf.lng.copying_files)
        label.setFixedHeight(15)
        self.content_layout.addWidget(label)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.content_layout.addWidget(self.progress)

        self.content_layout.addSpacerItem(QSpacerItem(0, 10))

        cancel = Btn(cnf.lng.cancel)
        cancel.mouseReleaseEvent = self.cancel_cmd
        self.content_layout.addWidget(cancel, alignment=Qt.AlignRight)

        self.center_win()

        if not MainUtils.smb_check():
            self.deleteLater()
            Manager.win_smb = WinSmb()
            Manager.win_smb.show()
            return

        self.show()

        self.copy_thread = CopyFilesThread()
        self.copy_thread.value.connect(self.update_progress)
        self.copy_thread.finished.connect(self.finalize)
        self.copy_thread.set_sources(dest,files)

        try:
            self.copy_thread.start()
        except Exception as e:
            self.finalize()
            print("copy files error")
            print(e)

    def keyPressEvent(self, event):
        event.ignore()

    def my_close(self, event):
        event.ignore()

    def cancel_cmd(self, e):
        self.copy_thread.stop.emit()
        self.deleteLater()

    def update_progress(self, progress_percentage):
        self.progress.setValue(progress_percentage)

    def finalize(self):
        self.finished.emit()
        self.deleteLater()        

    def center_win(self):
        parent = MainUtils.get_central_widget()
        geo = self.geometry()
        geo.moveCenter(parent.geometry().center())
        self.setGeometry(geo)
