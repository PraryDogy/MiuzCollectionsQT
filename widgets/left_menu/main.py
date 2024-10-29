import sqlalchemy
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QScrollArea, QWidget, QLabel, QSpacerItem

from base_widgets import LayoutH, LayoutV, Btn
from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils
from collections import defaultdict
from .collection_btn import CollectionBtn


class BaseLeftMenu(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setObjectName(Names.menu_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_widget.setObjectName(Names.menu_scrollbar_qwidget)
        scroll_widget.setStyleSheet(Themes.current)
        self.setWidget(scroll_widget)

        self.v_layout = LayoutV()
        scroll_widget.setLayout(self.v_layout)
        self.init_ui()
        gui_signals_app.reload_menu.connect(self.reload_menu)

    def init_ui(self):
        btns_widget = QWidget()
        main_btns_layout = LayoutV()
        btns_widget.setLayout(main_btns_layout)

        main_btns_layout.setContentsMargins(0, 5, 0, 15)

        label = CollectionBtn(parent=self, fake_name=cnf.lng.all_colls,
                              true_name=cnf.ALL_COLLS)
        main_btns_layout.addWidget(label)

        self.v_layout.addWidget(btns_widget)

        if cnf.small_menu_view:
            for letter, collections in self.load_colls_query().items():
                for coll in collections:
                    label = CollectionBtn(parent=self, fake_name=coll["fake_name"], true_name=coll["true_name"])
                    self.v_layout.addWidget(label)
        else:
            for letter, collections in self.load_colls_query().items():

                test = QLabel(text=letter)
                test.setContentsMargins(6, 20, 0, 5)
                test.setObjectName(Names.letter_btn)
                test.setStyleSheet(Themes.current)
                self.v_layout.addWidget(test)

                for coll in collections:
                    label = CollectionBtn(parent=self, fake_name=coll["fake_name"], true_name=coll["true_name"])
                    self.v_layout.addWidget(label)

        self.v_layout.addSpacerItem(QSpacerItem(0, 5))
        self.v_layout.addStretch(1)

    def change_view(self):
        cnf.small_menu_view = not cnf.small_menu_view
        gui_signals_app.reload_menu.emit()

    def load_colls_query(self) -> dict:
        menus = defaultdict(list)
        
        q = sqlalchemy.select(ThumbsMd.collection).distinct()

        session = Dbase.get_session()
        try:
            res = (i[0] for i in session.execute(q).fetchall() if i)
        finally:
            session.close()

        for true_name in res:
            fake_name = true_name.lstrip("0123456789").strip()
            fake_name = fake_name if fake_name else true_name
            letter = fake_name[0].capitalize()

            menus[letter].append({"fake_name": fake_name, "true_name": true_name})

        return {
            key: sorted(value, key=lambda x: x['fake_name'])
            for key, value in sorted(menus.items())
            }

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
