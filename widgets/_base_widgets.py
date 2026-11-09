import os
import re
import sys
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import (QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer,
						  pyqtSignal)
from PyQt6.QtGui import (QAction, QCloseEvent, QColor, QContextMenuEvent,
						 QFontMetrics, QIcon, QMouseEvent, QPainter,
						 QPainterPath, QPalette)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QGridLayout,
							 QGroupBox, QHBoxLayout, QLabel, QLayout,
							 QLineEdit, QListWidget, QListWidgetItem,
							 QMainWindow, QMenu, QProgressBar, QPushButton,
							 QScrollArea, QSizePolicy, QSlider, QSpinBox,
							 QStackedWidget, QStyle, QStyledItemDelegate,
							 QApplication, QStyleOptionViewItem, QTextEdit,
							 QTreeView, QTreeWidget, QTreeWidgetItem,
							 QVBoxLayout, QWidget)

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.themes import ThemeChanger
from system.utils import Utils


class TransparentButton(QPushButton):
	def __init__(self, text="", parent=None):
		super().__init__(text=text, parent=parent)


class TransparentLabel(QLabel):
	sym_line_feed = "\u000a"
	sym_paragraph_sep = "\u2029"

	def __init__(self, text="", parent=None):
		super().__init__(text or "", parent)

		self._original_text = text or ""
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

	def set_elide(self, enabled: bool = True, ignore_width: bool = True):
		self._elide_enabled = enabled
		if enabled:
			self.setMinimumWidth(0)
			policy = (QSizePolicy.Policy.Ignored if ignore_width
					  else QSizePolicy.Policy.Preferred)
			self.setSizePolicy(policy, QSizePolicy.Policy.Preferred)
		self._update_text()

	def sizeHint(self):
		hint = super().sizeHint()
		if self._elide_enabled:
			fm = QFontMetrics(self.font())
			shown_w = fm.horizontalAdvance(self.text())
			full_w = fm.horizontalAdvance(self._original_text)
			hint.setWidth(hint.width() - shown_w + full_w)
		return hint

	def minimumSizeHint(self):
		hint = super().minimumSizeHint()
		if self._elide_enabled:
			hint.setWidth(0)
		return hint

	def get_elided_text(self):
		width = self.contentsRect().width()
		if width <= 0:
			return self._original_text

		metrics = QFontMetrics(self.font())

		lines = self._original_text.splitlines()
		return '\n'.join(
			metrics.elidedText(
				line,
				Qt.TextElideMode.ElideMiddle,
				width,
			)
			for line in lines
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

		def clean(s: str) -> str:
			return s.replace(self.sym_paragraph_sep, "").replace(self.sym_line_feed, "")

		full_text = clean(self._original_text)

		# При elide выделение относится к обрезанной строке, поэтому копируем исходный текст
		if self._elide_enabled:
			copy_text = full_text
		else:
			copy_text = clean(self.selectedText()) or full_text

		menu = UMenu(parent=self)

		copy_action = QAction(Lng.copy, menu)
		copy_action.triggered.connect(
			lambda: Utils.pyqt_copy_text(copy_text)
		)
		menu.addAction(copy_action)

		if os.path.isfile(full_text) or os.path.isdir(full_text):
			reveal_action = QAction(Lng.reveal_in_finder, menu)
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
			(Lng.cut, self.cut_selection),
			(Lng.copy, lambda: Utils.pyqt_copy_text(self.selectedText())),
			(Lng.paste, self.paste_text),
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
			(Lng.cut, self.cut_selection),
			(Lng.copy, self.copy_selection),
			(Lng.paste, self.paste_text),
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
	def __init__(self):
		super().__init__()
		self.horizontalScrollBar().setDisabled(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setIconSize(QSize(16, 16))


class RoundedRowDelegate(QStyledItemDelegate):
	def paint(self, painter, option, index):
		view = option.widget
		if view is None or index.column() != 0:
			super().paint(painter, option, index)
			return

		if view.selectionModel().isSelected(index):
			text = QColor(view.theme.sel_text)
			opt = QStyleOptionViewItem(option)
			pal = QPalette(opt.palette)
			pal.setColor(QPalette.ColorRole.Text, text)
			pal.setColor(QPalette.ColorRole.HighlightedText, text)
			opt.palette = pal
			super().paint(painter, opt, index)
			return

		super().paint(painter, option, index)


class UTreeWidget(TransparentTreeWidget):
	BRANCH_ICON_X = 3   # x левого края иконки ветки от края viewport, подбирается по скриншоту
	GAP = 5  # px между левым краем подсветки и иконкой

	def __init__(self):
		super().__init__()
		self.horizontalScrollBar().setDisabled(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.setIconSize(QSize(16, 16))
		self.setHeaderHidden(True)
		self.setAutoScroll(False)
		self.setIndentation(15)
		self.setItemDelegate(RoundedRowDelegate(self))

		# Оставляем: без этой строки Qt снова рисует серый прямоугольник у branch
		pal = self.palette()
		pal.setColor(QPalette.ColorRole.Highlight, QColor(0, 0, 0, 0))
		self.setPalette(pal)

	@property
	def theme(self):
		return ThemeChanger.tree_theme

	def drawRow(self, painter, option, index):
		if self.selectionModel().isSelected(index):
			t = self.theme

			# Абсолютная позиция: одна и та же для всех строк, потому что
			# option.rect всегда начинается с края viewport
			left = max(0, self.BRANCH_ICON_X - self.GAP)

			rect = QRectF(
				left,
				option.rect.y() + t.v_margin,
				self.viewport().width() - left - t.h_margin,
				option.rect.height() - 2 * t.v_margin,
			)
			path = QPainterPath()
			path.addRoundedRect(rect, t.sel_radius, t.sel_radius)

			painter.save()
			painter.setRenderHint(QPainter.RenderHint.Antialiasing)
			painter.fillPath(path, QColor(t.sel_color))
			painter.restore()

			option = QStyleOptionViewItem(option)
			option.state &= ~QStyle.StateFlag.State_Selected

		super().drawRow(painter, option, index)


class UTreeView(TransparentTreeView):
	def __init__(self, parent=None):
		super().__init__(parent)


class UPushButton(TransparentButton):
	def __init__(self, text: str):
		self._raw_text = ""      # Инициализируем переменную для хранения чистого текста
		super().__init__("")
		self.setIconSize(QSize(12, 12))
		self.setFixedHeight(28)
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


class RedButton(UPushButton):
	def __init__(self, text):
		super().__init__(text)


class USep(TransparentFrame):
	def __init__(self):
		super().__init__()
		self.setFixedHeight(1)


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
	traffic_lights_path = Static.ICONS / "traffic_lights"

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
			icon_path = f"{self.traffic_lights_path}/unfocused.svg"
		elif self.is_pressed:
			icon_path = f"{self.traffic_lights_path}/{self.btn_type}/active.svg"
		elif self.is_group_hovered:
			icon_path = f"{self.traffic_lights_path}/{self.btn_type}/hover.svg"
		else:
			icon_path = f"{self.traffic_lights_path}/{self.btn_type}/default.svg"

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
	TRAFFIC_LIGHT_WIDTH = 0

	def __init__(self, parent: QMainWindow):
		super().__init__(parent)
		self.setFixedHeight(28)

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

	def set_custom_widget(self, widget: TransparentWidget):
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


class UFrame(TransparentFrame):
	def __init__(self, parent=None):
		super().__init__(parent)


class UBlackFrame(TransparentFrame):
	def __init__(self, parent=None):
		super().__init__(parent)


class UMainWinOverlay(TransparentWidget):
	def __init__(self, parent=None):
		"""для стилизации в qss"""
		super().__init__(parent)
		self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


class UMainWindow(QMainWindow):
	win_list: list[TransparentWidget] = []
	_focus_connected: bool = False

	def __init__(self, parent: TransparentWidget = None):
		super().__init__(parent)
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
		self.setup_window()
		UMainWindow._connect_focus_signal()

	@classmethod
	def _connect_focus_signal(cls):
		if UMainWindow._focus_connected:
			return
		app = QApplication.instance()
		app.focusWindowChanged.connect(UMainWindow._on_focus_window_changed)
		UMainWindow._focus_connected = True

	@staticmethod
	def _on_focus_window_changed(_window):
		active = QApplication.activeWindow()
		for w in list(UMainWindow.win_list):
			if isinstance(w, UMainWindow):
				w._apply_focus_state(active)

	def setWindowTitle(self, title: str):
		self.title_bar.set_title_text(title)
		return super().setWindowTitle(title)

	def setup_window(self):
		central_widget = UFrame()
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

		# Затемняющий слой поверх окна, виден когда поверх открыто другое UMainWindow
		self.dim_overlay = UMainWinOverlay(parent=self)
		self.dim_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		self.dim_overlay.hide()

		self.register_window()

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

	def center_to_parent(self, parent: TransparentWidget):
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

	def closeEvent(self, event: QCloseEvent | None):
		self.unregister_window()
		return super().closeEvent(event)

	def deleteLater(self):
		self.unregister_window()
		return super().deleteLater()

	def changeEvent(self, a0):
		if a0.type() == QEvent.Type.ActivationChange:
			self.title_bar.set_window_focused(self.isActiveWindow())
		return super().changeEvent(a0)

	def resizeEvent(self, a0):
		self.dim_overlay.setGeometry(self.rect())
		return super().resizeEvent(a0)

	def _apply_focus_state(self, active_window):
		# затемняем, только если активно другое наше UMainWindow;
		# если активна другая программа (active_window is None), ничего не меняем
		covered = isinstance(active_window, UMainWindow) and active_window is not self
		self.dim_overlay.setVisible(covered)
		if covered:
			self.dim_overlay.raise_()


# если переименовываешь, не забудь qss
class GrayTextLabel(TransparentLabel):
	def __init__(self, text: str):
		super().__init__(text)


class _TitleTextLabel(TransparentLabel):
	def __init__(self, text="", parent=None):
		super().__init__(text, parent)


# если переименовываешь, не забудь qss
class TitleTextWidget(TransparentWidget):
	def __init__(self, text: str, svg: Path = None):
		super().__init__()
		self.h_layout = QHBoxLayout(self)
		self.h_layout.setSpacing(10)
		self.h_layout.setContentsMargins(0, 0, 0, 0)

		if svg:
			self.svg_widget = QSvgWidget(str(svg))
			self.svg_widget.setFixedSize(23, 23)
			self.h_layout.addWidget(self.svg_widget)

		self.text_widget = _TitleTextLabel(text)
		self.h_layout.addWidget(self.text_widget)


# если переименовываешь, не забудь qss
class UTagWidget(TransparentFrame):
	right_svg_clicked = pyqtSignal()
	text_clicked = pyqtSignal()
	left_svg_clicked = pyqtSignal()

	qss_property_name = "style"
	qss_blue = "blue"
	qss_gray = "gray"
	qss_transparent = "transparent"
	qss_green = "green"
	qss_yellow = "yellow"
	qss_red = "red"

	def __init__(self, text: str, style: str, l_svg: Path = None, r_svg: Path = None):
		super().__init__()
		self.qss_style = style
		self.setFixedHeight(25)
		self.setProperty(UTagWidget.qss_property_name, style)
		self.set_qss_style(style)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.h_lay = QHBoxLayout(self)
		self.h_lay.setContentsMargins(7, 2, 7, 2)
		self.h_lay.setSpacing(6)
		self.h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

		if l_svg:
			self.left_svg_widget = QSvgWidget(str(l_svg))
			self.left_svg_widget.mouseReleaseEvent = self.text_widget_cmd
			self.left_svg_widget.setFixedSize(14, 14)
			self.h_lay.addWidget(self.left_svg_widget)

		if text:
			self.text_widget = TransparentLabel(text)
			self.text_widget.mouseReleaseEvent = self.text_widget_cmd
			self.h_lay.addWidget(self.text_widget)

		if r_svg:
			right_svg_wrapper = TransparentWidget()
			self.h_lay.addWidget(right_svg_wrapper)
			self.right_svg_lay = QVBoxLayout(right_svg_wrapper)
			self.right_svg_lay.setContentsMargins(0, 0, 0, 0)
			self.right_svg_lay.setSpacing(0)

			self.right_svg_widget = QSvgWidget(str(r_svg))
			self.right_svg_widget.mouseReleaseEvent = self.right_svg_cmd
			self.right_svg_widget.setFixedSize(14, 14)
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

	def __init__(self, text: str):
		super().__init__()
		self.setFixedHeight(26)
		
		# Один прямой горизонтальный слой
		self.main_layout = QHBoxLayout(self)
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(10)
		
		# Иконка слева
		self.left_icon = QSvgWidget()
		self.left_icon.setFixedSize(16, 16)
		self.left_icon.hide()
		
		# Текст
		self.text_widget = TransparentLabel(text)
		
		# Стрелка справа
		self.arrow_wid = QSvgWidget(str(Static.GRAY_ICONS / "arrow_right_gray.svg"))
		self.arrow_wid.setFixedSize(12, 12)
		
		# Сборка в один ряд
		self.main_layout.addWidget(self.left_icon)
		self.main_layout.addWidget(self.text_widget)
		self.main_layout.addStretch()
		self.main_layout.addWidget(self.arrow_wid)
		
		self.adjustSize()

	def set_left_icon(self, svg: Path):
		self.left_icon.load(str(svg))
		self.left_icon.show()

	def replace_arrow_widget(self, widget: TransparentWidget):
		self.arrow_wid.hide()
		self.main_layout.addWidget(widget)

	def hide_arrow(self):
		self.arrow_wid.hide()

	def show_warning(self):
		self.set_left_icon(Static.COLOR_ICONS / "yellow_warning.svg")

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

	def __init__(self, title: str):
		super().__init__()
		self.setWindowTitle(title)
		self.setFixedWidth(370)

		self.central_layout.setContentsMargins(10, 0, 10, 10)
		self.central_layout.setSpacing(0)
		self.show_titlebar_sep()
		self.central_layout.addSpacing(10)

		h_wid = TransparentWidget()
		self.central_layout.addWidget(h_wid)
		h_lay = QHBoxLayout(h_wid)
		h_lay.setContentsMargins(0, 0, 0, 0)
		h_lay.setSpacing(10)

		left_side_icon = QSvgWidget(str(Static.COLOR_ICONS / "copy_files.svg"))
		left_side_icon.setFixedSize(40, 40)
		h_lay.addWidget(left_side_icon)

		right_side_wid = TransparentWidget()
		right_side_lay = QVBoxLayout(right_side_wid)
		right_side_lay.setContentsMargins(0, 0, 0, 0)
		right_side_lay.setSpacing(2)
		h_lay.addWidget(right_side_wid)

		self.above_label = TransparentLabel()
		right_side_lay.addWidget(self.above_label)

		progressbar_row = TransparentWidget()
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

		self.cancel_btn = QSvgWidget(str(Static.GRAY_ICONS / "cancel_solid_gray.svg"))
		self.cancel_btn.setFixedSize(13, 13)
		self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
		progressbar_lay.addWidget(self.cancel_btn)

		self.below_label = TransparentLabel()
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

		self.btn_widget = TransparentWidget()
		self.central_layout.addWidget(self.btn_widget)

		self.btn_layout = QVBoxLayout(self.btn_widget)
		self.btn_layout.setContentsMargins(0, 0, 0, 0)
		self.btn_layout.setSpacing(6)

	def _calculate_optimal_text_width(
		self, text_wid: TransparentLabel, text: str,
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

	def _adjust_window_size(self, text_wid: TransparentLabel, text: str):
		text_wid.setFixedWidth(self._calculate_optimal_text_width(text_wid, text))

		self.icon_text_layout.activate()
		self.central_layout.activate()

		ideal_size = self.centralWidget().sizeHint()
		self.adjustSize()
		self.setFixedSize(self.width(), ideal_size.height())


class ConfirmWindow(VerticalWindow):
	ok_clicked = pyqtSignal()
	cancel_clicked = pyqtSignal()

	def __init__(self, text: str):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		# self.show_titlebar_underline()
		self.setWindowTitle(Lng.attention)

		self._setup_ui(text)
		self.central_layout.activate()
		self._adjust_window_size(self.text_wid, text)

	def _setup_ui(self, text: str):
		self.svg_widget = QSvgWidget(str(Static.COLOR_ICONS / "yellow_warning.svg"))
		self.svg_widget.setFixedSize(65, 65)
		self.icon_text_layout.addWidget(
			self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter
		)

		self.text_wid = GrayTextLabel(text)
		self.text_wid.set_selectable(True)
		self.text_wid.setWordWrap(True)
		self.icon_text_layout.addWidget(self.text_wid)

		self.ok_btn = ActiveButton(Lng.confirm)
		self.ok_btn.clicked.connect(self.ok_clicked.emit)
		self.ok_btn.clicked.connect(self.deleteLater)
		self.btn_layout.addWidget(self.ok_btn)

		self.cancel_btn = UPushButton(Lng.cancel)
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

	def __init__(self, text: str, text_edit_text: str = None):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.show_titlebar_sep()
		self.setWindowTitle(Lng.attention)

		self._setup_ui(text, text_edit_text)
		self.central_layout.activate()
		self._adjust_window_size(self.text_wid, text)

	def _setup_ui(self, text: str, text_edit_text: str):
		self.svg_widget = QSvgWidget(str(Static.COLOR_ICONS / "yellow_warning.svg"))
		self.svg_widget.setFixedSize(65, 65)
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

		self.cancel_btn = ActiveButton(Lng.got_it)
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
	def __init__(self, text: str):
		super().__init__(text)
		self.svg_widget.load(str(Static.COLOR_ICONS / "red_warning.svg"))


class InputTextWin(UMainWindow):
	ok_clicked = pyqtSignal(str)
	cancel_clicked = pyqtSignal()

	def __init__(self, description: str, svg: Path = None):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.text_input)
		self.show_titlebar_sep()
		self.central_layout.addSpacing(10)
		self.central_layout.setContentsMargins(10, 0, 10, 10)
		self.central_layout.setSpacing(0)

		svg_text_widget = TransparentWidget()
		self.central_layout.addWidget(svg_text_widget)
		svg_text_layout = QHBoxLayout(svg_text_widget)
		svg_text_layout.setContentsMargins(5, 0, 10, 0)
		svg_text_layout.setSpacing(5)

		if svg:
			svg_icon = QSvgWidget(str(svg))
			svg_icon.setFixedSize(15, 15)
			svg_text_layout.addWidget(svg_icon)

		self.description_label = GrayTextLabel(description)
		svg_text_layout.addWidget(self.description_label)

		self.central_layout.addSpacing(10)

		self.line_edit_widget = ULineEdit()
		self.line_edit_widget.setPlaceholderText(Lng.input_text)
		self.central_layout.addWidget(self.line_edit_widget)

		self.central_layout.addSpacing(10)

		btn_widget = TransparentWidget()
		self.central_layout.addWidget(btn_widget)

		btn_layout = QHBoxLayout(btn_widget)
		btn_layout.setContentsMargins(0, 0, 0, 0)
		btn_layout.setSpacing(10)

		btn_layout.addStretch()

		self.cancel_btn = UPushButton(Lng.cancel)
		self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
		self.cancel_btn.clicked.connect(self.deleteLater)
		btn_layout.addWidget(self.cancel_btn)

		self.ok_btn = ActiveButton(Lng.confirm)
		self.ok_btn.clicked.connect(self.ok_clicked_cmd)
		btn_layout.addWidget(self.ok_btn)

		self.adjustSize()
		self.setFixedSize(self.width(), self.height())

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
	def __init__(self):
		super().__init__(Lng.save)
		self.set_left_icon(Static.GRAY_ICONS / "diskette_gray.svg")


class MfAliasWidget(UGroupBox):
	changed = pyqtSignal()

	PATTERN = re.compile(r'^[A-Za-zА-Яа-яЁё0-9 ]+$')
	VALIDATE_DELAY_MS = 500

	def __init__(self):
		super().__init__()
		self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

		self.name_is_valid: bool = False

		v_layout = QVBoxLayout(self)
		v_layout.setContentsMargins(10, 5, 10, 5)
		v_layout.setSpacing(5)

		title_wrapper = TransparentWidget()
		title_lay = QHBoxLayout(title_wrapper)
		title_lay.setContentsMargins(0, 0, 0, 0)
		title_lay.setSpacing(0)

		title = TitleTextWidget(Lng.catalog_name, Static.GRAY_ICONS / "text_edit_gray.svg")
		title_lay.addWidget(title)
		title_lay.addStretch()
		v_layout.addWidget(title_wrapper)

		v_layout.addWidget(USep())

		name_text = GrayTextLabel(Lng.folder_name_full)
		name_text.setContentsMargins(0, 0, 0, 0)
		v_layout.addWidget(name_text)

		v_layout.addSpacing(5)

		self.line_edit = ULineEdit()
		self.line_edit.setPlaceholderText(Lng.alias_immutable)
		self.line_edit.textChanged.connect(self._on_text_changed)
		v_layout.addWidget(self.line_edit)

		# таймер отложенной проверки: перезапускается при каждом изменении текста
		self.validate_timer = QTimer(self)
		self.validate_timer.setSingleShot(True)
		self.validate_timer.timeout.connect(self._check_and_show)

		v_layout.addSpacing(5)

		checker_wrapper = TransparentWidget()
		checker_lay = QHBoxLayout(checker_wrapper)
		checker_lay.setContentsMargins(0, 0, 0, 0)
		checker_lay.setSpacing(5)

		self.checker_svg = QSvgWidget()
		self.checker_svg.setFixedSize(13, 13)
		checker_lay.addWidget(self.checker_svg)

		self.checker_text = GrayTextLabel("")
		self.checker_text.set_elide(True, ignore_width=False)
		self.checker_text.set_selectable(True)
		checker_lay.addWidget(self.checker_text)
		checker_lay.addStretch()
		v_layout.addWidget(checker_wrapper)

		self._show_state(None)

	# --- Отложенная проверка при вводе ---

	def _on_text_changed(self, _text: str):
		self.changed.emit()
		self.validate_timer.start(self.VALIDATE_DELAY_MS)

	def _check_and_show(self):
		self._show_state(self._get_error(self.line_edit.text()))

	def _show_state(self, error_text: str | None):
		text = self.line_edit.text()

		# единая точка обновления флага: читается при сохранении
		self.name_is_valid = bool(text) and error_text is None

		if not text:
			self.checker_svg.load(str(Static.GRAY_ICONS / "attention_gray.svg"))
			self.checker_text.setText(Lng.enter_alias_warning)
		elif error_text:
			self.checker_svg.load(str(Static.COLOR_ICONS / "yellow_warning.svg"))
			self.checker_text.setText(error_text)
		else:
			self.checker_svg.load(str(Static.COLOR_ICONS / "green_checkmark.svg"))
			self.checker_text.setText(Lng.alias_ok)

	# --- Правила проверки (одно место для ввода и для сохранения) ---

	def _get_error(self, mf_alias: str, minim=3, maxim=50) -> str | None:
		if not mf_alias:
			return Lng.enter_alias_warning
		if len(mf_alias) < minim or len(mf_alias) > maxim:
			return Lng.string_limit.format(minim=minim, maxim=maxim)
		if not self.PATTERN.fullmatch(mf_alias):
			return Lng.valid_message
		if any(i.mf_alias.lower() == mf_alias.lower() for i in Mf.items):
			return Lng.alias_taken
		return None

	def validate_and_show_win(self):
		mf_alias = self.line_edit.text()
		error_text = self._get_error(mf_alias)
		# при сохранении проверка срабатывает сразу, без ожидания таймера
		self.validate_timer.stop()
		self._show_state(error_text)
		if error_text:
			win_warn = WarningWindow(error_text)
			win_warn.center_to_parent(self.window())
			win_warn.show()
			return None
		return mf_alias


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



class _SvgWithThemeBg(TransparentLabel):
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


class SvgWithThemeBg(TransparentWidget):
	clicked_ = pyqtSignal()

	def __init__(self, svg: Path, container_size: tuple, icon_size: tuple):
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		# Фоновая подложка с заданным размером
		self.label = _SvgWithThemeBg()
		self.label.setFixedSize(*container_size)

		# SVG-иконка с заданным размером
		self.svg_widget = QSvgWidget(str(svg), self)
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


class MfPathWidget(UGroupBox):
	changed = pyqtSignal()

	def __init__(self, mf: Mf = None):
		super().__init__()
		self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
		self.setAcceptDrops(True)
		self.copy_path_btn_locked = False
		self.mf = mf
		self.title_ = Lng.catalog_path
		self.mf_path = mf.mf_paths[0] if mf else None
		self._title_icon = None
		self.title = None

		self.watch_timer = QTimer(self)
		self.watch_timer.timeout.connect(self.check_path_by_timer)

		self.v_lay = QVBoxLayout(self)
		self.v_lay.setContentsMargins(10, 5, 10, 5)
		self.v_lay.setSpacing(5)

		self.title_widget = TitleTextWidget(Lng.catalog_path, Static.COLOR_ICONS / "green_checkmark.svg")
		self.v_lay.addWidget(self.title_widget)

		# заголовок создаётся в _set_title_icon, здесь только разделитель и описание
		self.v_lay.addWidget(USep())

		self.path_label = GrayTextLabel("")
		self.path_label.setWordWrap(True)
		self.path_label.set_elide(True)
		self.v_lay.addWidget(self.path_label)

		self.v_lay.addLayout(self._create_buttons_layout())

		self.update_ui()

	def _create_buttons_layout(self) -> QHBoxLayout:
		buttons_layout = QHBoxLayout()
		buttons_layout.setContentsMargins(0, 5, 0, 0)
		buttons_layout.setSpacing(10)

		self.choose_btn = UPushButton(Lng.choose_folder)
		self.choose_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "magnifier_gray.svg")))
		self.choose_btn.clicked.connect(self.dialog_dir)
		buttons_layout.addWidget(self.choose_btn)

		# buttons_layout.addStretch()

		self.copy_path_btn = UPushButton(Lng.copy_dirpath)
		self.copy_path_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "copy_gray.svg")))
		self.copy_path_btn.setToolTip(Lng.copy_dirpath)
		self.copy_path_btn.clicked.connect(self.copy_path)
		buttons_layout.addWidget(self.copy_path_btn)

		buttons_layout.addStretch()

		return buttons_layout

	def _path_exists(self) -> bool:
		return bool(self.mf_path) and os.path.exists(self.mf_path)

	def update_ui(self):
		"""Обновляет заголовок, описание, кнопки и таймер по текущему пути"""
		has_path = self._path_exists()

		if has_path:
			self.title_widget.svg_widget.load(str(Static.COLOR_ICONS / "green_checkmark.svg"))
			self.path_label.setText(self.mf_path)
			self.watch_timer.stop()
			self.copy_path_btn.show()
		else:
			self.title_widget.svg_widget.load(str(Static.COLOR_ICONS / "yellow_warning.svg"))
			self.path_label.setText(Lng.path_hint_texts)
			if not self.watch_timer.isActive():
				self.watch_timer.start(1000)  # Проверка каждую секунду
			self.copy_path_btn.hide()

	def copy_path(self):

		def unlock():
			self.set_copy_path_btn_locked(False)
			try:
				self.copy_path_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "copy_gray.svg")))
			except RuntimeError:
				# на случай если окно уничтожилось раньше действия
				pass

		if self.copy_path_btn_locked or not self._path_exists():
			return

		Utils.pyqt_copy_text(self.mf_path)
		self.copy_path_btn.setIcon(QIcon(str(Static.COLOR_ICONS / "green_checkmark.svg")))
		self.set_copy_path_btn_locked(True)

		QTimer.singleShot(1000, unlock)

	def set_copy_path_btn_locked(self, value: bool):
		self.copy_path_btn_locked = value

	def check_path_by_timer(self):
		"""Срабатывание таймера в режиме ожидания пути"""
		if self._path_exists():
			self.changed.emit()
			self.update_ui()

	def update_path(self, new_path: str):
		"""Единый метод обновления пути из любых событий"""
		self.mf_path = new_path.rstrip(os.sep)
		self.changed.emit()
		self.update_ui()

	def validate_and_show_win(self):
		if not self._path_exists():
			win_warn = WarningWindow(Lng.select_folder_path)
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
