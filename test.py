from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QPainter
from PyQt5.QtWidgets import QApplication, QLabel


class MyLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)

        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


if __name__ == '__main__':
    app = QApplication([])

    label = MyLabel()
    label.setText('This is a really, long and poorly formatted runon sentence used to illustrate a point')
    label.setWindowFlags(Qt.Dialog)
    label.show()

    app.exec_()
