from math import ceil

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QGridLayout, QScrollArea, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils

from .above_thumbs import AboveThumbs, AboveThumbsNoImages
from .limit_btn import LimitBtn
from .thumbnail import Thumbnail
from .thumbs_dict import ThumbsDict
from .title import Title
from .up_btn import UpBtn


class Thumbnails(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.resize(cnf.root_g["aw"] - cnf.MENU_W, cnf.root_g["ah"])
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

        self.first_load = True
        self.init_ui()

        frame_layout.addStretch(1)

        self.setWidget(self.scroll_area_widget)

        self.resize_timer = QTimer(self)
        self.resize_timer.setInterval(500)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.reload_thumbnails)
        self.first_load = True

        gui_signals_app.reload_thumbnails.connect(self.reload_thumbnails)
        gui_signals_app.scroll_top.connect(self.scroll_top)

    def checkScrollValue(self, value):
        if self.height() == 0:
            return
        else:
            self.up_btn.move(
                self.width() - 60,
                self.height() - 60 + value
                )
            self.up_btn.setVisible(value > 0)
            self.up_btn.raise_()

    def scroll_top(self):
        self.verticalScrollBar().setValue(0)

    def init_ui(self):
        self.up_btn = UpBtn(self.scroll_area_widget)
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

        thumbs_dict = ThumbsDict()
        cnf.images.clear()

        if thumbs_dict:
            above_thumbs = AboveThumbs(self.width())
            self.thumbnails_layout.addWidget(above_thumbs)

            for month, images_data in thumbs_dict.items():
                self.create_one_grid(month, images_data)

        else:
            no_images = AboveThumbsNoImages(self.width())
            self.thumbnails_layout.addWidget(no_images)

        ln_thumbs = sum(len(lst) for lst in thumbs_dict.values())
        if ln_thumbs == cnf.current_limit:
            h_layout = LayoutH()
            h_layout.setContentsMargins(0, 0, 0, 10)
            self.thumbnails_layout.addLayout(h_layout)
            h_layout.addWidget(LimitBtn())

    def reload_thumbnails(self):
        if self.first_load:
            self.first_load = False
        else:
            MainUtils.clear_layout(self.thumbnails_layout)
            self.up_btn.deleteLater()
            self.init_ui()

    def create_one_grid(self, month, images_data):
        title_label = Title(month, [i[-1] for i in images_data], self.width())
        self.thumbnails_layout.addWidget(title_label)

        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignLeft)
        grid_layout.setContentsMargins(0, 0, 0, 30)

        ww = self.width()
        
        if not cnf.zoom:
            columns = max(ww // (cnf.THUMBSIZE), 1)
        else:
            columns = max(ww // (cnf.ZOOMED_THUMBSIZE), 1)

        # Добавляем изображения в сетку
        for idx, (byte_array, img_src) in enumerate(images_data):
            label = Thumbnail(
                byte_array=byte_array,
                img_src=img_src
                )
            grid_layout.addWidget(label, idx // columns, idx % columns)

        rows = ceil(len(images_data) / columns)
        grid_layout.setColumnStretch(columns, 1)
        grid_layout.setRowStretch(rows, 1)

        self.thumbnails_layout.addLayout(grid_layout)

    def resizeEvent(self, e: QEvent):
        self.resize_timer.stop()
        self.resize_timer.start()

        self.up_btn.setVisible(False)