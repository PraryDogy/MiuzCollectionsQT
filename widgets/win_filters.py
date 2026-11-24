
from PyQt6.QtCore import QDate, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.items import Filters, ReadableDateItem
from system.lang import Lng

from ._base_widgets import (ActiveButton, ConfirmWin, FlowLayout,
                            InputTextWin, TitleWidget, TransparentLabel,
                            TransparentWidget, UGroupBox, UMainWindow, UMenu,
                            UPushButton, TagWidget)
from .win_calendar import WinCalendar


class PendingDatesState:
	"""Выбор дат до нажатия «Применить». Dynamic не меняется, пока не нажата кнопка."""

	def __init__(self):
		self.start: QDate | None = self._to_qdate(Dynamic.py_date_start)
		self.end: QDate | None = self._to_qdate(Dynamic.py_date_end)

	@staticmethod
	def _to_qdate(py_date):
		return QDate(py_date.year, py_date.month, py_date.day) if py_date else None

	@staticmethod
	def _to_py(q_date: QDate | None):
		return q_date.toPyDate() if q_date else None

	def differs_from_dynamic(self) -> bool:
		return (
			self._to_py(self.start) != Dynamic.py_date_start
			or self._to_py(self.end) != Dynamic.py_date_end
		)

	def commit(self):
		Dynamic.py_date_start = self._to_py(self.start)
		Dynamic.py_date_end = self._to_py(self.end)

	def reset(self):
		self.start = None
		self.end = None


class WinFiltersTitleWidget(TitleWidget):
	reset_clicked = pyqtSignal()

	def __init__(self, title, title_svg):
		super().__init__(title=title, title_svg=title_svg)

		self.reset_button = UPushButton(Lng.reset)
		self.reset_button.clicked.connect(self.reset_clicked.emit)
		self.add_title_button(self.reset_button)
		self.set_margins(5, 0, 5, 0)


class CalendarTag(TagWidget):
	def __init__(self):
		super().__init__(Lng.not_selected)
		self.adjustSize()
		self.setFixedWidth(self.width())


class DatesWidget(UGroupBox):
	load_st_grid = pyqtSignal()
	readable_date = None

	def __init__(self, pending: PendingDatesState, parent=None):
		super().__init__(parent)
		self.pending = pending

		_today = QDate.currentDate()
		self.readable_date_wid = ReadableDateItem(JsonData.lng_index)

		self.dates_dict = {
			(_today, _today): Lng.preset_today,
			(_today.addDays(-1), _today.addDays(-1)): Lng.preset_yesterday,
			(_today.addDays(-7), _today): Lng.preset_week,
			(_today.addDays(-14), _today): Lng.preset_two_weeks,
			(_today.addMonths(-1), _today): Lng.preset_month,
			(_today.addYears(-1), _today): Lng.preset_year,
		}

		self.main_layout = QVBoxLayout(self)
		self.main_layout.setContentsMargins(5, 5, 5, 5)
		self.main_layout.setSpacing(7)

		self.title_widget = WinFiltersTitleWidget(Lng.dates_management, Static.COLOR_ICONS / "calendar.svg")
		self.title_widget.reset_clicked.connect(lambda: self.reset_dates(True))
		self.main_layout.addWidget(self.title_widget)

		dynamic_container = TransparentWidget()
		dynamic_container_lay = QHBoxLayout(dynamic_container)
		dynamic_container_lay.setContentsMargins(0, 0, 0, 0)
		dynamic_container_lay.setSpacing(5)

		self.dynamic_label = TransparentLabel(Lng.selected_dates)
		dynamic_container_lay.addWidget(self.dynamic_label)

		self.main_layout.addWidget(dynamic_container)
		self.main_layout.addSpacing(5)

		self.preset_menu = UMenu(parent=self)

		for qdates, text in self.dates_dict.items():
			action = QAction(text, self.preset_menu)
			action.triggered.connect(
				lambda _, d=qdates: self.action_cmd(d[0], d[1])
			)
			self.preset_menu.addAction(action)

		self.date_btns_widget = TransparentWidget()
		self.date_btns_layout = QHBoxLayout(self.date_btns_widget)
		self.date_btns_layout.setContentsMargins(0, 0, 0, 0)
		self.date_btns_layout.setSpacing(5)

		dates_btn = UPushButton(Lng.period)
		dates_btn.setMenu(self.preset_menu)
		self.date_btns_layout.addWidget(dates_btn)

		self.date_btns_layout.addSpacing(10)

		from_label = TransparentLabel(Lng.start_date)
		from_label.set_style("gray", "regular", "regular")
		self.date_btns_layout.addWidget(from_label)

		self.left_calendar_tag = CalendarTag()
		self.left_calendar_tag.clicked.connect(lambda: self.show_calendar_win("start"))
		self.date_btns_layout.addWidget(self.left_calendar_tag)

		self.date_btns_layout.addSpacing(10)

		to_label = TransparentLabel(Lng.end_date)
		to_label.set_style("gray", "regular", "regular")
		self.date_btns_layout.addWidget(to_label)

		self.right_calendar_tag = CalendarTag()
		self.right_calendar_tag.clicked.connect(lambda: self.show_calendar_win("end"))
		self.date_btns_layout.addWidget(self.right_calendar_tag)

		self.date_btns_layout.addStretch(1)
		self.main_layout.addWidget(self.date_btns_widget)

		self.update_readable_date_label()
		self.set_date_buttons_text()

	def is_all_time(self) -> bool:
		return self.pending.start is None and self.pending.end is None

	def date_digits(self, q_date: QDate) -> str:
		return q_date.toString("dd.MM.yyyy")

	def show_calendar_win(self, flag: str):
		qdate = self.pending.start if flag == "start" else self.pending.end

		self.calendar_win = WinCalendar(qdate)
		self.calendar_win.center_to_parent(self.window())

		def on_date_selected(date: QDate):
			# только черновик: в Dynamic попадёт после «Применить»
			if not date.isValid():
				if flag == "start":
					self.pending.start = None
				else:
					self.pending.end = None
			else:
				if flag == "start":
					self.pending.start = date
					if self.pending.end is not None and self.pending.start > self.pending.end:
						self.pending.end = self.pending.start
				else:
					self.pending.end = date
					if self.pending.start is not None and self.pending.start > self.pending.end:
						self.pending.start = self.pending.end

			self.handle_preset_change()

		self.calendar_win.date_selected.connect(on_date_selected)
		self.calendar_win.show()

	def action_cmd(self, q_date_start: QDate, q_date_end: QDate):
		self.pending.start = q_date_start
		self.pending.end = q_date_end
		self.handle_preset_change()

	def handle_preset_change(self):
		self.set_date_buttons_text()
		self.update_readable_date_label()

	def set_date_buttons_text(self):
		empty_text = Lng.not_selected

		if self.pending.start is None:
			self.left_calendar_tag.text_widget.setText(empty_text)
			self.left_calendar_tag.set_qss_style(self.left_calendar_tag.qss_gray)
		else:
			self.left_calendar_tag.text_widget.setText(self.date_digits(self.pending.start))
			self.left_calendar_tag.set_qss_style(self.left_calendar_tag.qss_green)

		if self.pending.end is None:
			self.right_calendar_tag.text_widget.setText(empty_text)
			self.right_calendar_tag.set_qss_style(self.right_calendar_tag.qss_gray)
		else:
			self.right_calendar_tag.text_widget.setText(self.date_digits(self.pending.end))
			self.right_calendar_tag.set_qss_style(self.right_calendar_tag.qss_green)

	def update_readable_date_label(self):
		start, end = self.pending.start, self.pending.end

		if self.is_all_time():
			text = Lng.all_time
		elif start is not None and end is not None and (start, end) in self.dates_dict:
			text = self.dates_dict[start, end]
		elif start is not None and end is None:
			text = f"{Lng.from_text} {self.readable_date_wid.get_readable_date(start)}"
		elif start is None and end is not None:
			text = f"{Lng.to_text} {self.readable_date_wid.get_readable_date(end)}"
		else:
			str_from = self.readable_date_wid.get_readable_date(start)
			str_to = self.readable_date_wid.get_readable_date(end)
			text = f"{Lng.from_text} {str_from} {Lng.to_text.lower()} {str_to}"

		DatesWidget.readable_date = text.lower()
		text = f"{Lng.selected_dates}: {text.lower()}"
		self.dynamic_label.setText(text)

	def reset_dates(self, with_sig: bool) -> bool:
		"""Сбрасывает даты сразу. Возвращает True, если даты были применены в Dynamic."""
		applied = bool(Dynamic.py_date_start or Dynamic.py_date_end)

		self.pending.reset()
		self.pending.commit()
		self.handle_preset_change()

		if with_sig and applied:
			self.load_st_grid.emit()
		return applied


class PendingTagsState:
	"""Выбор тегов до нажатия «Применить». Dynamic не меняется, пока не нажата кнопка."""

	def __init__(self):
		self.favs_tag_enabled: bool = Dynamic.favs_tag_enabled
		self.no_subfolders_tag_enabled: bool = Dynamic.no_subfolders_tag_enabled
		self.word_tags_list: list[str] = list(Dynamic.word_tags_list)

	def differs_from_dynamic(self) -> bool:
		return (
			self.favs_tag_enabled != Dynamic.favs_tag_enabled
			or self.no_subfolders_tag_enabled != Dynamic.no_subfolders_tag_enabled
			or self.word_tags_list != Dynamic.word_tags_list
		)

	def commit(self):
		Dynamic.favs_tag_enabled = self.favs_tag_enabled
		Dynamic.no_subfolders_tag_enabled = self.no_subfolders_tag_enabled
		Dynamic.word_tags_list[:] = self.word_tags_list

	def reset(self):
		self.favs_tag_enabled = False
		self.no_subfolders_tag_enabled = False
		self.word_tags_list.clear()


class FavTag(TagWidget):
	def __init__(self, pending: PendingTagsState):
		super().__init__(Lng.favorites, Static.GRAY_ICONS / "star.svg")
		self.pending = pending
		self.clicked.connect(self.toggle_fav)
		if pending.favs_tag_enabled:
			self.set_qss_style(self.qss_green)

	def toggle_fav(self, *args):
		self.pending.favs_tag_enabled = not self.pending.favs_tag_enabled
		self.set_qss_style(self.qss_green if self.pending.favs_tag_enabled else self.qss_gray)


class SubfoldersTag(TagWidget):
	def __init__(self, pending: PendingTagsState):
		super().__init__(Lng.without_subfolders, Static.GRAY_ICONS / "folder.svg")
		self.pending = pending
		self.clicked.connect(self.toggle_subfolders)
		if pending.no_subfolders_tag_enabled:
			self.set_qss_style(self.qss_green)

	def toggle_subfolders(self, *args):
		self.pending.no_subfolders_tag_enabled = not self.pending.no_subfolders_tag_enabled
		self.set_qss_style(
			self.qss_green if self.pending.no_subfolders_tag_enabled else self.qss_gray
		)


class WordTag(TagWidget):
	def __init__(self, text: str, pending: PendingTagsState):
		super().__init__(text, Static.GRAY_ICONS / "tags.svg", Static.GRAY_ICONS / "trash.svg")
		self.pending = pending
		self.word = text
		self.clicked.connect(self.toggle_word_tag)
		if text in pending.word_tags_list:
			self.set_qss_style(self.qss_green)

	def toggle_word_tag(self, *args):
		if self.word in self.pending.word_tags_list:
			self.pending.word_tags_list.remove(self.word)
			self.set_qss_style(self.qss_gray)
		else:
			self.pending.word_tags_list.append(self.word)
			self.set_qss_style(self.qss_green)


class AddTag(TagWidget):
	def __init__(self):
		super().__init__(Lng.new_tag, Static.GRAY_ICONS / "crest.svg")
		self.set_qss_style(self.qss_transparent)
		self.left_svg_widget.setFixedSize(10, 10)


class StandartTags(TransparentWidget):
	load_st_grid = pyqtSignal()

	def __init__(self, pending: PendingTagsState, parent=None):
		super().__init__(parent)
		self.pending = pending

		self.flow_layout = FlowLayout(self, spacing=7)
		self.flow_layout.setContentsMargins(0, 0, 0, 0)
		self._create_tags()

	def _create_tags(self):
		self.fav_tag = FavTag(self.pending)
		self.flow_layout.addWidget(self.fav_tag)

		self.subfolders_tag = SubfoldersTag(self.pending)
		self.flow_layout.addWidget(self.subfolders_tag)


class UserTags(TransparentWidget):
	load_st_grid = pyqtSignal()

	def __init__(self, pending: PendingTagsState, parent=None):
		super().__init__(parent)
		self.pending = pending

		policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
		policy.setHeightForWidth(True)
		self.setSizePolicy(policy)

		self.flow_layout = FlowLayout(self, spacing=7)
		self.flow_layout.setContentsMargins(0, 0, 0, 0)
		self._create_tags()

	def _create_tags(self):
		for word in Filters.items:
			tag = WordTag(word, self.pending)
			tag.right_svg_clicked.connect(lambda w=tag: self.show_remove_tag_win(w))
			self.flow_layout.addWidget(tag)

		self.add_tag = AddTag()
		self.add_tag.clicked.connect(self.show_text_win)
		self.flow_layout.addWidget(self.add_tag)

	def show_text_win(self):

		def ok_clicked(text: str):
			if text:
				Filters.items.append(text)
				Filters.write_json_data()
				self.flow_layout.clear()
				self._create_tags()

		self.text_win = InputTextWin(
			title=Lng.new_tag,
			description=Lng.new_tag_desc
		)
		self.text_win.setWindowTitle(Lng.new_tag)
		self.text_win.center_to_parent(self.window())
		self.text_win.ok_clicked.connect(ok_clicked)
		self.text_win.show()

	def show_remove_tag_win(self, widget: WordTag):

		def ok_clicked():
			text = widget.word
			Filters.items.remove(text)
			Filters.write_json_data()

			# удаление тега — необратимое действие, поэтому убираем его и из выбора, и из применённых
			if text in self.pending.word_tags_list:
				self.pending.word_tags_list.remove(text)
			if text in Dynamic.word_tags_list:
				Dynamic.word_tags_list.remove(text)
				self.load_st_grid.emit()
			widget.deleteLater()

		self.remove_tag_win = ConfirmWin(Lng.remove_tag_question, "red", "yellow")
		self.remove_tag_win.confirm_btn.setText(Lng.remove_tag_confirm)
		self.remove_tag_win.ok_clicked.connect(ok_clicked)
		self.remove_tag_win.center_to_parent(self.window())
		self.remove_tag_win.show()

	def hasHeightForWidth(self):
		return True

	def heightForWidth(self, width):
		return self.flow_layout.heightForWidth(width)

	def sizeHint(self):
		width = self.parentWidget().width() if self.parentWidget() else 500
		return QSize(width, self.heightForWidth(width))


class TagsWidget(UGroupBox):
	load_st_grid = pyqtSignal()

	def __init__(self, pending: PendingTagsState):
		super().__init__()
		self.pending = pending

		self.v_lay = QVBoxLayout(self)
		self.v_lay.setContentsMargins(5, 5, 5, 5)
		self.v_lay.setSpacing(7)

		self.title_widget = WinFiltersTitleWidget(Lng.tag_management, Static.COLOR_ICONS / "tags.svg")
		self.title_widget.reset_clicked.connect(lambda: self.reset_tags(True))
		self.v_lay.addWidget(self.title_widget)

		st_tags_title = TransparentLabel(Lng.standart_tags)
		st_tags_title.set_style("gray", "regular", "regular")
		self.v_lay.addWidget(st_tags_title)

		self.standart_tags = StandartTags(self.pending)
		self.v_lay.addWidget(self.standart_tags)

		user_tags_title = TransparentLabel(Lng.user_tags)
		user_tags_title.set_style("gray", "regular", "regular")
		self.v_lay.addWidget(user_tags_title)

		self.user_tags = UserTags(self.pending)
		self.user_tags.load_st_grid.connect(self.load_st_grid.emit)
		self.v_lay.addWidget(self.user_tags)

	@staticmethod
	def tags_applied_in_dynamic() -> bool:
		# сигнал нужен только если теги реально применены, а не просто отмечены в черновике
		return bool(
			Dynamic.favs_tag_enabled
			or Dynamic.no_subfolders_tag_enabled
			or Dynamic.word_tags_list
		)

	def reset_tags(self, with_sig: bool) -> bool:
		# возвращает, были ли теги применены до сброса
		applied = self.tags_applied_in_dynamic()

		self.pending.reset()
		self.pending.commit()

		for tag in self.findChildren(TagWidget):
			if not isinstance(tag, AddTag):
				tag.set_qss_style(tag.qss_gray)

		if with_sig and applied:
			self.load_st_grid.emit()
		return applied


class WinFilters(UMainWindow):
	load_st_grid = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.filters)
		self.setFixedWidth(590)

		# черновики: попадают в Dynamic только по «Применить» или при сбросе
		self.pending_dates = PendingDatesState()
		self.pending_tags = PendingTagsState()

		self.dates_widget = DatesWidget(self.pending_dates)
		self.dates_widget.load_st_grid.connect(self.load_st_grid.emit)
		self.central_layout.addWidget(self.dates_widget)

		self.tags_widget = TagsWidget(self.pending_tags)
		self.tags_widget.load_st_grid.connect(self.load_st_grid.emit)
		self.central_layout.addWidget(self.tags_widget)

		buttons_widget = TransparentWidget()
		self.central_layout.addWidget(buttons_widget)
		self.buttons_layout = QHBoxLayout(buttons_widget)
		self.buttons_layout.setContentsMargins(0, 0, 0, 0)
		self.buttons_layout.setSpacing(5)

		self.reset_all_button = UPushButton(Lng.reset_all)
		self.reset_all_button.clicked.connect(self.reset_all_cmd)
		self.buttons_layout.addWidget(self.reset_all_button)

		self.buttons_layout.addStretch(1)

		close_button = UPushButton(Lng.close)
		close_button.clicked.connect(self.deleteLater)
		self.buttons_layout.addWidget(close_button)

		self.apply_button = ActiveButton(Lng.apply)
		self.apply_button.clicked.connect(self.apply_cmd)
		self.buttons_layout.addWidget(self.apply_button)

		self.tags_widget.user_tags.adjustSize()
		self.tags_widget.adjustSize()
		self.adjustSize()

	def apply_cmd(self):
		# применяем только то, что изменилось относительно Dynamic; грид перезагружаем один раз
		dates_changed = self.pending_dates.differs_from_dynamic()
		tags_changed = self.pending_tags.differs_from_dynamic()

		if dates_changed or tags_changed:
			self.pending_dates.commit()
			self.pending_tags.commit()
			self.load_st_grid.emit()
		self.deleteLater()

	def reset_all_cmd(self):
		# сбрасываем даты и теги сразу; сигнал один, и только если было что-то применено
		dates_applied = self.dates_widget.reset_dates(False)
		tags_applied = self.tags_widget.reset_tags(False)

		if dates_applied or tags_applied:
			self.load_st_grid.emit()

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)