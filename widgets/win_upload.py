from collections import defaultdict

import sqlalchemy
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem

from base_widgets.wins import WinSystem
from database import THUMBS, Dbase
from utils.utils import URunnable, UThreadPool

from .menu_left import CollectionBtn, MenuLeft


class WorkerSignals(QObject):
    finished_ = pyqtSignal()


class CollectionsTask(URunnable):
    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):
        conn = Dbase.engine.connect()
        q = sqlalchemy.select(THUMBS.c.coll).distinct()
        res = conn.execute(q).fetchall()
        res = [i[0] for i in res]
        conn.close()
        # print(res)


class WinUpload(WinSystem):
    def __init__(self):
        super().__init__()

        self.menu_left = MenuLeft()
        self.central_layout.addWidget(self.menu_left)
        self.check_coll_btns()

    def check_coll_btns(self):
        any_tab = self.menu_left.menus[0]
        if len(any_tab.coll_btns) == 0:
            QTimer.singleShot(300, self.check_coll_btns)
        else:
            self.main()

    def main(self):
        
        for menu in self.menu_left.menus:

            disabled_btns = menu.coll_btns[:3]
            coll_btns = menu.coll_btns[3:]
            
            for i in disabled_btns:
                i.setDisabled(True)

            for i in coll_btns:
                i.pressed_.connect(lambda tt=i.text(): print(tt))