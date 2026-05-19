import sys

import numpy as np
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPen, QPixmap
from PyQt5.QtWidgets import (QApplication, QGraphicsPixmapItem,
                             QGraphicsRectItem, QGraphicsScene,
                             QGraphicsTextItem, QGraphicsView, QHBoxLayout,
                             QLabel, QPushButton, QVBoxLayout, QWidget)

from system.shared_utils import ImgUtils
from system.utils import Utils
from widgets._base_widgets import UMainWindow
from widgets.win_image_view import WinImageView
import os

class CropView(QGraphicsView):
    min_ww, min_hh = 300, 260
    def __init__(self):
        super().__init__()
        self.setMinimumSize(self.min_ww, self.min_hh)
        self.setAcceptDrops(True)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None
        self.image_np = None
        self.origin = QPointF()
        self.crop_rect_item = QGraphicsRectItem()
        self.scene.addItem(self.crop_rect_item)
        self.dragging = False

        lines = (
            "Перетащите изображение сюда.",
            "Выделите область изображения для поиска.",
            "Если ничего не нашлось, попробуйте уменьшить область."
        )

        self.placeholder = QGraphicsTextItem("\n".join(lines))
        self.placeholder.setDefaultTextColor(
            QColor(150, 150, 150)
        )
        font = QFont()
        font.setPointSize(14)
        self.placeholder.setFont(font)
        self.scene.addItem(self.placeholder)
        self.update_placeholder_pos()

    def get_crop_numpy(self) -> np.ndarray:
        rect = self.crop_rect_item.rect()
        x1 = int(rect.left())
        y1 = int(rect.top())
        x2 = int(rect.right())
        y2 = int(rect.bottom())
        h, w = self.image_np.shape[:2]
        x1 = max(0, min(w, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h, y1))
        y2 = max(0, min(h, y2))
        return self.image_np[y1:y2, x1:x2]

    def update_placeholder_pos(self):
        view_rect = self.mapToScene(
            self.viewport().rect()
        ).boundingRect()

        text_rect = self.placeholder.boundingRect()

        self.placeholder.setPos(
            view_rect.center().x() - text_rect.width() / 2,
            view_rect.center().y() - text_rect.height() / 2
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return
        path = event.mimeData().urls()[0].toLocalFile()
        if not os.path.isfile(path):
            return
        if not path.endswith(ImgUtils.ext_all):
            return
        self.placeholder.hide()
        self.image_np = ImgUtils.read_img(path)
        qimage = Utils.qimage_from_array(self.image_np)
        pixmap = QPixmap.fromImage(qimage)
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.crop_rect_item = QGraphicsRectItem()
        blue = QColor(70, 130, 240)
        pen = QPen(blue)
        pen.setWidth(2)
        self.crop_rect_item.setPen(pen)
        self.scene.addItem(self.crop_rect_item)
        self.setSceneRect(QRectF(pixmap.rect()))
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if self.pixmap_item is None:
            return
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.origin = self.mapToScene(event.pos())
            self.crop_rect_item.setRect(
                QRectF(self.origin, self.origin)
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self.origin, current_pos).normalized()
            self.crop_rect_item.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.update_placeholder_pos()


class CropWin(UMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(500, 500)

        above_bar = QWidget()
        self.central_layout.addWidget(above_bar)
        above_layout = QHBoxLayout(above_bar)
        above_layout.setContentsMargins(0, 0, 0, 0)

        self.ok_btn = QPushButton("Применить")
        above_layout.addWidget(self.ok_btn)

        self.crop_view = CropView()
        self.central_layout.addWidget(self.crop_view)

    def show_crop(self):
        self.crop_array = self.crop_view.get_crop_numpy()
        self.crop_qimage = Utils.qimage_from_array(self.crop_array)
        self.crop_pixmap = QPixmap.fromImage(self.crop_qimage)
        self.crop_pixmap = Utils.qiconed_resize(self.crop_pixmap, 500)
        self.test = QLabel()
        self.test.setPixmap(self.crop_pixmap)
        self.test.show()

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.show_crop()

        return super().keyPressEvent(a0)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = CropWin()
    window.show()

    sys.exit(app.exec_())