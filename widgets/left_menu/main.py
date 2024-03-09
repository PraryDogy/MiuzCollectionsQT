import sqlalchemy
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QWidget, QFrame

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from database import Queries, ThumbsMd
from signals import gui_signals_app
from styles import Styles
from utils import MainUtils

from .collection_btn import CollectionBtn


class BaseLeftMenu(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)

        self.setStyleSheet(
            f"""
            QScrollArea {{
                border: 0px;
            }}
            """)

        if MainUtils.get_mac_ver() <= 10.15:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet(
            f"""
            background-color: {Styles.menu_bg_color};
            border: 0px;
            """)
        self.setWidget(self.scroll_widget)

        self.v_layout = LayoutV()
        self.scroll_widget.setLayout(self.v_layout)
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
        res = Queries.get_query(query=q).fetchall()
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # 
        # 
        # res = res[:10]

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
        self.setFixedWidth(Styles.menu_w)

        h_lay = LayoutH()
        self.setLayout(h_lay)

        fake = QFrame()
        fake.setFixedWidth(10)
        fake.setStyleSheet(
            f"""
            border: 0px;
            background-color: {Styles.menu_bg_color};
            border-bottom-left-radius: {Styles.base_radius}px;
            """)
        h_lay.addWidget(fake)

        menu = BaseLeftMenu()
        h_lay.addWidget(menu)
