import os

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton

from system.shared_utils import ImgUtils
from system.tasks import ImageSearcher, UThreadPool
from system.utils import Utils
from cfg import Dynamic
from ._base_widgets import UMainWindow


class WinImgSearch(UMainWindow):
    finished_ = pyqtSignal(set)


    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setAcceptDrops(True)
        self.setFixedSize(500, 500)

        self.img_array = None

        self.img_label = QLabel()
        self.central_layout.addWidget(self.img_label)

        self.start_btn = QPushButton("start")
        self.start_btn.clicked.connect(self.start_image_searcher)
        self.central_layout.addWidget(self.start_btn)

    def start_image_searcher(self):
        if self.img_array is None:
            return
        self.image_searcher = ImageSearcher(self.img_array, max_side=450)
        self.image_searcher.sigs.finished_.connect(self.finished)
        UThreadPool.start(self.image_searcher)

    def finished(self, thumb_names_list: set[str]):
        for i in thumb_names_list:
            print(i)

        Dynamic.thumb_path_set = thumb_names_list
        self.finished_.emit(thumb_names_list)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            first_url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if first_url.endswith(ImgUtils.ext_all):
                self.img_array = ImgUtils.read_img(first_url)
                # self.img_array = ImgUtils.resize(self.img_array, 450)
                qimage = Utils.qimage_from_array(self.img_array)
                qimage = qimage.scaled(450, 450, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
                self.img_label.setPixmap(QPixmap.fromImage(qimage))
        return super().dropEvent(a0)
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    
# чтение изображения в фоне
# решить где ресайз
# отправлять в таск только путь?
# как прервать задачу закрытием
# когда очищать список динамик
# при закрытии очищать и при отображении сетки очищать