import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt

class LargeExtensionFilterWidget(QWidget):
    def __init__(self, extensions: list[str], parent=None):
        super().__init__(parent)
        self.extensions = sorted(extensions)
        self.parent_widget = parent
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)
        
        # --- Верхняя панель: Поиск и Управление ---
        top_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск расширения...")
        self.search_input.textChanged.connect(self._filter_list_items)
        top_layout.addWidget(self.search_input)
        
        # Кнопка: Выбрать всё
        self.select_all_btn = QPushButton("Все")
        self.select_all_btn.clicked.connect(lambda: self.set_all_states(Qt.CheckState.Checked))
        top_layout.addWidget(self.select_all_btn)
        
        # Кнопка: Снять все
        self.clear_all_btn = QPushButton("Ничего")
        self.clear_all_btn.clicked.connect(lambda: self.set_all_states(Qt.CheckState.Unchecked))
        top_layout.addWidget(self.clear_all_btn)
        
        main_layout.addLayout(top_layout)
        
        # --- Список с чекбоксами ---
        self.list_widget = QListWidget()
        self.list_widget.setUniformItemSizes(True) 
        
        for ext in self.extensions:
            item = QListWidgetItem(ext.upper())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list_widget.addItem(item)
            
        self.list_widget.itemChanged.connect(self._on_item_changed)
        main_layout.addWidget(self.list_widget)

    def _filter_list_items(self, text: str):
        text = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_item_changed(self, item):
        self._emit_active_filters()

    def set_all_states(self, state: Qt.CheckState):
        """Включает или выключает все чекбоксы разом"""
        self.list_widget.blockSignals(True)
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(state)
        self.list_widget.blockSignals(False)
        self._emit_active_filters()

    def _emit_active_filters(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text().lower())
                
        if self.parent_widget and hasattr(self.parent_widget, 'on_filter_changed'):
            self.parent_widget.on_filter_changed(selected)


# --- Демонстрационное приложение ---
class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Активные фильтры (PyQt6)")
        self.resize(450, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Генерируем 100 тестовых расширений
        many_extensions = [f".ext{i}" for i in range(1, 101)]
        many_extensions.extend([".jpg", ".png", ".webp"])
        
        # 1. Виджет фильтра
        self.filter_widget = LargeExtensionFilterWidget(many_extensions, parent=self)
        layout.addWidget(self.filter_widget)
        
        # 2. Нативное текстовое поле для вывода списка активных фильтров
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)        # Только для чтения
        self.result_display.setMaximumHeight(80)     # Ограничиваем по высоте, чтобы не занимало много места
        layout.addWidget(self.result_display)
        
        # Инициализируем стартовый текст
        self.on_filter_changed(many_extensions)
        
    def on_filter_changed(self, active_extensions):
        """Срабатывает при любом изменении чекбоксов"""
        # Сортируем для предсказуемого отображения
        active_extensions = sorted(active_extensions)
        
        if not active_extensions:
            self.result_display.setText("Активные фильтры: (ничего не выбрано)")
            return
            
        # Форматируем текст в верхний регистр (например: JPG, PNG, EXT1)
        formatted_extensions = [ext.upper() for ext in active_extensions]
        text_list = ", ".join(formatted_extensions)
        
        # Выводим в поле. Перенос строк сработает автоматически благодаря нативному QTextEdit
        self.result_display.setText(f"Активные фильтры ({len(active_extensions)}):\n{text_list}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
