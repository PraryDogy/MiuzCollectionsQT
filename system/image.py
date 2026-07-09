from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap


class UPixmap(QPixmap):
    def __init__(self, filepath: str):
        super().__init__(filepath)

    def qiconed_resize(self, max_side: int) -> QPixmap:
        return QIcon(self).pixmap(QSize(max_side, max_side))
    
    def base_resize(self, width: int, height: int) -> QPixmap:
        return self.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
