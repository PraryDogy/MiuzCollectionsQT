from math import ceil

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QGridLayout, QScrollArea, QWidget

from base_widgets import LayoutH, LayoutV
from cfg import cnf
from signals import gui_signals_app
from styles import Styles
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
        self.resize(cnf.root_g["aw"] - Styles.menu_w, cnf.root_g["ah"])

        self.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {Styles.thumbs_bg_color};
                border: 0px;
                border-radius: 0px;
            }}
            """)

        # if MainUtils.get_mac_ver() <= 10.15:
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Создаем фрейм для виджетов в области скролла
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_bg_color}
            """)

        self.up_btn = UpBtn(self.scroll_area_widget)
        self.up_btn.setVisible(False)
        self.verticalScrollBar().valueChanged.connect(self.checkScrollValue)

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
        self.up_btn.move(
            self.width() - 65,
            self.height() - 60 + value
            )
        self.up_btn.setVisible(value > 0)
        self.up_btn.raise_()

    def scroll_top(self):
        self.verticalScrollBar().setValue(0)

    def init_ui(self):
        thumbs_dict = ThumbsDict()
        cnf.images.clear()

        if thumbs_dict:
            self.thumbnails_layout.addLayout(AboveThumbs(self.width()))

            for month, images_data in thumbs_dict.items():
                self.create_one_grid(month, images_data)

        else:
            self.thumbnails_layout.addLayout(AboveThumbsNoImages(self.width()))

        ln_thumbs = sum(len(lst) for lst in thumbs_dict.values())
        if ln_thumbs == cnf.current_limit:
            h_layout = LayoutH()
            h_layout.setContentsMargins(0, 0, 0, 10)
            self.thumbnails_layout.addLayout(h_layout)
            h_layout.addWidget(LimitBtn())

        self.up_btn.raise_()

    def reload_thumbnails(self):
        if self.first_load:
            self.first_load = False
        else:
            self.scroll_area_widget.hide()
            MainUtils.clear_layout(self.thumbnails_layout)
            self.init_ui()
            self.scroll_area_widget.show()

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
