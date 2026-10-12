import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
							 QHBoxLayout, QPushButton, QLabel, QSizeGrip)
from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import QIcon

class MacControlButton(QPushButton):
	def __init__(self, btn_type, parent=None):
		super().__init__(parent)
		self.btn_type = btn_type  # 'close', 'minimize', 'maximize'
		self.base_path = "/Users/Loshkarev/Documents/_Projects/MiuzCollectionsQT/icons/traffic_lights"

		self.setFixedSize(12, 12)
		self.setStyleSheet("border: none; background: transparent;")

		self.is_window_focused = True
		self.is_group_hovered = False
		self.is_pressed = False

		self.update_icon()

	def update_icon(self):
		if not self.is_window_focused:
			icon_path = f"{self.base_path}/unfocused.svg"
		elif self.is_pressed:
			icon_path = f"{self.base_path}/{self.btn_type}/active.svg"
		elif self.is_group_hovered:
			icon_path = f"{self.base_path}/{self.btn_type}/hover.svg"
		else:
			icon_path = f"{self.base_path}/{self.btn_type}/default.svg"

		self.setIcon(QIcon(icon_path))
		self.setIconSize(QSize(12, 12))

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.is_pressed = True
			self.update_icon()
		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		self.is_pressed = False
		self.update_icon()
		super().mouseReleaseEvent(event)


class TitleBar(QWidget):
	def __init__(self, parent):
		super().__init__(parent)
		self.parent = parent
		self.setFixedHeight(28) # Стандартная высота заголовка macOS

		self.layout = QHBoxLayout(self)
		self.layout.setContentsMargins(8, 0, 0, 0)
		self.layout.setSpacing(8)

		self.close_btn = MacControlButton('close')
		self.min_btn = MacControlButton('minimize')
		self.max_btn = MacControlButton('maximize')

		self.close_btn.clicked.connect(self.parent.close)
		self.min_btn.clicked.connect(self.parent.showMinimized)
		self.max_btn.clicked.connect(self.toggle_maximize)

		self.layout.addWidget(self.close_btn)
		self.layout.addWidget(self.min_btn)
		self.layout.addWidget(self.max_btn)
		self.layout.addStretch() # Прижимаем кнопки влево

		# Устанавливаем фильтр событий, чтобы отслеживать hover для всей группы кнопок
		self.close_btn.installEventFilter(self)
		self.min_btn.installEventFilter(self)
		self.max_btn.installEventFilter(self)

		self._drag_pos = None

	def eventFilter(self, obj, event):
		if obj in (self.close_btn, self.min_btn, self.max_btn):
			if event.type() == QEvent.Type.Enter:
				self.set_group_hovered(True)
			elif event.type() == QEvent.Type.Leave:
				self.set_group_hovered(False)
		return super().eventFilter(obj, event)

	def set_group_hovered(self, state):
		self.close_btn.is_group_hovered = state
		self.min_btn.is_group_hovered = state
		self.max_btn.is_group_hovered = state
		self.close_btn.update_icon()
		self.min_btn.update_icon()
		self.max_btn.update_icon()

	def set_window_focused(self, state):
		self.close_btn.is_window_focused = state
		self.min_btn.is_window_focused = state
		self.max_btn.is_window_focused = state
		self.close_btn.update_icon()
		self.min_btn.update_icon()
		self.max_btn.update_icon()

	def toggle_maximize(self):
		if self.parent.isMaximized():
			self.parent.showNormal()
		else:
			self.parent.showMaximized()

	# Обработка перетаскивания окна
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self._drag_pos = event.globalPosition().toPoint()

	def mouseMoveEvent(self, event):
		if self._drag_pos is not None:
			delta = event.globalPosition().toPoint() - self._drag_pos
			self.parent.move(self.parent.pos() + delta)
			self._drag_pos = event.globalPosition().toPoint()

	def mouseReleaseEvent(self, event):
		self._drag_pos = None

	# Двойной клик по заголовку
	def mouseDoubleClickEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.toggle_maximize()


class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		
		# Убираем системный заголовок
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.resize(800, 600)

		# Общий главный виджет
		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)

		# Главный макет окна
		self.main_layout = QVBoxLayout(self.central_widget)
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(0)

		# --- 1. Первый макет (Кастомный заголовок) ---
		self.title_bar = TitleBar(self)
		self.main_layout.addWidget(self.title_bar)

		# --- 2. Второй макет (Под всё остальное) ---
		self.content_widget = QWidget()
		self.content_widget.setStyleSheet("background-color: #2D2D2D;") # Заглушка для цвета фона
		
		self.content_layout = QVBoxLayout(self.content_widget)
		self.content_layout.addWidget(QLabel("Основной контент галереи", alignment=Qt.AlignmentFlag.AlignCenter))
		
		# Добавляем контрол для изменения размеров окна (правый нижний угол)
		self.size_grip = QSizeGrip(self)
		self.content_layout.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

		self.main_layout.addWidget(self.content_widget)

	def changeEvent(self, event):
		# Отслеживаем фокус окна для изменения состояния светофоров на unfocused
		if event.type() == QEvent.Type.ActivationChange:
			self.title_bar.set_window_focused(self.isActiveWindow())
		super().changeEvent(event)


if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec())