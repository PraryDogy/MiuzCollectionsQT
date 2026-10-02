import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QLabel, QProgressBar, QPushButton)
from PyQt6.QtCore import Qt

class ProgressWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поиск совпадений")
        self.setFixedSize(300, 160) # Фиксируем размер окна
        
        # Основной вертикальный слой
        layout = QVBoxLayout(self)
        # Отступы от краев окна: слева, сверху, справа, снизу (по 16px)
        layout.setContentsMargins(16, 16, 16, 16) 
        # Расстояние между элементами внутри окна
        layout.setSpacing(12)

        # 1. Текст статуса
        self.status_label = QLabel("Найдено 15 из 30 изображений...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Немного увеличим шрифт
        self.status_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.status_label)

        # 2. Полоса прогресса (для наглядности)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(50)
        self.progress_bar.setTextVisible(False) # Скрываем проценты внутри полосы
        self.progress_bar.setFixedHeight(6)     # Делаем полоску тонкой и стильной
        layout.addWidget(self.progress_bar)

        # Пружина, которая прижимает кнопку к самому низу
        layout.addStretch()

        # 3. Растянутая кнопка
        self.stop_button = QPushButton("Остановить")
        
        # Наводим красоту: делаем кнопку похожей на современные веб/мобильные интерфейсы
        # Так как это кнопка отмены/остановки, логично сделать её в красных/теплых тонах
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;      /* Светло-красный фон */
                color: #dc2626;                 /* Темно-красный текст */
                border: 1px solid #fca5a5;      /* Рамка */
                border-radius: 6px;             /* Скругленные углы */
                padding: 10px;                  /* Внутренний отступ (делает кнопку "толстенькой") */
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #fca5a5;      /* Чуть темнее при наведении */
            }
            QPushButton:pressed {
                background-color: #f87171;      /* Еще темнее при клике */
            }
        """)
        
        # Добавляем в слой. QVBoxLayout автоматически растянет её по ширине окна
        # с учетом отступов (setContentsMargins), которые мы задали выше.
        layout.addWidget(self.stop_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProgressWindow()
    window.show()
    sys.exit(app.exec())