from PyQt6.QtCore import QDate, QLocale, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QImage, QMouseEvent, QPixmap, QPainter
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QStackedLayout,
                             QVBoxLayout)

from cfg import JsonData, Static
from system.lang import Lng
from system.utils import Utils

from ._base_widgets import (GrayTextLabel, TransparentLabel, TransparentWidget,
                            UHorizontalSep, UMainWidget, UMenu, UPushButton)

QSS_ROUND_SVG_SIZE = 30


class CalendarBigDate(GrayTextLabel):
    def __init__(self):
        super().__init__(text="30 сентября 2026")
        self.set_font_size(25)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.adjustSize() 
        self.setFixedWidth(self.width())
        self.clear()


class CalendarSvgNavi(QSvgWidget):
    clicked = pyqtSignal()

    def __init__(self, file_path, parent=None):
        super().__init__(file_path, parent)
        self._is_active = True
        self.set_enabled()

    def set_enabled(self):
        self._is_active = True
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_disabled(self):
        self._is_active = False
        self.setCursor(Qt.CursorShape.ForbiddenCursor)

    def mouseReleaseEvent(self, a0):
        # Если флаг False, клик просто игнорируется
        if self._is_active and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mouseReleaseEvent(a0)


class _CalendarDayBase(TransparentLabel):
    clicked = pyqtSignal()

    def __init__(self, text: str, day: int):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day = day

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(ev)


class CalendarDay(_CalendarDayBase):
    pass


class CalendarDaySelected(TransparentLabel):
    clicked = pyqtSignal()

    def __init__(self, text: str, day: int):
        super().__init__()
        self.day = day
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(ev)


class Calendar(UMainWidget):
    date_selected = pyqtSignal(QDate)

    svg_calendar_path = Static.COMMON_ICONS / "calendar.svg"
    svg_previous_path = Static.COMMON_ICONS / "arrow_left.svg"
    svg_next_path = Static.COMMON_ICONS / "arrow_right.svg"
    svg_blue_circle_path = Static.COMMON_ICONS / "blue_circle.svg"

    min_year = 2015
    day_property = "day_value"

    cell_size = (60, 50)
    svg_nav_size = (30, 30)
    svg_calendar_size = (25, 25)
    svg_blue_circle_size = (40, 40)

    def __init__(self, date: QDate):
        super().__init__()

        if JsonData.lng_index == 0:
            lng = QLocale.Language.Russian
            country = QLocale.Country.Russia
        elif JsonData.lng_index == 1:
            lng = QLocale.Language.English
            country = QLocale.Country.UnitedStates

        qimg = QImage(str(self.svg_blue_circle_path))
        qimg_scaled = Utils.pyqt_scaled_high_dpi(
            qimg,
            self.svg_blue_circle_size[0]
        )
        self.blue_circle_pixmap = QPixmap.fromImage(qimg_scaled)

        self.q_locale = QLocale(lng, country)
        self.current_date = date
        self.date_now = QDate.currentDate()

        self.setWindowTitle(Lng.calendar[JsonData.lng_index])
        self.set_close_only()
        self.set_always_on_top()
        # self.setWindowFlags(Qt.WindowType.Popup)

        self.init_ui()

        hh = 530
        self.adjustSize()
        self.setFixedSize(self.width(), hh)
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def init_ui(self):

        dynamic_container = TransparentWidget()
        self.central_layout.addWidget(dynamic_container)

        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(0, 0, 0, 0)
        dynamic_container_lay.setSpacing(0)

        calendar_icon = QSvgWidget()
        calendar_icon.load(str(self.svg_calendar_path))
        calendar_icon.setFixedSize(*self.svg_calendar_size)
        dynamic_container_lay.addWidget(calendar_icon)

        dynamic_container_lay.addSpacing(10)

        self.dynamic_label = CalendarBigDate()
        dynamic_container_lay.addWidget(self.dynamic_label)
        dynamic_container_lay.addStretch(1)

        self.central_layout.addSpacing(5)

        self.nav_widget = TransparentWidget()
        self.central_layout.addWidget(self.nav_widget)

        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(10, 0, 10, 0)
        self.nav_layout.setSpacing(0)
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_prev = CalendarSvgNavi(str(self.svg_previous_path))
        self.btn_prev.setFixedSize(*self.svg_nav_size)
        self.btn_prev.clicked.connect(self.prev_month)
        self.nav_layout.addWidget(self.btn_prev)

        self.nav_layout.addStretch()

        self.btn_month = UPushButton("")
        self.menu_month = UMenu(parent=self)
        self.btn_month.setMenu(self.menu_month)
        self.populate_months()
        self.nav_layout.addWidget(self.btn_month)

        self.nav_layout.addSpacing(10)

        self.btn_year = UPushButton("")
        self.menu_year = UMenu(parent=self)
        self.btn_year.setMenu(self.menu_year)
        self.populate_years()
        self.nav_layout.addWidget(self.btn_year)

        self.nav_layout.addStretch()

        self.btn_next = CalendarSvgNavi(str(self.svg_next_path))
        self.btn_next.setFixedSize(*self.svg_nav_size)
        self.btn_next.clicked.connect(self.next_month)
        self.nav_layout.addWidget(self.btn_next)

        self.central_layout.addWidget(UHorizontalSep())

        self.btn_container = TransparentWidget()
        self.central_layout.addWidget(self.btn_container)
        self.btn_container_layout = QHBoxLayout(self.btn_container)
        self.btn_container_layout.setContentsMargins(0, 0, 10, 20)
        self.btn_container_layout.setSpacing(15)

        self.btn_container_layout.addStretch(1)

        self.cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
        self.cancel_btn.clicked.connect(self.deleteLater)
        self.btn_container_layout.addWidget(self.cancel_btn)

        self.ok_btn = UPushButton(Lng.apply[JsonData.lng_index])
        self.ok_btn.clicked.connect(self.ok_clicked_cmd)
        self.btn_container_layout.addWidget(self.ok_btn)

        self.create_calendar_widget()
        self.update_calendar()

    def ok_clicked_cmd(self):
        self.date_selected.emit(self.current_date)
        self.deleteLater()

    def create_calendar_widget(self):
        self.calendar_widget = TransparentWidget()
        self.calendar_layout = QVBoxLayout(self.calendar_widget)
        self.calendar_layout.setContentsMargins(0, 0, 0, 0)
        self.calendar_layout.setSpacing(0)
        widget_num = self.central_layout.count() - 1
        self.central_layout.insertWidget(widget_num, self.calendar_widget)

    def recreate_calendar_widget(self):
        old_widget = self.calendar_widget

        self.central_layout.removeWidget(old_widget)
        old_widget.setParent(None)
        old_widget.deleteLater()

        self.create_calendar_widget()

    def update_dynamic_label(self):
        readable_date = self.q_locale.toString(
            self.current_date,
            "d MMMM yyyy"
        )
        self.dynamic_label.setText(readable_date)

    def populate_months(self):
        self.menu_month.clear()

        for month in range(1, 13):
            month_name = self.q_locale.standaloneMonthName(
                month,
                QLocale.FormatType.LongFormat
            )

            action = QAction(month_name.capitalize(), self)
            action.setData(month)
            action.triggered.connect(self.month_menu_selected)
            self.menu_month.addAction(action)

    def populate_years(self):
        self.menu_year.clear()

        max_year = self.date_now.year()

        for year in range(self.min_year, max_year + 1):
            action = QAction(str(year), self)
            action.setData(year)
            action.triggered.connect(self.year_menu_selected)
            self.menu_year.addAction(action)

    def month_menu_selected(self):
        action: QAction = self.sender()
        selected_month = action.data()

        year = self.current_date.year()
        current_day = self.current_date.day()

        days_in_new_month = QDate(year, selected_month, 1).daysInMonth()
        target_day = min(current_day, days_in_new_month)

        self.current_date = QDate(year, selected_month, target_day)
        self.update_calendar()

    def year_menu_selected(self):
        action: QAction = self.sender()
        selected_year = action.data()

        current_month = self.current_date.month()
        current_day = self.current_date.day()

        days_in_new_month = QDate(
            selected_year,
            current_month,
            1
        ).daysInMonth()

        target_day = min(current_day, days_in_new_month)

        self.current_date = QDate(
            selected_year,
            current_month,
            target_day
        )

        self.update_calendar()

    def day_selected(self):
        sender_button: _CalendarDayBase = self.sender()
        day = sender_button.day

        current_year = self.current_date.year()
        current_month = self.current_date.month()

        self.current_date = QDate(
            current_year,
            current_month,
            day
        )

        self.update_calendar()

    def prev_month(self):
        min_date = QDate(self.min_year, 1, 1)
        new_date = self.current_date.addMonths(-1)

        if new_date >= min_date:
            self.current_date = new_date
            self.update_calendar()

    def next_month(self):
        max_date = QDate(self.date_now.year(), 12, 31)
        new_date = self.current_date.addMonths(1)

        if new_date <= max_date:
            self.current_date = new_date
            self.update_calendar()

    def count_widgets(self):
        widgets = self.findChildren((TransparentWidget, CalendarDaySelected, CalendarDay))
        count = len(widgets) + 1
        print(f"Widgets: {count}")
        return count

    def update_calendar(self):
        self.update_dynamic_label()
        # print(self.count_widgets())

        current_year = self.current_date.year()
        current_month = self.current_date.month()
        current_day_val = self.current_date.day()

        month = self.q_locale.standaloneMonthName(
            current_month,
            QLocale.FormatType.LongFormat
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


        self.recreate_calendar_widget()

        header_widget = TransparentWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        for col in range(7):
            week = self.q_locale.dayName(
                col + 1,
                QLocale.FormatType.ShortFormat
            )

            lbl_day = GrayTextLabel(week.capitalize())
            lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_day.setFixedSize(*self.cell_size)

            header_layout.addWidget(lbl_day)

        self.calendar_layout.addWidget(header_widget)

        sep = UHorizontalSep()
        self.calendar_layout.addWidget(sep)

        first_day = QDate(current_year, current_month, 1)
        start_col = first_day.dayOfWeek() - 1
        days_in_month = first_day.daysInMonth()

        weeks = []
        current_week = [None] * 7

        for day in range(1, days_in_month + 1):
            index = start_col + day - 1
            col = index % 7

            current_week[col] = day

            if col == 6:
                weeks.append(current_week)
                current_week = [None] * 7

        if any(day is not None for day in current_week):
            weeks.append(current_week)

        for week_index, week in enumerate(weeks):
            week_widget = TransparentWidget()
            week_layout = QHBoxLayout(week_widget)
            week_layout.setContentsMargins(0, 0, 0, 0)
            week_layout.setSpacing(0)

            for day in week:
                if day is None:
                    empty = TransparentWidget()
                    empty.setFixedSize(*self.cell_size)
                    week_layout.addWidget(empty)
                    continue

                if day == current_day_val:
                    btn_day = CalendarDaySelected(str(day), day)
                    btn_day.setFixedSize(*self.cell_size)
                    btn_day.setPixmap(self.blue_circle_pixmap)

                    btn_day_text = TransparentLabel(
                        text=str(day),
                        parent=btn_day
                    )
                    btn_day_text.setGeometry(btn_day.rect())
                    btn_day_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    btn_day_text.setAttribute(
                        Qt.WidgetAttribute.WA_TransparentForMouseEvents
                    )
                else:
                    btn_day = CalendarDay(str(day), day)
                    btn_day.setFixedSize(*self.cell_size)

                btn_day.clicked.connect(self.day_selected)
                week_layout.addWidget(btn_day)

            self.calendar_layout.addWidget(week_widget)

            if week_index < len(weeks) - 1:
                self.calendar_layout.addWidget(UHorizontalSep())

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()

        return super().keyPressEvent(a0)
