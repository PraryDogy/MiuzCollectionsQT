import sqlalchemy
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QScrollArea, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils

from .collection_btn import CollectionBtn


class BaseLeftMenu(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setObjectName(Names.menu_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        # scroll_widget.setObjectName(Names.menu_scrollbar_qwidget)
        # scroll_widget.setStyleSheet(Themes.current)
        self.setWidget(scroll_widget)

        self.v_layout = LayoutV()
        scroll_widget.setLayout(self.v_layout)
        self.init_ui()
        gui_signals_app.reload_menu.connect(self.reload_menu)

    def init_ui(self):
        main_btns_layout = LayoutV()
        main_btns_layout.setContentsMargins(0, 5, 0, 15)

        label = CollectionBtn(parent=self, fake_name=cnf.lng.all_colls,
                              true_name=cnf.ALL_COLLS)
        main_btns_layout.addWidget(label)


        label = CollectionBtn(parent=self, fake_name=cnf.lng.recents,
                              true_name=cnf.RECENT_COLLS)
        main_btns_layout.addWidget(label)

        self.v_layout.addLayout(main_btns_layout)

        for fake_name, true_name in self.load_colls_query().items():
            label = CollectionBtn(parent=self, fake_name=fake_name, true_name=true_name)
            self.v_layout.addWidget(label)

        self.v_layout.addStretch(1)

    def load_colls_query(self) -> dict:
        menus = {}
        
        q = sqlalchemy.select(ThumbsMd.collection).distinct()

        session = Dbase.get_session()
        try:
            res = session.execute(q).fetchall()
        finally:
            session.close()

        for i in res:
            if not i:
                continue
            fakename = i[0].lstrip("0123456789").strip()
            fakename = fakename if fakename else i[0]
            menus[fakename] = i[0]
        
        sort_keys = sorted(menus.keys())

        return {fake_name: menus[fake_name] for fake_name in sort_keys}

    def reload_menu(self):
        MainUtils.clear_layout(self.v_layout)
        self.init_ui()


class LeftMenu(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(cnf.MENU_W)

        h_lay = LayoutH()
        self.setLayout(h_lay)

        fake = QFrame()
        fake.setFixedWidth(10)
        fake.setObjectName("menu_fake_widget")
        fake.setStyleSheet(Themes.current)
        h_lay.addWidget(fake)

        menu = BaseLeftMenu()
        h_lay.addWidget(menu)
