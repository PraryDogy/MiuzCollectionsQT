from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QLabel, QProgressBar, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import Btn, LayoutV, WinStandartBase
from styles import Names, Themes
from utils import MainUtils
from cfg import cnf

class Threads:
    threads_list: list = [i for i in range(0, 10)]



class DownloadsWin(WinStandartBase):
    cancel_pressed = pyqtSignal()

    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.my_close)
        self.set_title("Заменить заголовок")
        self.disable_min()
        self.disable_max()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(400, 420)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName(Names.th_scrollbar)
        self.scroll_area.setStyleSheet(Themes.current)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName(Names.th_scroll_widget)
        self.scroll_widget.setStyleSheet(Themes.current)
        self.scroll_area.setWidget(self.scroll_widget)

        self.v_layout = LayoutV()
        self.scroll_widget.setLayout(self.v_layout)

        self.content_layout.addWidget(self.scroll_area)

        for i in Threads.threads_list:
            self.add_progress()

    def add_progress(self):
        main = QWidget(parent=self.scroll_widget)
        # main.setFixedHeight(50)
        v_layout = LayoutV()
        v_layout.setContentsMargins(10, 0, 20, 0)
        main.setLayout(v_layout)

        label = QLabel(text="Заменить текст", parent=main)
        label.setFixedHeight(15)
        v_layout.addWidget(label)

        self.progress = QProgressBar(parent=main)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        v_layout.addWidget(self.progress)

        v_layout.addSpacerItem(QSpacerItem(0, 10))

        self.cancel_btn = Btn(text=cnf.lng.cancel)
        self.cancel_btn.mouseReleaseEvent = self.cancel_btn_cmd
        v_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.v_layout.addWidget(main)

    def my_close(self, event):
        self.close()
        return

    def cancel_btn_cmd(self, e):
        self.cancel_pressed.emit()
        self.close()

    def set_value(self, value: int):
        try:
            self.progress.setValue(value)
        except (Exception, RuntimeError) as e:
            MainUtils.print_err(parent=self, error=e)
