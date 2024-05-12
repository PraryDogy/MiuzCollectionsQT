import os
import subprocess

from PyQt5.QtWidgets import QAction, QFrame, QLabel

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Styles, default_theme


class CustomContext(ContextMenuBase):
    def __init__(self, parent: QLabel, true_name, event):
        super().__init__(event=event)

        self.true_name = true_name

        view_coll = self.addAction(cnf.lng.view)
        view_coll.triggered.connect(lambda e: self.show_collection())

        self.addSeparator()

        action_text = f"{cnf.lng.reveal} {cnf.lng.in_finder}"
        reveal_menu = ContextSubMenuBase(self, action_text)
        self.addMenu(reveal_menu)

        base_coll = QAction(cnf.lng.collection)
        base_coll.triggered.connect(lambda e: self.reveal_collection("base"))
        reveal_menu.addAction(base_coll)

        reveal_menu.addSeparator()

        prod_coll = QAction(cnf.lng.cust_fltr_names["prod"])
        prod_coll.triggered.connect(lambda e: self.reveal_collection("prod"))
        reveal_menu.addAction(prod_coll)


        mod_coll = QAction(cnf.lng.cust_fltr_names["mod"])
        mod_coll.triggered.connect(lambda e: self.reveal_collection("mod"))
        reveal_menu.addAction(mod_coll)

        if parent.objectName() == Names.menu_btn:
            try:
                parent.setObjectName(Names.menu_btn_bordered)
                parent.setStyleSheet(default_theme)
                self.show_menu()
                parent.setObjectName(Names.menu_btn)
                parent.setStyleSheet(default_theme)
            except Exception as e:
                print(e)

        else:
            try:
                parent.setObjectName(Names.menu_btn_selected_bordered)
                parent.setStyleSheet(default_theme)
                self.show_menu()
                parent.setObjectName(Names.menu_btn_selected)
                parent.setStyleSheet(default_theme)
            except Exception as e:
                print(e)

    def show_collection(self):
        cnf.curr_coll = self.true_name
        gui_signals_app.reload_title.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

    def reveal_collection(self, flag):
        if self.true_name in (cnf.ALL_COLLS, cnf.RECENT_COLLS):
            subprocess.Popen(["open", cnf.coll_folder])
            return

        coll_path = os.path.join(cnf.coll_folder, self.true_name)

        if flag == "base":
            subprocess.Popen(["open", coll_path])

        elif flag == "prod":
            new_path = os.path.join(coll_path, cnf.cust_fltr_names[flag])
            subprocess.Popen(["open", new_path])

        elif flag == "mod":
            new_path = os.path.join(coll_path, cnf.cust_fltr_names[flag])
            subprocess.Popen(["open", new_path])


class CollectionBtn(QLabel):
    def __init__(self, parent: QFrame, fake_name: str, true_name: str):
        super().__init__(text=fake_name)
        self.true_name = true_name
        self.fake_name = fake_name

        btn_w = Styles.menu_w - 20 - 5
        self.setFixedSize(btn_w, 28)

        if true_name == cnf.curr_coll:
            self.setObjectName(Names.menu_btn_selected)
        else:
            self.setObjectName(Names.menu_btn)

        self.setStyleSheet(default_theme)

    def mouseReleaseEvent(self, event):
        self.load_collection()

    def load_collection(self):
        cnf.curr_coll = self.true_name
        cnf.current_limit = cnf.LIMIT
        gui_signals_app.reload_title.emit()
        gui_signals_app.scroll_top.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()
            
    def contextMenuEvent(self, event):
        CustomContext(parent=self, true_name=self.true_name, event=event)

    def enterEvent(self, event):
        super().enterEvent(event)

        if self.true_name in ((cnf.ALL_COLLS, cnf.RECENT_COLLS)):
            return

        self.setToolTip(self.true_name)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.setToolTip("")