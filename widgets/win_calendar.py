from pathlib import Path

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout

from cfg import JsonData, Static
from system.items import ReadableDateItem
from system.lang import Lng

from ._base_widgets import (ActiveButton, SvgBg, TitleWidget, TransparentLabel, TransparentWidget, UGroupBox,
                            UMainWindow, UMenu, UPushButton, USep, BaseGroupBox)


class CalendarSvgNavi(TransparentWidget):
	clicked = pyqtSignal()

	def __init__(self, svg: Path, alignment):
		super().__init__()

		self.setSizePolicy(
					QSizePolicy.Policy.Expanding,
					QSizePolicy.Policy.Expanding
				)

		h_lay = QHBoxLayout(self)
		h_lay.setContentsMargins(0, 0, 0, 0)
		h_lay.setAlignment(alignment)

		svg_btn = SvgBg(svg, 25, 15)
		svg_btn.clicked_.connect(self.svg_clicked)
		h_lay.addWidget(svg_btn)

		self._is_active = True
		self.set_enabled()

	def set_enabled(self):
		self._is_active = True
		self.setCursor(Qt.CursorShape.PointingHandCursor)

	def set_disabled(self):
		self._is_active = False
		self.setCursor(Qt.CursorShape.ForbiddenCursor)

	def svg_clicked(self):
		if self._is_active:
			self.clicked.emit()

	def mouseReleaseEvent(self, a0):
		if self._is_active and a0.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit()
		return super().mouseReleaseEvent(a0)


class _CalendarDayBase(TransparentLabel):
	clicked = pyqtSignal()

	def __init__(self, text: str, date: QDate):
		super().__init__(text)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.date = date

	def mouseReleaseEvent(self, ev: QMouseEvent):
		if ev.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit()
		super().mouseReleaseEvent(ev)

	def enterEvent(self, event):
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		return super().enterEvent(event)


class CalendarDay(_CalendarDayBase):
	pass


class CalendarDayInactive(TransparentLabel):
	clicked = pyqtSignal(QDate)

	def __init__(self, text: str, date: QDate):
		super().__init__(text)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.set_style("gray", "regular", "regular")
		self.date = date

	def mouseReleaseEvent(self, ev: QMouseEvent):
		if ev.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit(self.date)
		super().mouseReleaseEvent(ev)

	def enterEvent(self, event):
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		return super().enterEvent(event)


class CalendarCircle(TransparentLabel):
	pass




class WinCalendar(UMainWindow):
	date_selected = pyqtSignal(QDate)
	min_year = 2015
	cell_size = (45, 35)
	svg_nav_size = (15, 15)
	svg_circle_size = (27, 27)

	# Теперь принимаем date, который может быть невалидным или None
	def __init__(self, date=None):
		super().__init__()
		self.readable_date = ReadableDateItem(JsonData.lng_index)
		self.date_now = QDate.currentDate()

		# --- РАЗДЕЛЕНИЕ ЛОГИКИ ---
		if date is None or not date.isValid():
			self.selected_date: QDate = self.date_now
			self.view_date = self.date_now
			self.date_on_load = self.date_now
		else:
			self.selected_date: QDate = date
			self.view_date = date
			self.date_on_load = date

		self.setWindowTitle(Lng.calendar)
		self.set_close_only()
		self.set_always_on_top()

		calendar_wrapper = BaseGroupBox()
		self.central_layout.addWidget(calendar_wrapper)
		self.wrapper_layout = QVBoxLayout(calendar_wrapper)
		self.wrapper_layout.setContentsMargins(5, 10, 5, 0)
		self.wrapper_layout.setSpacing(self.central_layout.spacing())
		self.wrapper_layout.setSpacing(0)

		self.init_ui()
		self.adjustSize()
		self.setFixedSize(self.width() + 15, self.height())

	def init_ui(self):
		_title_widget = TitleWidget("", title_svg=Static.COLOR_ICONS / "calendar.svg")
		_title_widget.v_lay.setSpacing(10)
		self.wrapper_layout.addWidget(_title_widget)
		self.dynamic_label = _title_widget.title_widget.text_widget

		self.nav_widget = TransparentWidget()
		self.wrapper_layout.addWidget(self.nav_widget)

		self.nav_layout = QHBoxLayout(self.nav_widget)
		self.nav_layout.setContentsMargins(0, 7, 0, 7)
		self.nav_layout.setSpacing(5)
		self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.btn_prev = CalendarSvgNavi(
			Static.GRAY_ICONS / "arrow_left.svg",
			Qt.AlignmentFlag.AlignLeft
		)
		self.btn_prev.clicked.connect(self.prev_month)
		self.nav_layout.addWidget(self.btn_prev)
		# self.nav_layout.addStretch()

		self.btn_month = UPushButton("")
		self.menu_month = UMenu(parent=self)
		self.btn_month.setMenu(self.menu_month)
		self.populate_months()
		self.nav_layout.addWidget(self.btn_month)

		self.btn_year = UPushButton("")
		self.menu_year = UMenu(parent=self)
		self.btn_year.setMenu(self.menu_year)
		self.populate_years()
		self.nav_layout.addWidget(self.btn_year)
		# self.nav_layout.addStretch()

		self.btn_next = CalendarSvgNavi(
			Static.GRAY_ICONS / "arrow_right.svg",
			Qt.AlignmentFlag.AlignRight
		)
		self.btn_next.clicked.connect(self.next_month)
		self.nav_layout.addWidget(self.btn_next)

		self.wrapper_layout.addWidget(USep())

		header_widget = TransparentWidget()
		header_layout = QHBoxLayout(header_widget)
		header_layout.setContentsMargins(0, 0, 0, 0)
		header_layout.setSpacing(0)

		for col in range(7):
			week_name = self.readable_date.q_locale.dayName(col + 1, self.readable_date.q_locale.FormatType.ShortFormat)
			lbl_day = TransparentLabel(week_name.capitalize())
			lbl_day.set_style("gray", "regular", "regular")
			lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
			lbl_day.setFixedSize(*self.cell_size)
			header_layout.addWidget(lbl_day)

		self.wrapper_layout.addWidget(header_widget)

		self.wrapper_layout.addWidget(USep())

		self.calendar_container = TransparentWidget()
		self.calendar_container_layout = QVBoxLayout(self.calendar_container)
		self.calendar_container_layout.setContentsMargins(0, 0, 0, 0)
		self.calendar_container_layout.setSpacing(0)
		self.wrapper_layout.addWidget(self.calendar_container)

		self.btn_container = TransparentWidget()
		self.central_layout.addWidget(self.btn_container)
		self.btn_container_layout = QHBoxLayout(self.btn_container)
		self.btn_container_layout.setContentsMargins(0, 0, 0, 0)
		self.btn_container_layout.setSpacing(5)

		self.reset_button = UPushButton(Lng.reset)
		self.reset_button.clicked.connect(self.reset_button_cmd)
		self.btn_container_layout.addWidget(self.reset_button)

		self.btn_container_layout.addStretch(1)

		cancel_btn = UPushButton(Lng.close)
		cancel_btn.clicked.connect(self.deleteLater)
		self.btn_container_layout.addWidget(cancel_btn)

		self.done_btn = ActiveButton(Lng.apply)
		self.done_btn.clicked.connect(self.ok_btn_cmd)
		self.btn_container_layout.addWidget(self.done_btn)

		self.create_calendar_widget()
		self.update_calendar()

		self.wrapper_layout.addStretch()

	def _add_circle(self, cell, day_num: int, kind: str):
		size = self.svg_circle_size[0]
		circle = CalendarCircle(str(day_num), cell)
		circle.setProperty("circle", kind)  # "selected" или "today"
		circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
		circle.setFixedSize(size, size)
		circle.move((self.cell_size[0] - size) // 2, (self.cell_size[1] - size) // 2)
		circle.show()

	def ok_btn_cmd(self):
		# Отправляем выбранную дату, либо пустой (невалидный) QDate, если None
		emit_date = self.selected_date if self.selected_date else QDate()
		self.date_selected.emit(emit_date)
		self.deleteLater()

	def reset_button_cmd(self):
		# Сбрасываем выделение и возвращаем сетку на текущий месяц
		self.selected_date = self.date_on_load
		self.view_date = self.date_on_load
		self.update_calendar()

	def create_calendar_widget(self):
		self.calendar_widget = TransparentWidget()
		self.calendar_layout = QVBoxLayout(self.calendar_widget)
		self.calendar_layout.setContentsMargins(0, 0, 0, 0)
		self.calendar_layout.setSpacing(0)
		self.calendar_container_layout.addWidget(self.calendar_widget)

	def recreate_calendar_widget(self):
		old_widget = self.calendar_widget
		self.calendar_container_layout.removeWidget(old_widget)
		old_widget.setParent(None)
		old_widget.deleteLater()
		self.create_calendar_widget()

	def update_dynamic_label(self):
		# Если дата выбрана — показываем ее, иначе пишем "Не выбрано"
		if self.selected_date:
			readable_date = self.readable_date.get_readable_date(self.selected_date)
			self.dynamic_label.setText(readable_date)
		else:
			self.dynamic_label.setText(Lng.not_selected)

	def populate_months(self):
		self.menu_month.clear()
		max_width = 0
		font_metrics = self.btn_month.fontMetrics()
		for month in range(1, 13):
			month_name = self.readable_date.q_locale.standaloneMonthName(
				month, self.readable_date.q_locale.FormatType.LongFormat
			).capitalize()
			action = QAction(month_name, self)
			action.setData(month)
			action.triggered.connect(self.month_menu_selected)
			self.menu_month.addAction(action)
			max_width = max(max_width, font_metrics.horizontalAdvance(month_name))
		offset = 30
		self.btn_month.setFixedWidth(max_width + offset)

	def populate_years(self):
		self.menu_year.clear()
		max_year = self.date_now.year()
		max_width = self.btn_year.fontMetrics().horizontalAdvance(str(max_year))
		for year in range(self.min_year, max_year + 1):
			action = QAction(str(year), self)
			action.setData(year)
			action.triggered.connect(self.year_menu_selected)
			self.menu_year.addAction(action)
		self.btn_year.setFixedWidth(max_width + 35)

	def month_menu_selected(self):
		action: QAction = self.sender()
		selected_month = action.data()
		year = self.view_date.year()
		current_day = self.view_date.day()
		days_in_new_month = QDate(year, selected_month, 1).daysInMonth()
		target_day = min(current_day, days_in_new_month)
		self.view_date = QDate(year, selected_month, target_day)
		self.update_calendar()

	def year_menu_selected(self):
		action: QAction = self.sender()
		selected_year = action.data()
		current_month = self.view_date.month()
		current_day = self.view_date.day()
		days_in_new_month = QDate(selected_year, current_month, 1).daysInMonth()
		target_day = min(current_day, days_in_new_month)
		self.view_date = QDate(selected_year, current_month, target_day)
		self.update_calendar()

	def day_selected(self):
		sender_button = self.sender()
		self.selected_date = sender_button.date
		self.view_date = sender_button.date
		self.update_calendar()

	def inactive_day_clicked(self, clicked_date: QDate):
		self.selected_date = clicked_date
		self.view_date = clicked_date
		self.update_calendar()

	def prev_month(self):
		min_date = QDate(self.min_year, 1, 1)
		new_date = self.view_date.addMonths(-1)
		if new_date >= min_date:
			self.view_date = new_date
			self.selected_date = new_date
			self.update_calendar()

	def next_month(self):
		max_date = QDate(self.date_now.year(), 12, 31)
		new_date = self.view_date.addMonths(1)
		if new_date <= max_date:
			self.view_date = new_date
			self.update_calendar()

	def update_calendar(self):
		self.update_dynamic_label()

		# Отрисовываем сетку на основе view_date
		current_year = self.view_date.year()
		current_month = self.view_date.month()

		month = self.readable_date.q_locale.standaloneMonthName(
			current_month,
			self.readable_date.q_locale.FormatType.LongFormat
		)
		self.btn_month.setText(month.capitalize())
		self.btn_year.setText(str(current_year))

		if current_year == self.min_year and current_month == 1:
			self.btn_prev.set_disabled()
		else:
			self.btn_prev.set_enabled()

		if current_year == self.date_now.year() and current_month == 12:
			self.btn_next.set_disabled()
		else:
			self.btn_next.set_enabled()

		self.recreate_calendar_widget()

		first_day = QDate(current_year, current_month, 1)
		start_col = first_day.dayOfWeek() - 1
		days_in_month = first_day.daysInMonth()

		all_days = []

		prev_month_date = first_day.addMonths(-1)
		days_in_prev_month = prev_month_date.daysInMonth()
		for i in range(start_col):
			day_num = days_in_prev_month - start_col + i + 1
			d_date = QDate(prev_month_date.year(), prev_month_date.month(), day_num)
			all_days.append((day_num, d_date, "inactive"))

		for day in range(1, days_in_month + 1):
			d_date = QDate(current_year, current_month, day)
			all_days.append((day, d_date, "active"))

		next_month_date = first_day.addMonths(1)
		total_cells = 42
		extra_days = total_cells - len(all_days)

		for day in range(1, extra_days + 1):
			d_date = QDate(next_month_date.year(), next_month_date.month(), day)
			all_days.append((day, d_date, "inactive"))

		weeks = [all_days[i:i + 7] for i in range(0, len(all_days), 7)]

		for week_index, week in enumerate(weeks):
			week_widget = TransparentWidget()
			week_layout = QHBoxLayout(week_widget)
			week_layout.setContentsMargins(0, 0, 0, 0)
			week_layout.setSpacing(0)

			for day_num, d_date, status in week:
				if status == "inactive":
					btn_day = CalendarDayInactive(str(day_num), d_date)
					btn_day.setFixedSize(*self.cell_size)
					btn_day.clicked.connect(self.inactive_day_clicked)
				else:
					btn_day = CalendarDay("", d_date)
					btn_day.setFixedSize(*self.cell_size)
					if self.selected_date is not None and d_date == self.selected_date:
						self._add_circle(btn_day, day_num, "selected")
					elif d_date == self.date_now:
						self._add_circle(btn_day, day_num, "today")
					else:
						btn_day.setText(str(day_num))
					btn_day.clicked.connect(self.day_selected)

					btn_day.clicked.connect(self.day_selected)

				week_layout.addWidget(btn_day)

			self.calendar_layout.addWidget(week_widget)

			if week_index < len(weeks) - 1:
				self.calendar_layout.addWidget(USep())

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)