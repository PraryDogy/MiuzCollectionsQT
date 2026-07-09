from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap


from PyQt6.QtGui import QPixmap, QIcon, QImage
from PyQt6.QtCore import QSize, Qt

class UPixmap(QPixmap):
    def __init__(self, filepath: str = ""):
        # Позволяем создавать пустой пиксмап, если filepath не передан
        if filepath:
            super().__init__(filepath)
        else:
            super().__init__()

    @classmethod
    def fromImage(cls, image: QImage, flags=Qt.ImageConversionFlag.AutoColor) -> 'UPixmap':
        """Конвертирует QImage в кастомный UPixmap."""
        # 1. Получаем стандартный QPixmap от родительского класса
        base_pixmap = super().fromImage(image, flags)
        
        # 2. Создаем пустой экземпляр нашего класса UPixmap
        custom_pixmap = cls()
        
        # 3. Переносим внутренние данные (данные C++ объекта) из базового в наш
        custom_pixmap.swap(base_pixmap)
        
        return custom_pixmap

    def qiconed_resize(self, max_side: int) -> QPixmap:
        return QIcon(self).pixmap(QSize(max_side, max_side))
    
    def base_resize(self, width: int, height: int) -> QPixmap:
        return self.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
