import sys

import numpy as np
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QPixmap
from PyQt5.QtWidgets import (QApplication, QGraphicsPixmapItem,
                             QGraphicsRectItem, QGraphicsScene, QGraphicsView,
                             QMainWindow)

from system.shared_utils import ImgUtils
from system.utils import Utils
from widgets.win_image_view import WinImageView


def load_image_to_numpy(path: str) -> np.ndarray:
    img = ImgUtils.read_img(path)
    return img


class CropView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = None
        self.image_np = None

        self.origin = QPointF()
        self.crop_rect_item = QGraphicsRectItem()

        blue = QColor(70, 130, 240)
        pen = QPen(blue)
        pen.setWidth(2)

        self.crop_rect_item.setPen(pen)
        self.scene.addItem(self.crop_rect_item)

        self.dragging = False

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        path = event.mimeData().urls()[0].toLocalFile()

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

    # ==========================================
    # MOUSE
    # ==========================================
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

    def get_crop_numpy(self):
        if self.image_np is None:
            return None

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

        cropped = self.image_np[y1:y2, x1:x2]

        return cropped


# ==========================================
# MAIN WINDOW
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Cropper")
        self.resize(1200, 800)

        self.view = CropView()

        self.setCentralWidget(self.view)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            crop = self.view.get_crop_numpy()
            if crop is not None:
                print("Crop shape:", crop.shape)


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())