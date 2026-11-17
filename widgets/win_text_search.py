import re

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.lang import Lng

from ._base_widgets import (ActiveButton, TitleTextWidget,
							TransparentLabel, TransparentWidget, UGroupBox,
							UMainWindow, UPushButton, USep, UTextEdit)


class WinTextSearch(UMainWindow):
	ok_clicked = pyqtSignal(str)
	reset_clicked = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setFixedSize(380, 330)
		self.setWindowTitle(Lng.search_window)

		self.magnifier_icon = QIcon(str(Static.GRAY_ICONS / "magnifier.svg"))
		self.wand_icon = QIcon(str(Static.GRAY_ICONS / "wand.svg"))

		self.central_layout.setSpacing(10)
		self.central_layout.setContentsMargins(10, 5, 10, 10)

		group_container = UGroupBox()
		self.central_layout.addWidget(group_container)
		group_layout = QVBoxLayout(group_container)
		group_layout.setContentsMargins(5, 5, 5, 5)
		group_layout.setSpacing(7)

		self.title_row = TitleTextWidget(Lng.search, Static.COLOR_ICONS / "magnifier.svg")
		group_layout.addWidget(self.title_row)

		self.title_row.h_layout.addStretch()

		self.format_button = UPushButton(Lng.enhance_text)
		self.format_button.clicked.connect(self.format_input_text)
		self.format_button.setIconSize(QSize(10, 10))
		self.format_button.setIcon(self.wand_icon)
		self.title_row.h_layout.addWidget(self.format_button)

		group_layout.addWidget(USep())

		# Текст описания форматов (RU / EN)
		self.description_label = TransparentLabel(Lng.text_search_descr)
		self.description_label.set_state("gray")
		self.description_label.setWordWrap(True)
		group_layout.addWidget(self.description_label)

		self.text_edit = UTextEdit()
		self.text_edit.setPlaceholderText(Lng.search_placeholder_texts)
		group_layout.addWidget(self.text_edit)

		# черновик грузим из Dynamic, а не из аргумента
		self.text_edit.setPlainText(", ".join(Dynamic.search_words_list))
		self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

		self.btns_container = TransparentWidget()
		self.central_layout.addWidget(self.btns_container)

		btns_layout = QHBoxLayout(self.btns_container)
		btns_layout.setContentsMargins(0, 0, 0, 0)
		btns_layout.setSpacing(5)

		reset_button = UPushButton(Lng.reset)
		reset_button.clicked.connect(self.reset_cmd)
		btns_layout.addWidget(reset_button)

		btns_layout.addStretch()

		close_btn = UPushButton(Lng.close)
		close_btn.clicked.connect(self.deleteLater)
		btns_layout.addWidget(close_btn)

		self.ok_btn = ActiveButton(Lng.search)
		self.ok_btn.setIcon(self.magnifier_icon)
		self.ok_btn.setIconSize(QSize(10, 10))
		self.ok_btn.clicked.connect(self.search)
		btns_layout.addWidget(self.ok_btn)

		self.setFocus()

	def _draft_words(self) -> list[str]:
		# черновик в том же виде, что и при сохранении в Dynamic
		text = self.text_edit.toPlainText()
		words = re.split(r"[,\n]+", text)
		words = [w.strip() for w in words if w.strip()]
		return list(dict.fromkeys(words))

	def format_input_text(self):
		self.text_edit.setPlainText(", ".join(self._draft_words()))

	def reset_cmd(self):
		# сброс: поле очищается всегда, сигнал только если было что-то применено
		applied = bool(Dynamic.search_words_list)
		self.text_edit.clear()
		if applied:
			Dynamic.search_words_list.clear()
			self.reset_clicked.emit()

	def search(self):
		draft = self._draft_words()
		applied = Dynamic.search_words_list

		# сигнал только если черновик отличается от применённого и есть что применять
		if draft != applied and (draft or applied):
			Dynamic.search_words_list[:] = draft
			self.ok_clicked.emit(", ".join(draft))

		self.deleteLater()

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)