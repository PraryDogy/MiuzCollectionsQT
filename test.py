import sys
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class DesignTestApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тестирование архитектуры дизайна UI")
        self.resize(1100, 600)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Главный сплиттер окна
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ==============================================================================
        # ЛЕВАЯ ПАНЕЛЬ: РЕШЕНИЕ 1 (Кнопка с меню + Stretch)
        # ==============================================================================
        left_container_1 = QWidget()
        left_layout_1 = QVBoxLayout(left_container_1)
        left_layout_1.setContentsMargins(
            0, 0, 0, 0
        )  # Убираем внешние рамки контейнера

        # 1. Горизонтальный ряд для кнопки управления (Панель инструментов)
        top_bar = QHBoxLayout()
        # Задаем внутренние отступы, чтобы кнопка не прилипала к краям сплиттера
        top_bar.setContentsMargins(10, 8, 10, 4)

        # Создаем кнопку и меню для нее
        self.menu_button = QPushButton("🗂️ Каталоги")
        catalog_menu = QMenu(self)
        catalog_menu.addAction("Каталог: Фотосессии 2026")
        catalog_menu.addAction("Каталог: Загрузки")
        catalog_menu.addSeparator()
        catalog_menu.addAction("➕ Добавить новый...")
        self.menu_button.setMenu(catalog_menu)

        # Архитектурный шаг: сжимаем кнопку до её контента
        self.menu_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )

        top_bar.addWidget(self.menu_button)
        top_bar.addStretch()  # Пружина: выталкивает кнопку влево, забирая всю лишнюю ширину

        left_layout_1.addLayout(top_bar)

        # Имитация дерева папок
        tree_stub_1 = QTreeView()
        left_layout_1.addWidget(tree_stub_1)

        splitter.addWidget(left_container_1)

        # ==============================================================================
        # СРЕДНЯЯ ПАНЕЛЬ: РЕШЕНИЕ 2 (Плоский QComboBox в стиле "Header Flat")
        # ==============================================================================
        left_container_2 = QWidget()
        # Визуально отделим второе решение тонкой границей для теста
        left_container_2.setStyleSheet(
            "border-left: 1px solid #d3d3d3; border-right: 1px solid #d3d3d3;"
        )
        left_layout_2 = QVBoxLayout(left_container_2)
        left_layout_2.setContentsMargins(0, 0, 0, 0)

        # Создаем QComboBox, который будет выглядеть как заголовок всей панели
        self.flat_combobox = QComboBox()
        self.flat_combobox.addItems(
            ["📸 Фотосессии 2026", "📥 Загрузки", "📂 Личный архив"]
        )

        # Стилизуем под современный плоский интерфейс без рамок
        self.flat_combobox.setStyleSheet("""
            QComboBox {
                border: none;
                background-color: #f0f0f0; /* Легкий контрастный фон под шапку */
                font-weight: bold;
                font-size: 13px;
                padding: 10px 15px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
        """)
        # Комбобокс по умолчанию растягивается на всю ширину, что нам и нужно для "шапки"
        left_layout_2.addWidget(self.flat_combobox)

        # Имитация дерева папок
        tree_stub_2 = QTreeView()
        tree_stub_2.setStyleSheet(
            "border: none;"
        )  # Убираем рамку, чтобы сливалось с шапкой
        left_layout_2.addWidget(tree_stub_2)

        splitter.addWidget(left_container_2)

        # ==============================================================================
        # ПРАВАЯ ПАНЕЛЬ: Сетка изображений (Заглушка)
        # ==============================================================================
        right_grid = QListWidget()
        right_grid.setViewMode(QListWidget.ViewMode.IconMode)
        # Подсказка по центру
        placeholder = QLabel(
            "← Подвигайте сплиттеры\n\nСлева: Вариант с кнопкой и Stretch\nЦентр: Вариант с плоским ComboBox\nСправа: Сетка",
            right_grid,
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")

        # При изменении размера окна центрируем текст-заглушку
        right_grid.resizeEvent = (
            lambda event: placeholder.setGeometry(right_grid.rect()) or None
        )

        splitter.addWidget(right_grid)

        # Настраиваем начальные пропорции панелей в сплиттере (25% | 25% | 50%)
        # splitter.setSizes()

        # Запрещаем панелям полностью схлопываться в 0 при перетаскивании
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Немного осовременим общий стиль (Fusion выглядит аккуратнее дефолтного Windows-стиля)
    app.setStyle("Fusion")
    window = DesignTestApp()
    window.show()
    sys.exit(app.exec())
