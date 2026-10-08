import os
import re
import sys
from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QAction, QCloseEvent, QColor, QContextMenuEvent,
                         QIcon, QMouseEvent, QPainter, QPixmap)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QFrame, QGroupBox,
                             QHBoxLayout, QLabel, QLayout, QLineEdit,
                             QListWidget, QListWidgetItem, QMainWindow, QMenu,
                             QProgressBar, QPushButton, QScrollArea, QSlider,
                             QSpacerItem, QSpinBox, QStackedWidget, QTextEdit,
                             QTreeView, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QWidget)
from qframelesswindow import FramelessMainWindow, StandardTitleBar
from typing_extensions import Optional

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
        self._context_menu_enabled = False

    def set_font_size(self, value_px: int):
        font = self.font()
        font.setPixelSize(value_px)
        self.setFont(font)

    def set_selectable(self, enabled: bool):
        if enabled:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.setCursor(Qt.CursorShape.IBeamCursor)
        else:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            self.unsetCursor()

    def set_context_menu(self, enabled: bool):
        self._context_menu_enabled = enabled

    def contextMenuEvent(self, ev: QContextMenuEvent):
        if not self._context_menu_enabled:
            return super().contextMenuEvent(ev)

        text = self.selectedText().replace(self.sym_paragraph_sep, "").replace(self.sym_line_feed, "")
        full_text = self.text().replace(self.sym_paragraph_sep, "").replace(self.sym_line_feed, "")

        menu = UMenu(parent=self)

        copy_action = QAction(Lng.copy[JsonData.lng_index], menu)
        copy_action.triggered.connect(lambda: Utils.pyqt_copy_text(text))
        menu.addAction(copy_action)

        if os.path.isfile(full_text) or os.path.isdir(full_text):
            reveal_action = QAction(Lng.reveal_in_finder[JsonData.lng_index], menu)
            reveal_action.triggered.connect(lambda: Utils.macos_reveal_files([full_text]))
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


class UTitleBar(StandardTitleBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)

        self.center_title = QLabel(self)
        self.center_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.center_title.setGeometry(0, 0, self.width(), self.height())

    def setTitle(self, title: str):
        self.center_title.setText(title)


class UBaseWindow(FramelessMainWindow):
	win_list: list[QWidget] = []
	bar_height = 30

	def __init__(self, parent: QWidget = None):
		super().__init__(parent)
		self.setup_window()

	def setup_window(self):
		title_bar = UTitleBar(self)
		self.setTitleBar(title_bar)

		central_widget = TransparentFrame()
		self.setCentralWidget(central_widget)

		self.central_layout = QVBoxLayout(central_widget)
		self.central_layout.setContentsMargins(5, 5, 5, 5)
		self.central_layout.setSpacing(0)
		self.central_layout.addSpacing(self.bar_height)

		# macOS
		if sys.platform == "darwin":
			self.setSystemTitleBarButtonVisible(True)
			self.titleBar.minBtn.hide()
			self.titleBar.maxBtn.hide()
			self.titleBar.closeBtn.hide()

		self.register_window()
		title_bar.raise_()

	def insert_sep(self):
		index = 1
		sep = USep()
		self.central_layout.insertWidget(index, sep)

	def get_titlebar_layout(self) -> QLayout:
		return self.titleBar.layout()

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
		flags = Qt.WindowType.CustomizeWindowHint
		flags |= Qt.WindowType.WindowCloseButtonHint
		self.setWindowFlags(flags)

	def closeEvent(self, event: QCloseEvent | None):
		self.unregister_window()
		return super().closeEvent(event)

	def deleteLater(self):
		self.unregister_window()
		return super().deleteLater()


class UMainWindow(UBaseWindow):
	pass


class UMainWidget(UBaseWindow):
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


class SelectableLabel(TransparentLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.set_selectable(True)
        self.set_context_menu(True)


class SelectableGrayLabel(GrayTextLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.set_selectable(True)
        self.set_context_menu(True)


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



class WinProgressbar(UMainWidget):
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
        self.insert_sep()
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


class ConfirmWindow(UMainWidget):
	ok_clicked = pyqtSignal()
	cancel_clicked = pyqtSignal()
	
	icon_path = Static.COMMON_ICONS / "yellow_warning.svg"
	icon_size = 40

	def __init__(self, text: str):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.insert_sep()
		self.setWindowTitle(Lng.attention[JsonData.lng_index])

		# 1. Создаем и компонуем все виджеты
		self._setup_ui(text)
		# 2. Даем layout первично рассчитаться
		self.central_layout.activate()
		# 3. Рассчитываем и фиксируем итоговые размеры на основе вашей логики с коэффициентом 1.15
		self._adjust_window_size(text)

	def _setup_ui(self, text: str):
		self.central_layout.setContentsMargins(15, 0, 10, 10)
		self.central_layout.setSpacing(0)
		self.central_layout.addSpacing(10)

		self.content_widget = TransparentWidget()
		self.central_layout.addWidget(self.content_widget)

		content_layout = QHBoxLayout(self.content_widget)
		content_layout.setContentsMargins(0, 0, 0, 0)
		content_layout.setSpacing(15)

		self.svg_widget = QSvgWidget()
		self.svg_widget.load(str(self.icon_path))
		self.svg_widget.setFixedSize(self.icon_size, self.icon_size)
		content_layout.addWidget(self.svg_widget)

		text_container = TransparentWidget()
		content_layout.addWidget(text_container)

		text_layout = QVBoxLayout(text_container)
		text_layout.setContentsMargins(0, 0, 0, 0)
		text_layout.setSpacing(5)

		self.text_wid = SelectableGrayLabel(text)
		self.text_wid.setWordWrap(True)
		text_layout.addWidget(self.text_wid)

		self.central_layout.addSpacing(10)

		self.btn_widget = QWidget()
		self.central_layout.addWidget(self.btn_widget)

		self.btn_layout = QHBoxLayout(self.btn_widget)
		self.btn_layout.setContentsMargins(0, 0, 0, 0)
		self.btn_layout.setSpacing(10)
		self.btn_layout.addStretch(1)

		self.cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
		self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
		self.cancel_btn.clicked.connect(self.deleteLater)
		self.btn_layout.addWidget(self.cancel_btn)

		self.ok_btn = ActiveButton(Lng.confirm[JsonData.lng_index])
		self.ok_btn.clicked.connect(self.ok_clicked.emit)
		self.ok_btn.clicked.connect(self.deleteLater)
		self.btn_layout.addWidget(self.ok_btn)

	def _calculate_optimal_text_width(self, text: str) -> tuple[int, int]:
		fm = self.text_wid.fontMetrics()
		# Измеряем ширину текста, если бы он поместился в одну строку
		single_line_width = fm.horizontalAdvance(text)
		# Стартовая минимальная ширина окна для расчетов
		test_width = 220
		max_width = 800  # Ограничитель, чтобы окно не растянулось на весь экран
		# Если текст короткий, сразу отдаем его ширину
		if single_line_width <= test_width:
			return single_line_width + 2, fm.height()
		# Алгоритм подгонки: прибавляем по 10 пикселей, пока коэффициент > 1.15
		while test_width < max_width:
			rect = fm.boundingRect(
				0, 0, test_width, 10000, 
				Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft, 
				text
			)
			real_text_width = rect.width()
			if real_text_width == 0:
				break
			# Проверяем вашу пропорцию
			ratio = test_width / real_text_width
			if ratio <= 1.15:
				return test_width, rect.height()
			# Если пустот справа слишком много, расширяем допустимую ширину еще на 10px
			test_width += 10
		# На случай, если уперлись в max_width
		final_rect = fm.boundingRect(
			0, 0, test_width, 10000, 
			Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft, 
			text
		)
		return test_width, final_rect.height()

	def _adjust_window_size(self, text: str):
		optimal_text_width, text_height = self._calculate_optimal_text_width(text)
		# Применяем рассчитанную ширину к текстовому виджету
		self.text_wid.setFixedWidth(optimal_text_width)
		# Высота контентного блока (максимум между иконкой и высотой текста)
		content_height = max(self.icon_size, text_height)
		self.content_widget.setFixedHeight(content_height)
		# Высота блока кнопок
		btn_height = self.btn_widget.sizeHint().height()
		self.btn_widget.setFixedHeight(btn_height)
		# Ширина окна: ширина контента против минимально необходимой ширины для кнопок
		content_width = 15 + self.icon_size + 15 + optimal_text_width + 10
		min_btns_width = self.btn_widget.sizeHint().width() + 25 
		final_window_width = max(content_width, min_btns_width)
		# Итоговая высота окна
		layout_height = (
			getattr(self, 'bar_height', 0) +  # Подстраховка, если bar_height инициализируется в родительском классе
			10 +
			content_height +
			10 +
			btn_height +
			10
		)

		central_widget = self.centralWidget()
		if central_widget:
			central_widget.setFixedHeight(layout_height)

		# Полностью блокируем ресайз с вычисленными значениями
		self.setFixedWidth(final_window_width)
		self.setFixedHeight(layout_height)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key.Key_Escape:
			self.cancel_clicked.emit()
			self.deleteLater()
		else:
			super().keyPressEvent(event)

    
class WarningWindow(ConfirmWindow):
    def __init__(self, text: str):
        super().__init__(text)
        self.cancel_btn.setVisible(False)
        self.ok_btn.setVisible(False)
        self.got_it_btn = UPushButton(Lng.got_it[JsonData.lng_index])
        self.got_it_btn.clicked.connect(self.deleteLater)
        self.got_it_btn.setFixedWidth(150)
        self.btn_layout.addWidget(self.got_it_btn)
        self.btn_layout.addStretch(1)


class SuperConfirmWindow(ConfirmWindow):
    icon_path = Static.COMMON_ICONS / "red_warning.svg"

    def __init__(self, text: str):
        super().__init__(text)
        self.svg_widget.load(str(self.icon_path))


class InputTextWin(UMainWidget):
    ok_clicked = pyqtSignal(str)
    cancel_clicked = pyqtSignal()

    def __init__(self, description: str, svg_path: str = None):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.text_input[JsonData.lng_index])
        self.insert_sep()
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


class MfPathWidget(UGroupBox):
    changed = pyqtSignal()
    magnifier = Static.COMMON_ICONS / "magnifier.svg"
    green_checkmark = Static.COMMON_ICONS / "green_checkmark.svg"
    hh = 70
    icon_size = 35

    def __init__(self, lng_index: int, mf_path: str = None):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFixedHeight(self.hh)

        self.mf_path = mf_path
        self.lng_index = lng_index
        
        # Таймер инициализируем один раз как атрибут класса
        self.watch_timer = QTimer(self)
        self.watch_timer.timeout.connect(self.check_path_by_timer)
    
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(10, 2, 2, 2)
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

    def init_no_path_ui(self):
        """Создание панели 'Путь не выбран' (индекс 0 в стеке)"""
        widget = QWidget()
        h_lay = QHBoxLayout(widget)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(str(self.magnifier))
        right_btn.setFixedSize(self.icon_size, self.icon_size)
        h_lay.addWidget(right_btn)
        
        lines = (
            f"{Lng.folder_path[self.lng_index]}:",
            Lng.path_hint_texts[self.lng_index].lower()
        )
        self.no_path_label = QLabel("\n".join(lines))
        self.no_path_label.setWordWrap(True)
        h_lay.addWidget(self.no_path_label)
        h_lay.addStretch()
        
        self.stack.addWidget(widget)

    def init_ok_path_ui(self):
        """Создание панели 'Путь корректен' (индекс 1 в стеке)"""
        widget = QWidget()
        h_lay = QHBoxLayout(widget)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)

        right_btn = QSvgWidget()
        right_btn.load(str(self.green_checkmark))
        right_btn.setFixedSize(35, 35)
        h_lay.addWidget(right_btn)

        self.ok_path_label = SelectableLabel("")
        h_lay.addWidget(self.ok_path_label)
        h_lay.addStretch()

        self.stack.addWidget(widget)

    def show_no_path(self):
        """Включение режима ожидания пути"""
        self.stack.setCurrentIndex(0)
        if not self.watch_timer.isActive():
            self.watch_timer.start(1000)  # Проверка каждую секунду

    def show_ok_path(self):
        """Включение режима успешного пути"""
        self.watch_timer.stop()  # Важно: останавливаем таймер сразу
        lines = (f"{Lng.folder_path[self.lng_index]}:", self.mf_path)
        self.ok_path_label.setText('\n'.join(lines))
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

    def mouseReleaseEvent(self, a0: QMouseEvent):
        if a0.button() != Qt.MouseButton.LeftButton:  # Исправлена проверка кнопки мыши
            return super().mouseReleaseEvent(a0)
        
        dialog = QFileDialog()
        url = dialog.getExistingDirectory()
        if url and os.path.isdir(url):
            self.update_path(url)
        return super().mouseReleaseEvent(a0)
        
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