import os

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel

from system.shared_utils import ImgUtils
from system.utils import Utils

from ._base_widgets import UMainWindow


class WinImgSearch(UMainWindow):
    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setAcceptDrops(True)
        self.setFixedSize(500, 500)

        self.img_label = QLabel()
        self.central_layout.addWidget(self.img_label)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            first_url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if first_url.endswith(ImgUtils.ext_all):
                img_array = ImgUtils.read_img(first_url)
                img_array = ImgUtils.resize(img_array, 450)
                qimage = Utils.qimage_from_array(img_array)
                self.img_label.setPixmap(QPixmap.fromImage(qimage))
        return super().dropEvent(a0)