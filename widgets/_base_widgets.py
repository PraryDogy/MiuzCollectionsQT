import os
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import (QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer,
                          pyqtSignal)
from PyQt6.QtGui import (QAction, QCloseEvent, QColor, QContextMenuEvent,
                         QFontMetrics, QIcon, QPainter, QPainterPath, QPalette)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFrame,
                             QGroupBox, QHBoxLayout, QLabel, QLayout,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QProgressBar, QPushButton,
                             QScrollArea, QSizePolicy, QSlider, QSpinBox,
                             QStyle, QStyledItemDelegate, QStyleOptionViewItem,
                             QTableWidget, QTextEdit, QTreeView, QTreeWidget,
                             QTreeWidgetItem, QVBoxLayout, QWidget)

from cfg import Static
from system.items import Mf, RootProbe
from system.lang import Lng
from system.themes import ThemeChanger
from system.utils import Utils


class TransparentButton(QPushButton):
	pass


class TransparentLabel(QLabel):
	sym_line_feed = "\u000a"
	sym_paragraph_sep = "\u2029"

	def __init__(self, text="", parent=None):
		super().__init__(text or "", parent)
		self._original_text = text or ""
		self._elide_enabled = False
		self._context_menu_enabled = False
		self._underline = False

		# исходные настройки, к которым возвращаемся при выключении elide
		self._base_policy = self.sizePolicy()
		self._base_min_width = self.minimumWidth()

		# tooltip, который ставит сам элидинг; пользовательский tooltip не трогаем
		self._auto_tooltip = False

	# --- Стиль ---

	def set_style(
			self,
			color: Literal["regular", "gray", "accent"],
			size: Literal["regular", "small", "big"],
			weight: Literal["regular", "bold"]
	):
		values = {
			"state": color,
			"text_size": size,
			"text_weight": weight,
		}
		for k, v in values.items():
			self.setProperty(k, v)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def set_state(self, state: str):
		self.setProperty("state", state)

	def get_state(self) -> str:
		return self.property("state")

	# --- Текст ---

	def setText(self, text: str):
		self._original_text = text or ""
		self._update_text()

	def text_full(self) -> str:
		"""Исходный текст без элидинга."""
		return self._original_text

	def _update_text(self):
		text = (
			self.get_elided_text()
			if self._elide_enabled
			else self._original_text
		)

		# без изменения текста не дергаем QLabel, иначе resizeEvent даёт лишние перерисовки
		if text != self.text():
			QLabel.setText(self, text)

		self._apply_auto_tooltip(text)

	def _apply_auto_tooltip(self, shown: str):
		want_tip = self._elide_enabled and shown != self._original_text
		if want_tip:
			self.setToolTip(self._original_text)
			self._auto_tooltip = True
		elif self._auto_tooltip:
			self.setToolTip("")
			self._auto_tooltip = False

	# --- Выделение и меню ---

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

	# --- Элидинг ---

	def set_elide(self, enabled: bool = True, ignore_width: bool = True):
		self._elide_enabled = enabled
		if enabled:
			self.setMinimumWidth(0)
			policy = (QSizePolicy.Policy.Ignored if ignore_width
					  else QSizePolicy.Policy.Preferred)
			self.setSizePolicy(policy, QSizePolicy.Policy.Preferred)
		else:
			self.setMinimumWidth(self._base_min_width)
			self.setSizePolicy(self._base_policy)
		self._update_text()

	def get_elided_text(self) -> str:
		width = self.contentsRect().width()
		if width <= 0:
			return self._original_text

		metrics = QFontMetrics(self.font())
		lines = self._original_text.splitlines() or [""]
		return "\n".join(
			metrics.elidedText(line, Qt.TextElideMode.ElideMiddle, width)
			for line in lines
		)

	def refresh_elide(self):
		"""Пересчёт сокращения, например после того как появилась ширина."""
		if self._elide_enabled:
			self._update_text()

	# --- Размеры ---

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

	def resizeEvent(self, event):
		super().resizeEvent(event)
		if self._elide_enabled:
			self._update_text()

	# --- Контекстное меню ---

	def contextMenuEvent(self, ev: QContextMenuEvent):
		if not self._context_menu_enabled:
			return super().contextMenuEvent(ev)

		def clean(s: str) -> str:
			return s.replace(self.sym_paragraph_sep, "").replace(self.sym_line_feed, "")

		full_text = clean(self._original_text)

		# при элидинге выделение относится к обрезанной строке, поэтому копируем исходный текст
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
	pass


class TransparentWidget(QWidget):
	pass


class TransparentLineEdit(QLineEdit):
	pass


class TransparentTextEdit(QTextEdit):
	pass

class TransparentMenu(QMenu):
	pass


class TransparentScrollArea(QScrollArea):
	pass


class UGroupBox(QGroupBox):
	pass


class UTableWidget(QTableWidget):
	pass


class HoverGroupBox(UGroupBox):
	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)
		self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
		self.setProperty("hovered", False)

	def _set_hovered(self, value: bool):
		if self.property("hovered") == value:
			return
		self.setProperty("hovered", value)
		# перерисовываем стиль с учётом нового значения свойства
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def enterEvent(self, event):
		self._set_hovered(True)
		super().enterEvent(event)

	def leaveEvent(self, event):
		self._set_hovered(False)
		super().leaveEvent(event)


class TransparentListWidget(QListWidget):
	pass


class TransparentTreeWidget(QTreeWidget):
	pass


class TransparentTreeView(QTreeView):
	pass


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
	def __init__(self, parent: QTreeWidget | QTreeWidgetItem, texts: str | list[str]):
		if isinstance(texts, str):
			texts = [texts]
		super().__init__(parent, texts)


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


class AccentButton(UPushButton):
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
		self.central_layout.setContentsMargins(10, 5, 10, 10)
		self.central_layout.setSpacing(10)

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


class TitleWidget(TransparentWidget):
	def __init__(self, title: str, descr: str = None, title_svg: Path = None, sep: bool = True):
		super().__init__()
		self.v_lay = QVBoxLayout(self)
		self.v_lay.setContentsMargins(0, 0, 0, 0)
		self.v_lay.setSpacing(5)

		self.title_widget = TitleTextWidget(title, title_svg)
		self.v_lay.addWidget(self.title_widget)

		if sep:
			self.sep = USep()
			self.v_lay.addWidget(self.sep)

		if descr:
			self.description_widget = TransparentLabel(descr)
			self.description_widget.setWordWrap(True)
			self.description_widget.set_style("gray", "regular", "regular")
			self.v_lay.addWidget(self.description_widget)

	def add_title_button(self, widget: TransparentButton):
		self.title_widget.h_layout.addStretch()
		self.title_widget.h_layout.addWidget(widget)

	def set_margins(self, l, t, r, b):
		self.v_lay.setContentsMargins(l, t, r, b)



# если переименовываешь, не забудь qss
class TagWidget(TransparentFrame):
	right_svg_clicked = pyqtSignal()
	clicked = pyqtSignal()

	qss_property_name = "style"
	qss_blue = "blue"
	qss_gray = "gray"
	qss_transparent = "transparent"
	qss_green = "green"
	qss_yellow = "yellow"
	qss_red = "red"

	def __init__(self, text: str = None, l_svg: Path = None, r_svg: Path = None, max_text_width: int = 150):
		super().__init__()
		self.qss_style = self.qss_gray
		self.setFixedHeight(25)
		self.setProperty(self.qss_property_name, self.qss_gray)
		self.set_qss_style(self.qss_gray)
		self.setCursor(Qt.CursorShape.PointingHandCursor)

		self.h_lay = QHBoxLayout(self)
		self.h_lay.setContentsMargins(7, 2, 7, 2)
		self.h_lay.setSpacing(6)
		self.h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

		if l_svg:
			self.left_svg_widget = QSvgWidget(str(l_svg))
			self.left_svg_widget.setFixedSize(14, 14)
			self.h_lay.addWidget(self.left_svg_widget)

		text = text if text else ""
		self.text_widget = TransparentLabel(text)
		self.text_widget.setMaximumWidth(max_text_width)
		self.text_widget.set_elide(True, ignore_width=False)
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
		self.setProperty(self.qss_property_name, qss_style)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def right_svg_cmd(self, *args):
		self.right_svg_clicked.emit()

	def mouseReleaseEvent(self, a0):
		self.clicked.emit()
		return super().mouseReleaseEvent(a0)


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
		self.arrow_wid = QSvgWidget(str(Static.GRAY_ICONS / "arrow_right.svg"))
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

		self.cancel_btn = QSvgWidget(str(Static.GRAY_ICONS / "cancel_solid.svg"))
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


class VerticalWin(UMainWindow):
	WIDTH = 250

	def __init__(self):
		super().__init__()
		self.setFixedWidth(self.WIDTH)
		self.set_always_on_top()
		self.set_close_only()
		self.show_titlebar_sep()
		self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
		self.central_layout.setSpacing(3)

		self.button_layout = None
		self.text_layout = None

	def create_button_layout(self):
		self.button_widget = TransparentWidget()
		self.button_layout = QVBoxLayout(self.button_widget)
		self.button_layout.setContentsMargins(0, 5, 0, 5)
		self.button_layout.setSpacing(6)
		self.central_layout.addWidget(self.button_widget)
		return self.button_layout

	def create_text_layout(self, margin: int = 5):
		# обертка для текста с полями: лейблы внутри получают ширину без полей
		self.text_wrapper = TransparentWidget()
		self.text_layout = QVBoxLayout(self.text_wrapper)
		self.text_layout.setContentsMargins(margin, 0, margin, 0)
		self.text_layout.setSpacing(5)
		self.central_layout.addWidget(self.text_wrapper)
		return self.text_layout

	def fit_label(self, label: QLabel):
		# ширина, доступная лейблу: окно минус поля central_layout и text_layout
		cm = self.central_layout.contentsMargins()
		label_w = self.WIDTH - cm.left() - cm.right()
		if self.text_layout is not None:
			tm = self.text_layout.contentsMargins()
			label_w -= tm.left() + tm.right()

		label.setWordWrap(True)
		label.setFixedWidth(label_w)
		label_h = label.heightForWidth(label_w)
		if label_h <= 0:
			label_h = label.sizeHint().height()
		label.setFixedHeight(label_h)

	def finish_layout(self):
		self.central_layout.activate()
		self.adjustSize()

	def set_width(self, width: int):
		self.WIDTH = width
		self.setFixedWidth(width)
		self.fit_label(self.description_label)
		self.finish_layout()


class AllertWin(VerticalWin):
	BUTTONS: dict[str, UPushButton] = {
		"red": RedButton,
		"blue": ActiveButton,
		"regular": UPushButton
	}
	ICONS = {
		"red": "red_warning.svg",
		"blue": "info.svg",
		"yellow": "yellow_warning.svg",
		"green": "green_checkmark.svg",
	}

	ok_clicked = pyqtSignal()
	cancel_clicked = pyqtSignal()

	def __init__(
		self,
		text: str,
		confirm_btn: Literal["red", "blue", "regular"],
		icon: Literal["red", "blue", "yellow", "green"],
	):
		super().__init__()
		self.confirm_button_cls = self.BUTTONS[confirm_btn]
		self.icon_path = str(Static.COLOR_ICONS / self.ICONS[icon])

		self.setWindowTitle(Lng.attention)
		self._setup_ui(text)
		self.finish_layout()

	def _setup_ui(self, text: str):
		self.svg_widget = QSvgWidget(self.icon_path)
		self.svg_widget.setFixedSize(65, 65)
		self.central_layout.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)
		self.central_layout.addSpacing(5)

		text_layout = self.create_text_layout()

		self.description_label = TransparentLabel(text)
		self.description_label.set_style("gray", "regular", "regular")
		self.description_label.set_selectable(True)
		self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		text_layout.addWidget(self.description_label)
		self.fit_label(self.description_label)

		self.button_layout = self.create_button_layout()
		self.confirm_btn: UPushButton = self.confirm_button_cls(Lng.confirm)
		self.confirm_btn.clicked.connect(self.on_confirm)
		self.button_layout.addWidget(self.confirm_btn)

	def on_confirm(self):
		self.ok_clicked.emit()
		self.deleteLater()

	def on_cancel(self):
		self.cancel_clicked.emit()
		self.deleteLater()

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Escape:
			self.on_cancel()
		else:
			super().keyPressEvent(event)


class ConfirmWin(AllertWin):
	def __init__(
		self,
		text: str,
		confirm_btn: Literal["red", "blue", "regular"],
		icon: Literal["red", "blue", "yellow", "green"],
	):
		super().__init__(text, confirm_btn, icon)
		self.cancel_btn = UPushButton(Lng.cancel)
		self.cancel_btn.clicked.connect(self.on_cancel)
		self.button_layout.addWidget(self.cancel_btn)


class InputTextWin(UMainWindow):
	ok_clicked = pyqtSignal(str)

	def __init__(self, title: str, description: str):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(title)
		self.show_titlebar_sep()
		self.central_layout.setSpacing(10)
		self.central_layout.setContentsMargins(10, 5, 10, 10)

		text = " " + description
		self.description_label = TransparentLabel(text)
		# self.description_label.setWordWrap(True)
		self.description_label.set_style("gray", "regular", "regular")
		self.central_layout.addWidget(self.description_label)

		self.line_edit_widget = ULineEdit()
		self.line_edit_widget.setPlaceholderText(Lng.input_text)
		self.central_layout.addWidget(self.line_edit_widget)

		# self.central_layout.addSpacing(5)

		btn_widget = TransparentWidget()
		self.central_layout.addWidget(btn_widget)

		btn_layout = QHBoxLayout(btn_widget)
		btn_layout.setContentsMargins(0, 0, 0, 0)
		btn_layout.setSpacing(5)

		reset_btn = UPushButton(Lng.reset)
		reset_btn.clicked.connect(self.line_edit_widget.clear)
		btn_layout.addWidget(reset_btn)

		btn_layout.addStretch()

		self.cancel_btn = UPushButton(Lng.close)
		self.cancel_btn.clicked.connect(self.deleteLater)
		btn_layout.addWidget(self.cancel_btn)

		self.ok_btn = ActiveButton(Lng.apply)
		self.ok_btn.clicked.connect(self.ok_clicked_cmd)
		btn_layout.addWidget(self.ok_btn)

		self.adjustSize()
		self.setFixedSize(300, self.height())

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
		self.set_left_icon(Static.GRAY_ICONS / "diskette.svg")


class MfAliasWidget(TransparentWidget):
	changed = pyqtSignal()
	auto_name_clicked = pyqtSignal()

	VALIDATE_DELAY_MS = 500
	MINIM = 3
	MAXIM = 30

	def __init__(self):
		super().__init__()
		self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

		self.name_is_valid: bool = False

		v_layout = QVBoxLayout(self)
		v_layout.setContentsMargins(5, 0, 5, 0)
		v_layout.setSpacing(5)

		title = TitleWidget(
			Lng.catalog_name,
			Lng.folder_name_full.format(minim=self.MINIM, maxim=self.MAXIM)
		)
		v_layout.addWidget(title)


		autoname_button = UPushButton(Lng.auto_name)
		autoname_button.setIcon(QIcon(str(Static.GRAY_ICONS / "wand.svg")))
		autoname_button.clicked.connect(self.auto_name_clicked.emit)
		title.add_title_button(autoname_button)

		self.line_edit = ULineEdit()
		self.line_edit.setPlaceholderText(Lng.alias_immutable)
		self.line_edit.textChanged.connect(self._on_text_changed)
		v_layout.addWidget(self.line_edit)

		# таймер отложенной проверки: перезапускается при каждом изменении текста
		self.validate_timer = QTimer(self)
		self.validate_timer.setSingleShot(True)
		self.validate_timer.timeout.connect(self._check_and_show)

		checker_wrapper = TransparentWidget()
		checker_lay = QHBoxLayout(checker_wrapper)
		checker_lay.setContentsMargins(0, 0, 0, 0)
		checker_lay.setSpacing(5)

		self.checker_svg = QSvgWidget()
		self.checker_svg.setFixedSize(13, 13)
		checker_lay.addWidget(self.checker_svg)

		self.checker_text = TransparentLabel("")
		# self.checker_text.set_state("gray")
		self.checker_text.set_elide(True, ignore_width=False)
		self.checker_text.set_selectable(True)
		checker_lay.addWidget(self.checker_text)
		checker_lay.addStretch()
		v_layout.addWidget(checker_wrapper)

		self._show_state(None)

	# --- Отложенная проверка при вводе ---

	def set_mf_name(self, text: str):
		self.line_edit.setText(text)

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
			self.checker_svg.load(str(Static.COLOR_ICONS / "yellow_warning.svg"))
			self.checker_text.setText(Lng.enter_alias_warning)
		elif error_text:
			self.checker_svg.load(str(Static.COLOR_ICONS / "yellow_warning.svg"))
			self.checker_text.setText(error_text)
		else:
			self.checker_svg.load(str(Static.COLOR_ICONS / "green_checkmark.svg"))
			self.checker_text.setText(Lng.alias_ok)

	# --- Правила проверки (одно место для ввода и для сохранения) ---

	def _get_error(self, mf_alias: str) -> str | None:
		if not mf_alias:
			return Lng.enter_alias_warning
		if len(mf_alias) < self.MINIM or len(mf_alias) > self.MAXIM:
			return Lng.string_limit.format(minim=self.MINIM, maxim=self.MAXIM)
		# if not self.PATTERN.fullmatch(mf_alias):
			# return Lng.valid_message
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
			win_warn = AllertWin(error_text, "blue", "yellow")
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


class SvgBg(TransparentLabel):
	clicked_ = pyqtSignal()

	def __init__(self, svg: Path, ww0: int, ww1: int):
		"""
		ww0: размер подложки
		ww1: размер svg внутри подложки
		"""
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setFixedSize(ww0, ww0)
		self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
		self.setProperty("style", "base")

		self.svg_widget = QSvgWidget(str(svg), self)
		self.svg_widget.setFixedSize(ww1, ww1)
		self.svg_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
		self.svg_widget.move((ww0 - ww1) // 2, (ww0 - ww1) // 2)

	def _set_style_state(self, state: str):
		if self.property("style") == state:
			return
		self.setProperty("style", state)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def set_selected_style(self):
		self._set_style_state("selected")

	def set_base_style(self):
		self._set_style_state("base")

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self._set_style_state("pressed")
		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			if self.rect().contains(event.pos()):
				self.clicked_.emit()
			self._set_style_state("base")
		super().mouseReleaseEvent(event)


class ChoosePathWidget(TransparentFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		# мышь проходит сквозь строку к MfPathWidget
		for w in (self, ):
			w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

		lay = QHBoxLayout(self)
		lay.setContentsMargins(10, 10, 10, 10)
		lay.setSpacing(10)

		self.icon = QSvgWidget()
		self.icon.setFixedSize(26, 26)
		self.icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		lay.addWidget(self.icon)

		text_wrapper = TransparentWidget()
		text_wrapper.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		lay.addWidget(text_wrapper)
		text_lay = QVBoxLayout(text_wrapper)
		text_lay.setContentsMargins(0, 0, 0, 0)
		text_lay.setSpacing(0)

		self.status_label = TransparentLabel("")
		self.status_label.set_style("regular", "regular", "bold")
		self.status_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		text_lay.addWidget(self.status_label)

		self.path_label = TransparentLabel("")
		self.path_label.set_style("regular", "regular", "regular")
		self.path_label.set_elide(True)
		self.path_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		text_lay.addWidget(self.path_label)

		self.set_state("warn")

	def set_hovered(self, value: bool):
		"""Вызывается из MfPathWidget: наведение на весь блок, а не на строку."""
		new_value = "true" if value else "false"
		if self.property("hovered") == new_value:
			return
		self.setProperty("hovered", new_value)
		for w in (self, self.status_label, self.path_label):
			w.style().unpolish(w)
			w.style().polish(w)
		self.update()

	def set_state(self, state: str):
		"""state: 'ok' или 'warn'. Меняет свойство, стиль переприменяется."""
		if self.property("state") == state:
			return
		self.setProperty("state", state)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def set_bad(self):
		self.icon.load(str(Static.COLOR_ICONS / "yellow_warning.svg"))
		self.status_label.setText(Lng.no_catalog_path)
		self.status_label.set_state("warn")
		self.path_label.setText(Lng.press_choose_catalog)
		self.set_state("warn")

	def set_good(self, path: str, lng: str):
		self.icon.load(str(Static.COLOR_ICONS / "green_checkmark.svg"))
		self.status_label.setText(lng)
		self.status_label.set_state("ok")
		self.path_label.setText(path)
		self.set_state("ok")


class MfPathWidget(HoverGroupBox):
	changed = pyqtSignal()
	user_busy = pyqtSignal(bool)   # True — открыт диалог выбора папки

	def __init__(self, mf: Mf = None):
		super().__init__()
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
		self.setAcceptDrops(True)
		self.mf = mf
		self.draft_mf_path = mf.mf_path if mf else None

		main_lay = QHBoxLayout(self)
		main_lay.setContentsMargins(10, 5, 10, 5)
		main_lay.setSpacing(10)

		content = TransparentWidget()
		content_lay = QVBoxLayout(content)
		content_lay.setContentsMargins(0, 0, 0, 0)
		content_lay.setSpacing(5)

		self.title_widget = TitleWidget(
			Lng.catalog_path,
			Lng.catalog_path_descr,
			Static.COLOR_ICONS / "finder.svg",
			sep=False
		)
		content_lay.addWidget(self.title_widget)

		content_lay.addSpacing(5)

		status_wrap = TransparentWidget()
		content_lay.addWidget(status_wrap)
		status_lay = QHBoxLayout(status_wrap)
		status_lay.setContentsMargins(0, 0, 0, 0)
		status_lay.setSpacing(0)
		self.status = ChoosePathWidget()
		status_lay.addWidget(self.status)

		self.start_btn = QSvgWidget(str(Static.GRAY_ICONS / "arrow_right.svg"))
		self.start_btn.setFixedSize(15, 15)

		main_lay.addWidget(content)
		main_lay.addWidget(self.start_btn)

		self.update_ui()

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.pos()):
			self.dialog_dir()
		super().mouseReleaseEvent(event)

	def enterEvent(self, a0):
		super().enterEvent(a0)
		self.status.set_hovered(True)

	def leaveEvent(self, a0):
		super().leaveEvent(a0)
		self.status.set_hovered(False)

	def _path_exists(self) -> bool:
		return bool(self.draft_mf_path) and RootProbe.is_available(self.draft_mf_path)

	def update_ui(self):
		if self._path_exists():
			self.setToolTip(self.draft_mf_path)
			self.status.set_good(self.draft_mf_path, lng=Lng.ok_catalog_path)
		else:
			self.setToolTip(Lng.find_catalog)
			self.status.set_bad()

	def update_path(self, new_path: str):
		"""Единый метод обновления пути из любых событий"""
		self.draft_mf_path = new_path.rstrip(os.sep)
		self.changed.emit()
		self.update_ui()

	def validate_and_show_win(self):
		if not self._path_exists():
			win_warn = AllertWin(Lng.select_catalog_path, "blue", "yellow")
			win_warn.center_to_parent(self.window())
			win_warn.show()
			return None
		return self.draft_mf_path

	def dialog_dir(self):
		if not self.draft_mf_path:
			directory = os.path.expanduser("~/Downloads")
		else:
			directory = self.draft_mf_path
		self.user_busy.emit(True)
		try:
			self.dialog = QFileDialog(directory=directory)
			url = self.dialog.getExistingDirectory()
		finally:
			self.user_busy.emit(False)
		if url and os.path.isdir(url):
			self.update_path(url)

	def dropEvent(self, a0):
		if a0.mimeData().hasUrls():
			url = a0.mimeData().urls()[0].toLocalFile()
			if url and os.path.isdir(url):
				self.update_path(url)
		return super().dropEvent(a0)

	def dragEnterEvent(self, a0):
		if a0.mimeData().hasUrls():
			a0.accept()
		return super().dragEnterEvent(a0)