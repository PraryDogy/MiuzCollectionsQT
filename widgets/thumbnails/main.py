from math import ceil

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QGridLayout, QScrollArea, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils

from .above_thumbs import AboveThumbs, AboveThumbsNoImages
from .limit_btn import LimitBtn
from .images_dict_db import ImagesDictDb
from .thumbnail import Thumbnail
from .title import Title
from .up_btn import UpBtn


class Thumbnails(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.resize(cnf.root_g["aw"] - cnf.MENU_W, cnf.root_g["ah"])
        self.ww = cnf.root_g["aw"] - cnf.MENU_W
        self.horizontalScrollBar().setDisabled(True)

        self.setObjectName(Names.th_scrollbar)
        self.setStyleSheet(Themes.current)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Создаем фрейм для виджетов в области скролла
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setObjectName(Names.th_scroll_widget)
        self.scroll_area_widget.setStyleSheet(Themes.current)
        
        # Основной лейаут фрейма в области скролла
        frame_layout = LayoutV(self.scroll_area_widget)

        self.thumbnails_layout = LayoutV()
        self.thumbnails_layout.setContentsMargins(5, 10, 5, 0)
        frame_layout.addLayout(self.thumbnails_layout)

        self.columns = self.get_columns()
        self.init_ui()

        frame_layout.addStretch(1)
        self.setWidget(self.scroll_area_widget)

        gui_signals_app.reload_thumbnails.connect(self.reload_thumbnails)
        gui_signals_app.scroll_top.connect(self.scroll_top)
        gui_signals_app.move_to_wid.connect(self.move_to_wid)

    def checkScrollValue(self, value):
        self.up_btn.move(
            self.width() - 60,
            self.height() - 60 + value
            )
        self.up_btn.setVisible(value > 0)
        self.up_btn.raise_()

    def scroll_top(self):
        self.verticalScrollBar().setValue(0)

    def init_ui(self):
        thumbs_dict = ImagesDictDb()
        cnf.images.clear()

        if thumbs_dict:
            above_thumbs = AboveThumbs(self.width())
            self.thumbnails_layout.addWidget(above_thumbs)

            for some_date, images_list in thumbs_dict.items():
                self.images_grid(some_date, images_list)

        else:
            no_images = AboveThumbsNoImages(self.width())
            self.thumbnails_layout.addWidget(no_images)

        ln_thumbs = sum(len(lst) for lst in thumbs_dict.values())
        if ln_thumbs == cnf.current_limit:
            h_layout = LayoutH()
            h_layout.setContentsMargins(0, 0, 0, 10)
            self.thumbnails_layout.addLayout(h_layout)
            h_layout.addWidget(LimitBtn())

        self.up_btn = UpBtn(self.scroll_area_widget)
        self.up_btn.setVisible(False)
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

    def reload_thumbnails(self):
        MainUtils.clear_layout(self.thumbnails_layout)
        self.up_btn.deleteLater()
        self.init_ui()

    def images_grid(self, images_date: str, images_list: list[dict]):
        """
            images_date: "date start - date fin / month year"
            images_list: [ {"img": img byte_array, "src": img_src, "coll": coll}, ... ]
        """

        img_src_list = [img_dict["src"] for img_dict in images_list]
        title_label = Title(title=images_date, images=img_src_list, width=self.width())
        self.thumbnails_layout.addWidget(title_label)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignLeft)
        grid_layout.setContentsMargins(0, 0, 0, 30)

        idx = 0

        for img_dict in images_list:
            label = Thumbnail(
                byte_array=img_dict["img"],
                img_src=img_dict["src"],
                coll=img_dict["coll"],
                images_date=images_date
                )
            grid_layout.addWidget(label, idx // self.columns, idx % self.columns)

            idx += 1

        # rows = ceil(len(images_list) / self.columns)
        # grid_layout.setColumnStretch(self.columns, 1)
        # grid_layout.setRowStretch(rows, 1)
        self.thumbnails_layout.addLayout(grid_layout)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.up_btn.setVisible(False)

        if abs(a0.size().width() - self.ww) > cnf.THUMBSIZE:
            self.ww = a0.size().width()
            new_columns = self.get_columns()
            self.columns = new_columns
            self.reload_thumbnails()
            self.resize(a0.size().width(), self.height())
        return super().resizeEvent(a0)

    def get_columns(self):
        return max(self.width() // (cnf.THUMBSIZE + cnf.THUMBPAD), 1)
    
    def move_to_wid(self, wid):
        self.ensureWidgetVisible(wid)