import os

from PyQt5.QtCore import QMimeData, Qt, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QDrag, QMouseEvent, QPixmap
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget

from cfg import Static
from system.utils import Utils

from ._base_widgets import UMenu


class PathItem(QWidget):
    min_wid = 5
    arrow_right = " \U0000203A" # ›
    height_ = 15

    def __init__(self, dir: str, name: str, path: str):
        """
        Этот виджет - часть группы виджетов PathItem, которые в сумме отображают
        указанный путь  
        Например: /путь/до/файла.txt    
        Указанный путь будет разбит на секции, которые отображаются в виде PathItem     
        Мы получим группу виджетов PathItem (имя - путь),   
        где каждый видждет PathItem будет кликабельным и открывать соответсвующий путь  
        путь - /путь    
        до - /путь/до   
        файла.txt - /путь/до/файла.txt  
        """
        super().__init__()
        self.path = path
        self.setFixedHeight(self.height_)
        self.dir = dir

        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(5)
        self.setLayout(item_layout)

        self.img_wid = QSvgWidget()
        self.img_wid.setFixedSize(15, 15)
        item_layout.addWidget(self.img_wid)
        
        self.text_wid = QLabel(text=name)
        self.collapse()
        item_layout.addWidget(self.text_wid)

    def add_arrow(self):
        """
        Добавляет к тексту виджета ">"
        """
        t = self.text_wid.text() + " " + PathItem.arrow_right
        self.text_wid.setText(t)

    def del_arrow(self):
        """
        Удаляет ">"
        """
        t = self.text_wid.text().replace(PathItem.arrow_right, "")
        self.text_wid.setText(t)

    def expand(self):
        """
        Показывает виджет в полную длину
        """
        self.text_wid.setFixedWidth(self.text_wid.sizeHint().width())
 
    def solid_style(self):
        """
        Выделяет виджет синим цветом
        """
        self.text_wid.setStyleSheet(
            f"""
                background: {Static.BLUE_GLOBAL};
                border-radius: 2px;
            """
        )

    def default_style(self):
        """
        Сбрасывает стиль
        """
        self.text_wid.setStyleSheet("")

    def collapse(self):
        """
        Схлопывает виджет до указанной минимальной длины, если
        виджет находится не под курсором мыши
        """
        if not self.text_wid.underMouse():
            self.text_wid.setMinimumWidth(self.min_wid)

    def enterEvent(self, a0):
        """
        Раскрывает виджет на всю его длину при наведении мыши
        """
        self.expand()

    def leaveEvent(self, a0):
        """
        Отложено схолпывает виджет до указанной минимальной длины
        """
        QTimer.singleShot(500, self.collapse)


class PathWidget(QWidget):
    last_item_limit = 40
    height_ = 25
    folder_icon = "./images/folder.svg"
    hdd_icon = "./images/hdd.svg"
    computer_icon = "./images/computer.svg"

    def __init__(self, path: str):
        """
        Нижний бар:     
        - Группа виджетов PathItem (читай описание PathItem)  
        """
        super().__init__()
        self.path = path
        self.setFixedHeight(PathWidget.height_)
        self.setAcceptDrops(True)
        self.current_path: str = None

        self.main_lay = QHBoxLayout()
        self.main_lay.setContentsMargins(0, 0, 0, 0)
        self.main_lay.setSpacing(5)
        self.main_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self.main_lay)

        self.update(path)

    def update(self, dir: str):
        """
        Отобразить новый путь сетки / папки / файла     
        src: путь сетки / папки / файла
        """
        if dir == self.current_path:
            return
        for i in self.findChildren(PathItem):
            i.deleteLater()
        self.current_path = dir
        root = dir.strip(os.sep).split(os.sep)
        path_items: dict[int, PathItem] = {}

        for x, name in enumerate(root, start=1):
            dir = os.path.join(os.sep, *root[:x])
            path_item = PathItem(dir, name, self.path)
            path_item.img_wid.load(self.folder_icon)
            path_item.add_arrow()
            path_items[x] = path_item
            self.main_lay.addWidget(path_item)

        path_items.get(1).img_wid.load(self.computer_icon)

        if path_items.get(2):
            path_items.get(2).img_wid.load(self.hdd_icon)

        last_item = path_items.get(len(root))

        if last_item:
            text_ = last_item.text_wid.text()
            if len(text_) > PathWidget.last_item_limit:
                path_item.text_wid.setText(text_[:PathWidget.last_item_limit] + "...")
            last_item.del_arrow()
            last_item.expand()
            last_item.enterEvent = lambda *args, **kwargs: None
            last_item.leaveEvent = lambda *args, **kwargs: None

