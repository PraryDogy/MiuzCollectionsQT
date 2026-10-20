import os
import re
import sys
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QAction, QCloseEvent, QContextMenuEvent, QFontMetrics,
						 QIcon, QMouseEvent)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QGridLayout,
							 QGroupBox, QHBoxLayout, QLabel, QLayout,
							 QLineEdit, QListWidget, QListWidgetItem,
							 QMainWindow, QMenu, QProgressBar, QPushButton,
							 QScrollArea, QSizePolicy, QSlider, QSpinBox,
							 QStackedWidget, QTextEdit, QTreeView, QTreeWidget,
							 QTreeWidgetItem, QVBoxLayout, QWidget)

from cfg import JsonData, Static
from system.lang import Lng
from system.utils import Utils


class TransparentButton(QPushButton):
	def __init__(self, text="", parent=None):
		super().__init__(text=text, parent=parent)


class TransparentLabel(QLabel):
	sym_line_feed = "\u000a"
	sym_paragraph_sep = "\u2029"

	def __init__(self, text="", parent=None):
		super().__init__(text, parent)

		self._original_text = text
		self._elide_enabled = False
		self._context_menu_enabled = False

	def setText(self, text: str):
		self._original_text = text
		self._update_text()

	def set_font_size(self, value_px: int):
		font = self.font()
		font.setPixelSize(value_px)
		self.setFont(font)

	def set_selectable(self, enabled: bool):
		if enabled:
			self.setTextInteractionFlags(
				Qt.TextInteractionFlag.TextSelectableByMouse
			)
			self.setCursor(Qt.CursorShape.IBeamCursor)
			self.set_context_menu(True)
		else:
			self.setTextInteractionFlags(
				Qt.TextInteractionFlag.NoTextInteraction
			)
			self.unsetCursor()

	def set_context_menu(self, enabled: bool):
		self._context_menu_enabled = enabled

	def set_elide(self, enabled: bool = True):
		self._elide_enabled = enabled
		self._update_text()

	def get_elided_text(self):
		metrics = QFontMetrics(self.font())
		return metrics.elidedText(
			self._original_text,
			Qt.TextElideMode.ElideMiddle,
			self.contentsRect().width(),
		)

	def _update_text(self):
		text = (
			self.get_elided_text()
			if self._elide_enabled
			else self._original_text
		)

		QLabel.setText(self, text)

		self.setToolTip(
			self._original_text
			if self._elide_enabled and text != self._original_text
			else ""
		)

	def resizeEvent(self, event):
		super().resizeEvent(event)

		if self._elide_enabled:
			self._update_text()

	def contextMenuEvent(self, ev: QContextMenuEvent):
		if not self._context_menu_enabled:
			return super().contextMenuEvent(ev)

		text = self.selectedText().replace(
			self.sym_paragraph_sep, ""
		).replace(self.sym_line_feed, "")

		full_text = self._original_text.replace(
			self.sym_paragraph_sep, ""
		).replace(self.sym_line_feed, "")

		menu = UMenu(parent=self)

		copy_action = QAction(Lng.copy[JsonData.lng_index], menu)
		copy_action.triggered.connect(
			lambda: Utils.pyqt_copy_text(text)
		)
		menu.addAction(copy_action)

		if os.path.isfile(full_text) or os.path.isdir(full_text):
			reveal_action = QAction(
				Lng.reveal_in_finder[JsonData.lng_index], menu
			)
			reveal_action.triggered.connect(
				lambda: Utils.macos_reveal_files([full_text])
			)
			menu.addAction(reveal_action)

		menu.show_menu_under_cursor(ev)


class TransparentFrame(QFrame):
	def __init__(self, parent=None):
		super().__init__(parent)


class TransparentWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)


class TransparentLineEdit(QLineEdit):
	def __init__(self, parent=None):
		super().__init__(parent)


class TransparentTextEdit(QTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)


class TransparentMenu(QMenu):
	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)


class TransparentScrollArea(QScrollArea):
	def __init__(self, parent=None):
		super().__init__(parent)


class UGroupBox(QGroupBox):
	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)


class TransparentListWidget(QListWidget):
	def __init__(self, parent=None):
		super().__init__(parent)


class TransparentTreeWidget(QTreeWidget):
	def __init__(self, parent=None):
		super().__init__(parent)


class TransparentTreeView(QTreeView):
	def __init__(self, parent=None):
		super().__init__(parent)


class UMenu(TransparentMenu):
	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)

	def show_menu_under_cursor(self, event: QContextMenuEvent):
		self.exec(event.globalPos())

	def mouseReleaseEvent(self, a0):
		if a0.button() == Qt.MouseButton.RightButton:
			a0.ignore()
		else:
			super().mouseReleaseEvent(a0)


class ULineEdit(TransparentLineEdit):
	hh = 30

	def __init__(self):
		super().__init__()

	def cut_selection(self, *args):
		text = self.selectedText()
		Utils.pyqt_copy_text(text)

		new_text = self.text().replace(text, "")
		self.setText(new_text)

	def paste_text(self, *args):
		text = Utils.pyqt_paste_text()
		self.insert(text)

	def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
		self.menu_ = UMenu(parent=self)

		actions = [
			(Lng.cut[JsonData.lng_index], self.cut_selection),
			(Lng.copy[JsonData.lng_index], lambda: Utils.pyqt_copy_text(self.selectedText())),
			(Lng.paste[JsonData.lng_index], self.paste_text),
		]

		for text, slot in actions:
			act = QAction(text=text, parent=self.menu_)
			act.triggered.connect(slot)
			self.menu_.addAction(act)

		self.menu_.show_menu_under_cursor(a0)


class UTextEdit(TransparentTextEdit):
	def __init__(self):
		super().__init__()

	def copy_selection(self):
		cur = self.textCursor()
		text = cur.selectedText().strip()
		Utils.pyqt_copy_text(text)

	def cut_selection(self):
		cur = self.textCursor()
		text = cur.selectedText().strip()
		Utils.pyqt_copy_text(text)
		cur.removeSelectedText()

	def paste_text(self):
		text = Utils.pyqt_paste_text()
		new_text = self.toPlainText() + text
		self.setPlainText(new_text)

	def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
		menu_ = UMenu(parent=self)

		actions = [
			(Lng.cut[JsonData.lng_index], self.cut_selection),
			(Lng.copy[JsonData.lng_index], self.copy_selection),
			(Lng.paste[JsonData.lng_index], self.paste_text),
		]

		for text, slot in actions:
			act = QAction(text=text, parent=menu_)
			act.triggered.connect(slot)
			menu_.addAction(act)

		menu_.show_menu_under_cursor(a0)


class UScrollVerticalArea(TransparentScrollArea):
	def __init__(self):
		super().__init__()
		self.setWidgetResizable(True)
		self.setAcceptDrops(True)
		self.horizontalScrollBar().setDisabled(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


class UListSpacerItem(QListWidgetItem):

	def __init__(self, parent: QListWidget):
		super().__init__()
		self.setFlags(Qt.ItemFlag.NoItemFlags)


class UListWidgetItem(QListWidgetItem):

	def __init__(self, parent: QListWidget, text: str):
		super().__init__(text, parent)

	def set_checkable(self):
		self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
		self.setCheckState(Qt.CheckState.Unchecked)


class UTreeWidgetItem(QTreeWidgetItem):

	def __init__(self, parent: QTreeWidget | QTreeWidgetItem, text: str):
		super().__init__(parent, [text])


class UListWidget(TransparentListWidget):
	ICON_SIZE = (16, 16)

	def __init__(self):
		super().__init__()
		self.horizontalScrollBar().setDisabled(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setIconSize(QSize(*self.ICON_SIZE))


class UTreeWidget(TransparentTreeWidget):
	ICON_SIZE = (16, 16)

	def __init__(self):
		super().__init__()
		self.horizontalScrollBar().setDisabled(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setIconSize(QSize(*self.ICON_SIZE))

		self.setHeaderHidden(True)
		self.setAutoScroll(False)
		self.setIndentation(15)


class UTreeView(TransparentTreeView):
	def __init__(self, parent=None):
		super().__init__(parent)


class UPushButton(TransparentButton):
	hh = 28
	icon_size = (12, 12)

	def __init__(self, text: str):
		self._raw_text = ""      # Инициализируем переменную для хранения чистого текста
		super().__init__("")
		self.setIconSize(QSize(*self.icon_size))
		self.setFixedHeight(self.hh)
		self.setText(text)       # Вызываем наш переопределенный setText
		self.ensurePolished()

	def setText(self, text):
		self._raw_text = text    # Сохраняем оригинальный текст без пробелов
		self._apply_text()       # Применяем форматирование

	def text(self):
		# Возвращаем чистый текст, чтобы в других частях программы не вылезали лишние пробелы
		return self._raw_text

	def setIcon(self, icon):
		super().setIcon(icon)
		self._apply_text()       # Пересчитываем текст, так как иконка могла появиться или исчезнуть

	def _apply_text(self):
		# Если у кнопки есть иконка (не пустая) и есть текст — добавляем пробел
		if not self.icon().isNull() and self._raw_text:
			super().setText(" " + self._raw_text)
		else:
			super().setText(self._raw_text)

	def enterEvent(self, event):
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		super().enterEvent(event)


class ActiveButton(UPushButton):
	def __init__(self, text):
		super().__init__(text)


class USep(TransparentFrame):
	property_name = "style"

	def __init__(self):
		super().__init__()
		self.setFixedHeight(1)
		self.set_style("default")

	def set_style(self, style: Literal["default", "dark_gray"]):
		self.setProperty(self.property_name, style)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()


class USlider(QSlider):
	clicked = pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.valueChanged.connect(self._on_value_changed)

	def mousePressEvent(self, ev):
		if ev.button() != Qt.MouseButton.LeftButton:
			ev.ignore()
			return

		ratio = ev.pos().x() / self.width()
		value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
		self.setValue(value)
		ev.accept()
		return super().mousePressEvent(ev)

	def wheelEvent(self, e) -> None:
		if e:
			e.ignore()

	def _on_value_changed(self, value: int):
		self.blockSignals(True)
		self.setValue(value)
		self.blockSignals(False)
		self.clicked.emit(value)


class USpinBox(QSpinBox):
	def __init__(self, *args, **kw):
		super().__init__(*args, **kw)
		self.setFixedHeight(27)

	def enterEvent(self, event):
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		return super().enterEvent(event)


class UGroupBox(UGroupBox):
	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)


class UCheckBox(QCheckBox):
	def __init__(self, text: str, parent=None):
		super().__init__(text, parent)
		self.setCursor(Qt.CursorShape.PointingHandCursor)



class MacControlButton(QPushButton):
	base_path = Static.ICONS / "traffic_lights"

	def __init__(self, btn_type: str, parent=None):
		super().__init__(parent)
		self.btn_type = btn_type  # 'close', 'minimize', 'maximize'
		self.setFixedSize(12, 12)

		self.is_window_focused = True
		self.is_group_hovered = False
		self.is_pressed = False

		self.update_icon()

	def update_icon(self):
		# Если окно не в фокусе ИЛИ кнопка отключена — ставим серую иконку
		if not self.isEnabled() or not self.is_window_focused:
			icon_path = f"{self.base_path}/unfocused.svg"
		elif self.is_pressed:
			icon_path = f"{self.base_path}/{self.btn_type}/active.svg"
		elif self.is_group_hovered:
			icon_path = f"{self.base_path}/{self.btn_type}/hover.svg"
		else:
			icon_path = f"{self.base_path}/{self.btn_type}/default.svg"

		self.setIcon(QIcon(icon_path))
		self.setIconSize(QSize(12, 12))

	def mousePressEvent(self, e):
		if e.button() == Qt.MouseButton.LeftButton:
			self.is_pressed = True
			self.update_icon()
		return super().mousePressEvent(e)

	def mouseReleaseEvent(self, e):
		self.is_pressed = False
		self.update_icon()
		return super().mouseReleaseEvent(e)


class TitleBar(TransparentWidget):
	HH = 28
	TRAFFIC_LIGHT_WIDTH = 0

	def __init__(self, parent: QMainWindow):
		super().__init__(parent)
		self.setFixedHeight(self.HH)

		self.parent_ = parent
		self._drag_pos = None

		self.h_layout = QHBoxLayout(self)
		self.h_layout.setContentsMargins(0, 0, 0, 0)
		self.h_layout.setSpacing(0)

		
		# --- 1. Контейнер для кнопок-светофоров ---
		self.buttons_widget = TransparentWidget()
		self.buttons_layout = QHBoxLayout(self.buttons_widget)
		self.buttons_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

		self.close_btn = MacControlButton('close') # (12px)
		self.min_btn = MacControlButton('minimize') # (12px)
		self.max_btn = MacControlButton('maximize') # (12px)

		self.close_btn.clicked.connect(self.parent_.close)
		self.min_btn.clicked.connect(self.parent_.showMinimized)
		self.max_btn.clicked.connect(self.toggle_maximize)

		self.buttons_layout.setContentsMargins(0, 0, 0, 0)
		self.buttons_layout.setSpacing(0)
		self.buttons_layout.addSpacing(10)
		self.buttons_layout.addWidget(self.close_btn)
		self.buttons_layout.addSpacing(8)
		self.buttons_layout.addWidget(self.min_btn)
		self.buttons_layout.addSpacing(8)
		self.buttons_layout.addWidget(self.max_btn)
		self.buttons_layout.addSpacing(15)

		self.h_layout.addWidget(self.buttons_widget)
		self.buttons_widget.adjustSize()
		TitleBar.TRAFFIC_LIGHT_WIDTH = self.buttons_widget.sizeHint().width()
		
		# --- 2. Контейнер для заголовка или кастомного виджета ---
		self.content_container = TransparentWidget()
		self.content_container.setSizePolicy(
			QSizePolicy.Policy.Expanding,
			QSizePolicy.Policy.Preferred
		)
		
		self.content_layout = QVBoxLayout(self.content_container)
		self.content_layout.setContentsMargins(0, 0, 0, 0)
		
		self.title_label = TransparentLabel()
		self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.content_layout.addWidget(self.title_label)
		
		self.h_layout.addWidget(self.content_container)

		# --- 3. Балансировочная пустышка справа ---
		# Ширина: 10 + 36 + 16 + 15 = 77 пикселей
		self.right_spacer = TransparentWidget()
		self.right_spacer.setFixedWidth(self.TRAFFIC_LIGHT_WIDTH)
		self.h_layout.addWidget(self.right_spacer)

		self.close_btn.installEventFilter(self)
		self.min_btn.installEventFilter(self)
		self.max_btn.installEventFilter(self)

	def set_custom_widget(self, widget: QWidget):
		# Прячем стандартный текст вместо его удаления
		self.title_label.hide()
		
		# Безопасно удаляем старые кастомные виджеты, не трогая title_label
		for i in reversed(range(self.content_layout.count())):
			item = self.content_layout.itemAt(i)
			w = item.widget()
			if w and w != self.title_label:
				self.content_layout.removeItem(item)
				w.deleteLater()
				
		self.content_layout.addWidget(widget)
		self.right_spacer.hide()

	def set_title_text(self, text: str):
		# Удаляем любые кастомные виджеты, если они были добавлены
		for i in reversed(range(self.content_layout.count())):
			item = self.content_layout.itemAt(i)
			w = item.widget()
			if w and w != self.title_label:
				self.content_layout.removeItem(item)
				w.deleteLater()
				
		# Снова показываем наш текстовый лейбл
		self.title_label.setText(text)
		self.title_label.show()
		self.right_spacer.show()

	def set_group_hovered(self, state: bool):
		self.close_btn.is_group_hovered = state
		self.min_btn.is_group_hovered = state
		self.max_btn.is_group_hovered = state
		self.close_btn.update_icon()
		self.min_btn.update_icon()
		self.max_btn.update_icon()

	def set_window_focused(self, state: bool):
		self.close_btn.is_window_focused = state
		self.min_btn.is_window_focused = state
		self.max_btn.is_window_focused = state
		self.close_btn.update_icon()
		self.min_btn.update_icon()
		self.max_btn.update_icon()

	def toggle_maximize(self):
		if self.parent_.isMaximized():
			self.parent_.showNormal()
		else:
			self.parent_.showMaximized()

	def set_close_only(self):
		self.min_btn.setEnabled(False)
		self.max_btn.setEnabled(False)
		self.min_btn.update_icon()
		self.max_btn.update_icon()

	def eventFilter(self, a0, a1):
		if a0 in (self.close_btn, self.min_btn, self.max_btn):
			if a1.type() == QEvent.Type.Enter:
				self.set_group_hovered(True)
			elif a1.type() == QEvent.Type.Leave:
				self.set_group_hovered(False)
		return super().eventFilter(a0, a1)

	def mousePressEvent(self, a0):
		if a0.button() == Qt.MouseButton.LeftButton:
			self._drag_pos = a0.globalPosition().toPoint()

	def mouseMoveEvent(self, a0):
		if self._drag_pos is not None:
			delta = a0.globalPosition().toPoint() - self._drag_pos
			self.parent_.move(self.parent_.pos() + delta)
			self._drag_pos = a0.globalPosition().toPoint()

	def mouseReleaseEvent(self, a0):
		self._drag_pos = None


# стилизованный виджет, чтобы окно имело заливку + рамку + углы
class UMainWindowFrame(TransparentFrame):
	property_name = "style"

	def __init__(self, parent=None):
		super().__init__(parent)
		self.set_style("default")

	def set_style(self, style: Literal["default", "black"]):
		self.setProperty(self.property_name, style)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()


class UMainWindow(QMainWindow):
	win_list: list[QWidget] = []

	def __init__(self, parent: QWidget = None):
		super().__init__(parent)
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setup_window()

	def setWindowTitle(self, title: str):
		self.title_bar.set_title_text(title)
		return super().setWindowTitle(title)

	def setup_window(self):
		central_widget = UMainWindowFrame()
		self.setCentralWidget(central_widget)

		self.window_layout = QVBoxLayout(central_widget)
		self.window_layout.setContentsMargins(0, 0, 0, 0)
		self.window_layout.setSpacing(0)

		self.title_bar = TitleBar(self)
		self.window_layout.addWidget(self.title_bar)

		self.sep_container = TransparentWidget()
		self.sep_layout = QVBoxLayout(self.sep_container)
		self.sep_layout.setContentsMargins(5, 1, 5, 1)
		self.sep_layout.setSpacing(0)
		self.sep = USep()
		self.sep_layout.addWidget(self.sep)
		self.window_layout.addWidget(self.sep_container)
		self.sep_container.setVisible(False)

		self.central_layout = QVBoxLayout()
		self.central_layout.setContentsMargins(0, 0, 0, 0)
		self.central_layout.setSpacing(0)
		
		self.window_layout.addLayout(self.central_layout)

		self.register_window()

	def set_window_style(self, style: Literal["default", "black"]):
		frame: UMainWindowFrame = self.centralWidget()
		frame.set_style(style)

	def set_titlebar_sep_style(self, style: Literal["default", "dark_gray"]):
		self.sep.set_style(style)

	def set_titlebar_height(self, h: int):
		self.title_bar.setFixedHeight(h)

	def show_titlebar_sep(self):
		self.sep_container.setVisible(True)

	def register_window(self):
		self.win_list.append(self)

	def unregister_window(self):
		try:
			self.win_list.remove(self)
		except ValueError:
			pass

	def center_to_parent(self, parent: QWidget):
		try:
			geo = self.geometry()
			geo.moveCenter(parent.geometry().center())
			self.setGeometry(geo)
		except Exception as e:
			print("center error:", e)

	def set_always_on_top(self):
		self.setWindowModality(Qt.WindowModality.ApplicationModal)

	def set_close_only(self):
		self.title_bar.set_close_only()
		return
		flags = Qt.WindowType.CustomizeWindowHint
		flags |= Qt.WindowType.WindowCloseButtonHint
		self.setWindowFlags(flags)

	def closeEvent(self, event: QCloseEvent | None):
		self.unregister_window()
		return super().closeEvent(event)

	def deleteLater(self):
		self.unregister_window()
		return super().deleteLater()


class GrayTextLabel(TransparentLabel):
	def __init__(self, text: str):
		super().__init__(text)


class TitleTextLabel(TransparentLabel):
	def __init__(self, text="", parent=None):
		super().__init__(text, parent)


class UTagWidget(TransparentFrame):
	right_svg_clicked = pyqtSignal()
	text_clicked = pyqtSignal()
	left_svg_clicked = pyqtSignal()

	qss_property_name = "style"
	qss_blue = "blue"
	qss_gray = "gray"
	qss_transparent = "transparent"
	qss_green = "green"

	tag_height = 25
	right_svg_size = (14, 14)
	left_svg_size = (15, 15)
	base_right_spacing = 7
	low_right_spacing = 3

	def __init__(
			  self, text: str,
			  qss_style: str,
			  left_svg_path: str = None,
			  right_svg_path: str = None
			):
		super().__init__()
		self.qss_style = qss_style
		self.setFixedHeight(self.tag_height)
		self.setProperty(UTagWidget.qss_property_name, qss_style)
		self.set_qss_style(qss_style)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.h_lay = QHBoxLayout(self)
		self.h_lay.setContentsMargins(7, 2, self.base_right_spacing, 2)
		self.h_lay.setSpacing(6)
		self.h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

		if left_svg_path:
			self.left_svg_widget = QSvgWidget()
			self.left_svg_widget.mouseReleaseEvent = self.text_widget_cmd
			self.left_svg_widget.load(left_svg_path)
			self.left_svg_widget.setFixedSize(*self.left_svg_size)
			self.h_lay.addWidget(self.left_svg_widget)

		self.text_widget = TransparentLabel(text)
		self.text_widget.mouseReleaseEvent = self.text_widget_cmd
		self.h_lay.addWidget(self.text_widget)

		if right_svg_path:
			right_svg_wrapper = TransparentWidget()
			self.h_lay.addWidget(right_svg_wrapper)
			self.right_svg_lay = QVBoxLayout(right_svg_wrapper)
			self.right_svg_lay.setContentsMargins(0, 0, 0, 0)
			self.right_svg_lay.setSpacing(0)

			self.right_svg_widget = QSvgWidget()
			self.right_svg_widget.mouseReleaseEvent = self.right_svg_cmd
			self.right_svg_widget.load(right_svg_path)
			self.right_svg_widget.setFixedSize(*self.right_svg_size)
			self.right_svg_lay.addWidget(self.right_svg_widget)

	def set_qss_style(self, qss_style: str):
		self.qss_style = qss_style
		self.setProperty(UTagWidget.qss_property_name, qss_style)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def right_svg_cmd(self, *args):
		self.right_svg_clicked.emit()

	def text_widget_cmd(self, *args):
		self.text_clicked.emit()


class RowArrowWidget(TransparentWidget):
	clicked = pyqtSignal()
	arrow_svg = Static.COMMON_ICONS / "next.svg"
	warning_svg = Static.COMMON_ICONS / "yellow_warning.svg"
	hh = 26
	svg_size = 16

	# обычно эти виджеты помещаются в QGroupBox
	# Это правильные отступы чтобы все красиво смотрелось
	group_margings = (5, 5, 5, 5)
	group_spacing = 5

	def __init__(self, text: str):
		super().__init__()
		self.setFixedHeight(self.hh)
		
		# Один прямой горизонтальный слой
		self.main_layout = QHBoxLayout(self)
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(10)
		
		# Иконка слева
		self.left_icon = QSvgWidget()
		self.left_icon.setFixedSize(self.svg_size, self.svg_size)
		self.left_icon.hide()
		
		# Текст
		self.text_widget = QLabel(text)
		
		# Стрелка справа
		self.arrow_wid = QSvgWidget()
		self.arrow_wid.setFixedSize(self.svg_size, self.svg_size)
		self.arrow_wid.load(str(self.arrow_svg))
		
		# Сборка в один ряд
		self.main_layout.addWidget(self.left_icon)
		self.main_layout.addWidget(self.text_widget)
		self.main_layout.addStretch()
		self.main_layout.addWidget(self.arrow_wid)
		
		self.adjustSize()

	def set_left_icon(self, svg_path: Path):
		self.left_icon.load(str(svg_path))
		self.left_icon.show()

	def replace_arrow_widget(self, widget: QWidget):
		self.arrow_wid.hide()
		self.main_layout.addWidget(widget)

	def hide_arrow(self):
		self.arrow_wid.hide()

	def show_warning(self):
		self.set_left_icon(self.warning_svg)

	def set_disabled(self):
		self.blockSignals(True)
		self.setDisabled(True)

	def mouseReleaseEvent(self, a0):
		if a0.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit()
		return super().mouseReleaseEvent(a0)

	def enterEvent(self, event):
		if self.arrow_wid.isVisible():
			self.setCursor(Qt.CursorShape.PointingHandCursor)
		return super().enterEvent(event)



class WinProgressbar(UMainWindow):
	cancel = pyqtSignal()
	files_icon_path = Static.COMMON_ICONS / "copy_files.svg"
	cancel_icon_path = Static.COMMON_ICONS / "cancel.svg"
	ww = 370

	def __init__(self, title: str):
		super().__init__()
		self.setWindowTitle(title)
		self.setFixedWidth(self.ww)

		self.central_layout.setContentsMargins(10, 0, 10, 10)
		self.central_layout.setSpacing(0)
		self.show_titlebar_sep()
		self.central_layout.addSpacing(10)

		h_wid = QWidget()
		self.central_layout.addWidget(h_wid)
		h_lay = QHBoxLayout(h_wid)
		h_lay.setContentsMargins(0, 0, 0, 0)
		h_lay.setSpacing(10)

		left_side_icon = QSvgWidget(str(self.files_icon_path))
		left_side_icon.setFixedSize(40, 40)
		h_lay.addWidget(left_side_icon)

		right_side_wid = QWidget()
		right_side_lay = QVBoxLayout(right_side_wid)
		right_side_lay.setContentsMargins(0, 0, 0, 0)
		right_side_lay.setSpacing(2)
		h_lay.addWidget(right_side_wid)

		self.above_label = QLabel()
		right_side_lay.addWidget(self.above_label)

		progressbar_row = QWidget()
		right_side_lay.addWidget(progressbar_row)
		progressbar_lay = QHBoxLayout(progressbar_row)
		progressbar_lay.setContentsMargins(0, 0, 0, 0)
		progressbar_lay.setSpacing(10)
		progressbar_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.progressbar = QProgressBar()
		self.progressbar.setTextVisible(False)
		self.progressbar.setFixedHeight(6)
		self.progressbar.adjustSize()
		progressbar_lay.addWidget(self.progressbar)

		self.cancel_btn = QSvgWidget(str(self.cancel_icon_path))
		self.cancel_btn.setFixedSize(13, 13)
		self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
		progressbar_lay.addWidget(self.cancel_btn)

		self.below_label = QLabel()
		right_side_lay.addWidget(self.below_label)

		self.adjustSize()

	def cancel_cmd(self, *args):
		self.cancel.emit()
		self.deleteLater()

	def closeEvent(self, a0):
		self.cancel.emit()
		return super().closeEvent(a0)


class VerticalWindow(UMainWindow):
	def __init__(self):
		super().__init__()

		self.central_layout.setSpacing(10)
		self.central_layout.setContentsMargins(15, 10, 15, 15)

		self.icon_text_widget = TransparentWidget()
		self.central_layout.addWidget(self.icon_text_widget)

		self.icon_text_layout = QVBoxLayout(self.icon_text_widget)
		self.icon_text_layout.setContentsMargins(10, 0, 10, 0)
		self.icon_text_layout.setSpacing(5)

		self.btn_widget = QWidget()
		self.central_layout.addWidget(self.btn_widget)

		self.btn_layout = QVBoxLayout(self.btn_widget)
		self.btn_layout.setContentsMargins(0, 0, 0, 0)
		self.btn_layout.setSpacing(6)

	def _calculate_optimal_text_width(
		self, text_wid: QLabel, text: str,
		min_width: int = 180, max_width: int = 800,
	) -> int:
		fm = text_wid.fontMetrics()
		single_line_width = fm.horizontalAdvance(text)

		if single_line_width <= min_width:
			return single_line_width + 2

		for width in range(min_width, max_width + 1, 5):
			rect = fm.boundingRect(
				0, 0, width, 10000,
				Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft,
				text,
			)
			if rect.height() > 0 and width / rect.width() <= 1.05:
				return width

		return max_width

	def _adjust_window_size(self, text_wid: QLabel, text: str):
		text_wid.setFixedWidth(self._calculate_optimal_text_width(text_wid, text))

		self.icon_text_layout.activate()
		self.central_layout.activate()

		ideal_size = self.centralWidget().sizeHint()
		self.adjustSize()
		self.setFixedSize(self.width(), ideal_size.height())


class ConfirmWindow(VerticalWindow):
	ok_clicked = pyqtSignal()
	cancel_clicked = pyqtSignal()

	icon_path = Static.COMMON_ICONS / "yellow_warning.svg"
	icon_size = (65, 65)
	ww = 280

	def __init__(self, text: str):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		# self.show_titlebar_underline()
		self.setWindowTitle(Lng.attention[JsonData.lng_index])

		self._setup_ui(text)
		self.central_layout.activate()
		self._adjust_window_size(self.text_wid, text)

	def _setup_ui(self, text: str):
		self.svg_widget = QSvgWidget()
		self.svg_widget.load(str(self.icon_path))
		self.svg_widget.setFixedSize(*self.icon_size)
		self.icon_text_layout.addWidget(
			self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter
		)

		self.text_wid = GrayTextLabel(text)
		self.text_wid.set_selectable(True)
		self.text_wid.setWordWrap(True)
		self.icon_text_layout.addWidget(self.text_wid)

		self.ok_btn = ActiveButton(Lng.confirm[JsonData.lng_index])
		self.ok_btn.clicked.connect(self.ok_clicked.emit)
		self.ok_btn.clicked.connect(self.deleteLater)
		self.btn_layout.addWidget(self.ok_btn)

		self.cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
		self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
		self.cancel_btn.clicked.connect(self.deleteLater)
		self.btn_layout.addWidget(self.cancel_btn)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Escape:
			self.cancel_clicked.emit()
			self.deleteLater()
		else:
			super().keyPressEvent(event)


class WarningWindow(VerticalWindow):
	ok_clicked = pyqtSignal()
	cancel_clicked = pyqtSignal()

	icon_path = Static.COMMON_ICONS / "yellow_warning.svg"
	icon_size = (65, 65)
	ww = 280

	def __init__(self, text: str, text_edit_text: str = None):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.show_titlebar_sep()
		self.setWindowTitle(Lng.attention[JsonData.lng_index])

		self._setup_ui(text, text_edit_text)
		self.central_layout.activate()
		self._adjust_window_size(self.text_wid, text)

	def _setup_ui(self, text: str, text_edit_text: str):
		self.svg_widget = QSvgWidget()
		self.svg_widget.load(str(self.icon_path))
		self.svg_widget.setFixedSize(*self.icon_size)
		self.icon_text_layout.addWidget(
			self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter
		)

		self.text_wid = GrayTextLabel(text)
		self.text_wid.set_selectable(True)
		self.text_wid.setWordWrap(True)
		self.icon_text_layout.addWidget(self.text_wid)

		if text_edit_text:
			self.text_edit_widget = UTextEdit()
			self.text_edit_widget.setPlainText(text_edit_text)
			self.icon_text_layout.addWidget(self.text_edit_widget)

		self.cancel_btn = ActiveButton(Lng.got_it[JsonData.lng_index])
		self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
		self.cancel_btn.clicked.connect(self.deleteLater)
		self.btn_layout.addWidget(self.cancel_btn)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Escape:
			self.cancel_clicked.emit()
			self.deleteLater()
		else:
			super().keyPressEvent(event)


class SuperConfirmWindow(ConfirmWindow):
	icon_path = Static.COMMON_ICONS / "red_warning.svg"

	def __init__(self, text: str):
		super().__init__(text)
		self.svg_widget.load(str(self.icon_path))


class InputTextWin(UMainWindow):
	ok_clicked = pyqtSignal(str)
	cancel_clicked = pyqtSignal()

	def __init__(self, description: str, svg_path: str = None):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.text_input[JsonData.lng_index])
		self.show_titlebar_sep()
		self.central_layout.addSpacing(10)
		self.central_layout.setContentsMargins(10, 0, 10, 10)
		self.central_layout.setSpacing(0)

		svg_text_widget = TransparentWidget()
		self.central_layout.addWidget(svg_text_widget)
		svg_text_layout = QHBoxLayout(svg_text_widget)
		svg_text_layout.setContentsMargins(5, 0, 10, 0)
		svg_text_layout.setSpacing(5)

		if svg_path:
			svg_icon = QSvgWidget()
			svg_icon.load(svg_path)
			svg_icon.setFixedSize(20, 20)
			svg_text_layout.addWidget(svg_icon)

		self.description_label = GrayTextLabel(description)
		svg_text_layout.addWidget(self.description_label)

		self.central_layout.addSpacing(10)

		self.line_edit_widget = ULineEdit()
		self.line_edit_widget.setPlaceholderText(Lng.input_text[JsonData.lng_index])
		self.central_layout.addWidget(self.line_edit_widget)

		self.central_layout.addSpacing(10)

		btn_widget = QWidget()
		self.central_layout.addWidget(btn_widget)

		btn_layout = QHBoxLayout(btn_widget)
		btn_layout.setContentsMargins(0, 0, 0, 0)
		btn_layout.setSpacing(10)

		btn_layout.addStretch()

		self.cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
		self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
		self.cancel_btn.clicked.connect(self.deleteLater)
		btn_layout.addWidget(self.cancel_btn)

		self.ok_btn = ActiveButton(Lng.confirm[JsonData.lng_index])
		self.ok_btn.clicked.connect(self.ok_clicked_cmd)
		btn_layout.addWidget(self.ok_btn)

		self.adjustSize()

	def ok_clicked_cmd(self):
		text = self.line_edit_widget.text()
		text = text.strip().replace("\n", " ")
		self.ok_clicked.emit(text)
		self.deleteLater()

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
			self.ok_clicked_cmd()
		return super().keyPressEvent(a0)



class SaveRowArrowWidget(RowArrowWidget):
	save_svg = Static.COMMON_ICONS / "save.svg"

	def __init__(self, lng_index: int):
		super().__init__(Lng.save[lng_index])
		self.set_left_icon(self.save_svg)


class MfAliasWidget(QWidget):
	changed = pyqtSignal()

	def __init__(self, lng_index: int):
		super().__init__()
		self.lng_index = lng_index

		v_layout = QVBoxLayout(self)
		v_layout.setContentsMargins(0, 0, 0, 0)
		v_layout.setSpacing(0)

		name_text = QLabel(Lng.folder_name[lng_index])
		name_text.setContentsMargins(2, 0, 2, 0)
		v_layout.addWidget(name_text)

		v_layout.addSpacing(10)

		self.line_edit = ULineEdit()
		self.line_edit.textChanged.connect(self.changed.emit)
		self.line_edit.setPlaceholderText(Lng.alias_immutable[lng_index])
		v_layout.addWidget(self.line_edit)

	def validate(self):
		pattern = r'^[A-Za-zА-Яа-яЁё0-9 ]+$'
		mf_alias = self.line_edit.text()
		error_text = None  # Переменная для хранения текста ошибки
		if not mf_alias:
			error_text = Lng.enter_alias_warning[self.lng_index]
		elif len(mf_alias) < 5 or len(mf_alias) > 50:
			error_text = f'{Lng.string_limit[self.lng_index]}'
		elif not re.fullmatch(pattern, mf_alias):
			error_text = f'{Lng.valid_message[self.lng_index]}'
		if error_text:
			win_warn = WarningWindow(error_text)
			win_warn.center_to_parent(self.window())
			win_warn.show()
			return None
		return mf_alias


class MfStopListWidget(QWidget):
	changed = pyqtSignal()

	def __init__(self, lng_index: int, mf_stop_list: list[str]):
		super().__init__()
		self.lng_index = lng_index

		v_layout = QVBoxLayout(self)
		v_layout.setContentsMargins(0, 0, 0, 0)
		v_layout.setSpacing(0)

		name_text = QLabel(Lng.ignore_list_descr[lng_index])
		name_text.setContentsMargins(2, 0, 2, 0)
		v_layout.addWidget(name_text)

		v_layout.addSpacing(10)

		self.text_edit = UTextEdit()
		self.text_edit.setPlaceholderText(Lng.ignore_list[lng_index])
		self.text_edit.textChanged.connect(self.changed.emit)
		v_layout.addWidget(self.text_edit)

		if mf_stop_list:
			self.text_edit.setPlainText("\n".join(mf_stop_list))


class FlowLayout(QLayout):
	def __init__(self, parent=None, spacing=7):
		super().__init__(parent)
		self.items = []
		self.spacing = spacing

	def clear(self):
		while self.count():
			child = self.takeAt(0)
			if child and child.widget():
				# Уничтожаем сам виджет, чтобы он не завис в памяти и на экране
				child.widget().deleteLater()
		self.update()

	def addItem(self, item):
		self.items.append(item)

	def count(self):
		return len(self.items)

	def itemAt(self, index):
		if 0 <= index < len(self.items):
			return self.items[index]
		return None

	def takeAt(self, index):
		if 0 <= index < len(self.items):
			return self.items.pop(index)
		return None

	def expandingDirections(self):
		return Qt.Orientation(0)

	def hasHeightForWidth(self):
		return True

	def heightForWidth(self, width):
		return self._do_layout(QRect(0, 0, width, 0), True)

	def setGeometry(self, rect):
		super().setGeometry(rect)
		self._do_layout(rect, False)

	def sizeHint(self):
		return self.minimumSize()

	def minimumSize(self):
		size = QSize(0, 0)

		for item in self.items:
			size = size.expandedTo(item.minimumSize())

		margins = self.contentsMargins()
		size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

		return size

	def _do_layout(self, rect, test_only):
		margins = self.contentsMargins()
		rect = rect.adjusted(
			margins.left(),
			margins.top(),
			-margins.right(),
			-margins.bottom()
		)

		x = rect.x()
		y = rect.y()
		line_height = 0

		for item in self.items:
			item_size = item.sizeHint()
			next_x = x + item_size.width() + self.spacing

			if next_x - self.spacing > rect.right() and line_height > 0:
				x = rect.x()
				y += line_height + self.spacing
				next_x = x + item_size.width() + self.spacing
				line_height = 0

			if not test_only:
				item.setGeometry(QRect(QPoint(x, y), item_size))

			x = next_x
			line_height = max(line_height, item_size.height())

		return y + line_height - rect.y() + margins.bottom()



class _SvgIconButtonContainer(TransparentLabel):
	qss_base_style = "base"
	qss_selected_style = "selected"
	qss_pressed_style = "pressed"
	attr_name = "style"

	def __init__(self):
		super().__init__()
		self.set_base()

	def set_style_state(self, state: str):
		if self.property(self.attr_name) != state:
			self.setProperty(self.attr_name, state)
			self.style().unpolish(self)
			self.style().polish(self)
			self.update()

	def set_base(self):
		self.set_style_state(self.qss_base_style)

	def set_selected(self):
		self.set_style_state(self.qss_selected_style)

	def set_pressed(self):
		self.set_style_state(self.qss_pressed_style)

	def mousePressEvent(self, ev):
		ev.ignore()

	def mouseReleaseEvent(self, ev):
		ev.ignore()


class SvgBgWidget(TransparentWidget):
	clicked_ = pyqtSignal()

	def __init__(self, svg_path: Path, container_size: tuple, icon_size: tuple):
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		# Фоновая подложка с заданным размером
		self.label = _SvgIconButtonContainer()
		self.label.setFixedSize(*container_size)

		# SVG-иконка с заданным размером
		self.svg_widget = QSvgWidget(str(svg_path), self)
		self.svg_widget.setFixedSize(*icon_size)
		self.svg_widget.setAttribute(
			Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
		)

		# Наложение иконки на фон
		layout = QGridLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		layout.addWidget(self.label, 0, 0)
		layout.addWidget(
			self.svg_widget, 0, 0,
			Qt.AlignmentFlag.AlignCenter
		)

		self.label.stackUnder(self.svg_widget)
		self.svg_widget.raise_()

	def set_selected_style(self):
		self.label.set_selected()

	def set_base_style(self):
		self.label.set_base()

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.label.set_pressed()

		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			if self.rect().contains(event.pos()):
				self.clicked_.emit()

			self.label.set_base()

		super().mouseReleaseEvent(event)


class CopyTextSvgWidget(SvgBgWidget):
	svg_path = Static.COMMON_ICONS / "copy.svg"
	green_mark = Static.COMMON_ICONS / "green_checkmark.svg"
	CLICK_COOLDOWN = 500  # мс

	def __init__(self, current_text: str, container_size: tuple, svg_size: tuple):
		super().__init__(self.svg_path, container_size, svg_size)

		self.setToolTip(Lng.copy_text[JsonData.lng_index])

		self.current_text = current_text
		self._click_locked = False

		self._cooldown_timer = QTimer(self)
		self._cooldown_timer.setSingleShot(True)
		self._cooldown_timer.setInterval(self.CLICK_COOLDOWN)
		self._cooldown_timer.timeout.connect(self._unlock_click)

	def set_current_text(self, text: str):
		self.current_text = text

	def _unlock_click(self):
		self._click_locked = False
		self.svg_widget.load(str(self.svg_path))

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			if not self._click_locked:
				self._click_locked = True
				self._cooldown_timer.start()
				Utils.pyqt_copy_text(self.current_text)
				self.svg_widget.load(str(self.green_mark))

		super().mouseReleaseEvent(event)


class MfPathWidget(UGroupBox):
	changed = pyqtSignal()
	folder_magnifier = Static.COMMON_ICONS / "folder_magnifier.svg"
	magnifier = Static.COMMON_ICONS / "magnifier.svg"
	green_checkmark = Static.COMMON_ICONS / "green_checkmark.svg"
	copy = Static.COMMON_ICONS / "copy.svg"
	icon_size = (23, 23)

	def __init__(self, lng_index: int, mf_path: str = None):
		super().__init__()
		self.setAcceptDrops(True)

		self.mf_path = mf_path
		self.lng_index = lng_index
		
		# Таймер инициализируем один раз как атрибут класса
		self.watch_timer = QTimer(self)
		self.watch_timer.timeout.connect(self.check_path_by_timer)
	
		self.main_lay = QVBoxLayout(self)
		self.main_lay.setContentsMargins(15, 8, 15, 8)
		self.main_lay.setSpacing(0)

		# Используем QStackedWidget для безопасного переключения экранов
		self.stack = QStackedWidget()
		self.main_lay.addWidget(self.stack)

		# Создаем обе панели заранее
		self.init_no_path_ui()
		self.init_ok_path_ui()

		if self.mf_path and os.path.exists(self.mf_path):
			self.show_ok_path()
		else:
			self.show_no_path()

		self.adjustSize()
		OFFSET = 60
		self.setMinimumWidth(self.width() + OFFSET)

		self.copy_path_btn_locked = False

	def init_no_path_ui(self):
		"""Создание панели 'Путь не выбран' (индекс 0 в стеке)"""
		widget = QWidget()
		main_h_layout = QHBoxLayout(widget)
		main_h_layout.setContentsMargins(0, 0, 0, 0)
		main_h_layout.setSpacing(10)

		# Контейнер для текста
		all_texts = TransparentWidget()
		main_h_layout.addWidget(all_texts)
		all_texts_layout = QVBoxLayout(all_texts)
		all_texts_layout.setContentsMargins(0, 0, 0, 0)
		all_texts_layout.setSpacing(8)

		all_texts_layout.addStretch()

		# СТРОКА 1: Заголовок
		first_row_container = TransparentWidget()
		all_texts_layout.addWidget(first_row_container)
		first_row_layout = QHBoxLayout(first_row_container)
		first_row_layout.setContentsMargins(0, 0, 0, 0)
		first_row_layout.setSpacing(10)
		
		magnifier_svg_widget = QSvgWidget()
		magnifier_svg_widget.load(str(self.folder_magnifier))
		magnifier_svg_widget.setFixedSize(*self.icon_size)
		first_row_layout.addWidget(magnifier_svg_widget)
		
		title_first_row = TitleTextLabel(Lng.folder_path[JsonData.lng_index])
		first_row_layout.addWidget(title_first_row)

		# РАЗДЕЛИТЕЛЬ
		all_texts_layout.addWidget(USep())
		all_texts_layout.addSpacing(2)

		# СТРОКА 2: Путь / Подсказка + Кнопка копирования (заглушка)
		second_row = TransparentWidget()
		all_texts_layout.addWidget(second_row)
		mf_path_layout = QHBoxLayout(second_row)
		mf_path_layout.setContentsMargins(0, 0, 0, 0)
		mf_path_layout.setSpacing(0)

		self.no_path_label = GrayTextLabel(Lng.path_hint_texts[self.lng_index])
		mf_path_layout.addWidget(self.no_path_label, stretch=1)

		# Невидимая кнопка-заглушка, удерживающая место
		self.fake_copy_btn = UPushButton("")
		self.fake_copy_btn.setIcon(QIcon(str(self.copy)))
		# Заставляем Qt сохранять геометрию кнопки, даже когда она скрыта
		sp = self.fake_copy_btn.sizePolicy()
		sp.setRetainSizeWhenHidden(True)
		self.fake_copy_btn.setSizePolicy(sp)
		self.fake_copy_btn.setVisible(False)
		mf_path_layout.addWidget(self.fake_copy_btn)

		# СТРОКА 3: Нижние кнопки управления
		buttons_container = TransparentWidget()
		all_texts_layout.addWidget(buttons_container)
		buttons_layout = QHBoxLayout(buttons_container)
		buttons_layout.setContentsMargins(0, 0, 0, 0)
		buttons_layout.setSpacing(10)

		choose_folder = UPushButton(Lng.choose_folder[JsonData.lng_index])
		choose_folder.setIcon(QIcon(str(self.magnifier)))
		choose_folder.clicked.connect(self.dialog_dir)
		buttons_layout.addWidget(choose_folder)

		all_texts_layout.addStretch()

		self.stack.addWidget(widget)

	def init_ok_path_ui(self):
		"""Создание панели 'Путь корректен' (индекс 1 в стеке)"""
		widget = QWidget()
		main_h_layout = QHBoxLayout(widget)
		main_h_layout.setContentsMargins(0, 0, 0, 0)
		main_h_layout.setSpacing(10)

		# Контейнер для текста
		all_texts = TransparentWidget()
		main_h_layout.addWidget(all_texts)
		all_texts_layout = QVBoxLayout(all_texts)
		all_texts_layout.setContentsMargins(0, 0, 0, 0)
		all_texts_layout.setSpacing(8)

		all_texts_layout.addStretch()

		# СТРОКА 1: Заголовок
		first_row_container = TransparentWidget()
		all_texts_layout.addWidget(first_row_container)
		first_row_layout = QHBoxLayout(first_row_container)
		first_row_layout.setContentsMargins(0, 0, 0, 0)
		first_row_layout.setSpacing(10)
		
		green_checkmark_widget = QSvgWidget()
		green_checkmark_widget.load(str(self.green_checkmark))
		green_checkmark_widget.setFixedSize(*self.icon_size)
		first_row_layout.addWidget(green_checkmark_widget)
		
		title_first_row = TitleTextLabel(Lng.folder_path[JsonData.lng_index])
		first_row_layout.addWidget(title_first_row)

		# РАЗДЕЛИТЕЛЬ
		all_texts_layout.addWidget(USep())
		all_texts_layout.addSpacing(2)

		# СТРОКА 2: Путь / Подсказка + Кнопка копирования (активная)
		second_row = TransparentWidget()
		all_texts_layout.addWidget(second_row)
		mf_path_layout = QHBoxLayout(second_row)
		mf_path_layout.setContentsMargins(0, 0, 0, 0)
		mf_path_layout.setSpacing(0)

		self.mf_path_label = GrayTextLabel("")
		self.mf_path_label.set_elide(True)
		mf_path_layout.addWidget(self.mf_path_label, stretch=1)

		self.copy_path_btn = UPushButton("")
		self.copy_path_btn.clicked.connect(self.copy_path)
		self.copy_path_btn.setIcon(QIcon(str(self.copy)))
		self.copy_path_btn.setToolTip(Lng.copy_dirpath[JsonData.lng_index])
		mf_path_layout.addWidget(self.copy_path_btn)

		# СТРОКА 3: Нижние кнопки управления
		buttons_container = TransparentWidget()
		all_texts_layout.addWidget(buttons_container)
		buttons_layout = QHBoxLayout(buttons_container)
		buttons_layout.setContentsMargins(0, 0, 0, 0)
		buttons_layout.setSpacing(10)

		change_btn = UPushButton(Lng.choose_folder[JsonData.lng_index])
		change_btn.setIcon(QIcon(str(self.magnifier)))
		change_btn.clicked.connect(self.dialog_dir)
		buttons_layout.addWidget(change_btn)

		all_texts_layout.addStretch()

		self.stack.addWidget(widget)



	def copy_path(self):

		def unlock():
			self.set_copy_path_btn_locked(False)
			self.copy_path_btn.setIcon(QIcon(str(self.copy)))

		if self.copy_path_btn_locked:
			return

		Utils.pyqt_copy_text(self.mf_path)
		self.copy_path_btn.setIcon(QIcon(str(self.green_checkmark)))
		self.set_copy_path_btn_locked(True)

		QTimer.singleShot(1000, unlock)

	def set_copy_path_btn_locked(self, value: bool):
		self.copy_path_btn_locked = value

	def show_no_path(self):
		"""Включение режима ожидания пути"""
		self.stack.setCurrentIndex(0)
		if not self.watch_timer.isActive():
			self.watch_timer.start(1000)  # Проверка каждую секунду

	def show_ok_path(self):
		"""Включение режима успешного пути"""
		self.watch_timer.stop()  # Важно: останавливаем таймер сразу
		self.mf_path_label.setText(self.mf_path)
		self.stack.setCurrentIndex(1)

	def check_path_by_timer(self):
		"""Срабатывание таймера"""
		if self.mf_path and os.path.exists(self.mf_path):
			self.changed.emit()
			self.show_ok_path()

	def update_path(self, new_path: str):
		"""Единый метод обновления пути из любых событий"""
		self.mf_path = new_path.rstrip(os.sep)
		self.changed.emit()
		self.show_ok_path()

	def validate(self):
		if not self.mf_path or not os.path.exists(self.mf_path):
			win_warn = WarningWindow(Lng.select_folder_path[self.lng_index])
			win_warn.center_to_parent(self.window())
			win_warn.show()
			return None
		return self.mf_path

	def dialog_dir(self):
		if not self.mf_path:
			directory = os.path.expanduser("~/Downloads")
		else:
			directory = self.mf_path
		self.dialog = QFileDialog(directory=directory)
		url = self.dialog.getExistingDirectory()
		if url and os.path.isdir(url):
			self.update_path(url)

	def dropEvent(self, a0):
		if a0.mimeData().hasUrls():
			url = a0.mimeData().urls()[0].toLocalFile()
			if url and os.path.isdir(url):
				self.update_path(url)
		return super().dropEvent(a0)
	
	def dragEnterEvent(self, a0):
		if a0.mimeData().hasUrls():  # Принимаем дроп только если это ссылки/файлы
			a0.accept()
		return super().dragEnterEvent(a0)