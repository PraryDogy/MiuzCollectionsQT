import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QFrame
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import numpy as np

class ReadDesatImage(QWidget):
    def __init__(self, src: str):
        super().__init__()

        img = cv2.imread(src, cv2.IMREAD_UNCHANGED)

        # Если изображение успешно загружено
        if img is not None:
            h, w, ch = img.shape
            bytesPerLine = ch * w
            qImg = QPixmap.fromImage(
                QImage(img.data, w, h, bytesPerLine, QImage.Format.Format_BGR888)
                )

            # Создание метки QLabel и отображение изображения
            label = QLabel(self)
            label.setPixmap(qImg)
            label.setAlignment(Qt.AlignCenter)


            qimage = qImg.toImage()

            # Преобразование QImage в массив numpy
            width = qimage.width()
            height = qimage.height()
            bytes_per_line = qimage.bytesPerLine()
            image_data = qimage.bits().asarray(height * bytes_per_line)

            # Создание массива numpy изображения
            image = np.array(image_data, dtype=np.uint8)
            image = image.reshape((height, width, 4)) 

            cv2.imshow("123", image)
            cv2.waitKey(0)

            return



            # Размещение метки в макете
            layout = QVBoxLayout()
            layout.addWidget(label)
            self.setLayout(layout)

        else:
            print("Не удалось загрузить изображение.")

src = "/Users/Loshkarev/Desktop/DSC_6795.jpg"
import os
plg = "/Users/Loshkarev/Documents/_Projects/MiuzCollectionsQT/env/lib/python3.11/site-packages/PyQt5/Qt5/plugins"
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plg

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReadDesatImage(src)
    # window.show()
    # sys.exit(app.exec_())

 