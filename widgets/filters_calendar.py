from datetime import datetime, timedelta
from typing import Literal

from PyQt5.QtCore import QDate, QLocale, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIcon, QKeyEvent, QTextCharFormat
from PyQt5.QtWidgets import (QCalendarWidget, QGroupBox, QLabel, QSizePolicy,
                             QSpinBox, QTabWidget, QToolButton, QVBoxLayout,
                             QWidget)

from cfg import Cfg, Dynamic
from system.filters import Filters
from system.lang import Lng

from ._base_widgets import (HSep, SmallBtn, UHBoxLayout, VListSpacerItem,
                            VListWidgetItem, UMainWindow, UVBoxLayout,
                            VListWidget)


class CheckableItem(VListWidgetItem):
    hh = 25

    def __init__(self, parent, text = None):
        super().__init__(parent, self.hh, text)
        self.setFlags(
            self.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        self.setCheckState(
            Qt.CheckState.Unchecked
        )


class WinFilters(QWidget):
    closed_ = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    ww = 300
    hh = 300

    def __init__(self):
        super().__init__()
        self.central_layout = QVBoxLayout(self)
        self.central_layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = VListWidget()
        self.list_widget.itemClicked.connect(self.item_cmd)
        self.central_layout.addWidget(self.list_widget)

        favs_item = CheckableItem(
            parent=self.list_widget,
            text=Lng.favorites[Cfg.lng_index]
        )
        self.list_widget.addItem(favs_item)
        if Dynamic.filter_favs:
            favs_item.setCheckState(Qt.CheckState.Checked)

        folder_item = CheckableItem(
            parent=self.list_widget,
            text=Lng.only_this_folder[Cfg.lng_index]
        )
        self.list_widget.addItem(folder_item)
        if Dynamic.filter_only_folder:
            folder_item.setCheckState(Qt.CheckState.Checked)

        self.list_widget.addItem(
            VListSpacerItem(parent=self.list_widget)
        )

        for i in Filters.items:
            item = CheckableItem(
                parent=self.list_widget,
                text=i
            )
            self.list_widget.addItem(item)
            if i in Dynamic.filters_enabled:
                item.setCheckState(Qt.CheckState.Checked)

        self.list_widget.setCurrentRow(0)

        self.central_layout.setSpacing(10)
        marings = self.central_layout.contentsMargins()
        marings.setBottom(15)
        self.central_layout.setContentsMargins(marings)

        self.reset_btn = SmallBtn(Lng.reset[Cfg.lng_index])
        self.reset_btn.setFixedWidth(100)
        self.reset_btn.clicked.connect(self.reset_cmd)
        self.central_layout.addWidget(
            self.reset_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

    def item_cmd(self, item: VListWidgetItem):
        if isinstance(item, VListSpacerItem):
            return
        if item.text() == Lng.favorites[Cfg.lng_index]:
            if Dynamic.filter_favs:
                Dynamic.filter_favs = False
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                Dynamic.filter_favs = True
                item.setCheckState(Qt.CheckState.Checked)
        elif item.text() == Lng.only_this_folder[Cfg.lng_index]:
            if Dynamic.filter_only_folder:
                Dynamic.filter_only_folder = False
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                Dynamic.filter_only_folder = True
                item.setCheckState(Qt.CheckState.Checked)
        elif item.text() in Dynamic.filters_enabled:
            Dynamic.filters_enabled.remove(item.text())
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            Dynamic.filters_enabled.append(item.text())
            item.setCheckState(Qt.CheckState.Checked)
        self.reload_thumbnails.emit()

    def reset_cmd(self):
        items = [
            self.list_widget.item(i)
            for i in range(self.list_widget.count())
        ]
        # удаляем спейсер
        items.pop(2)
        for item in items:
            item.setCheckState(Qt.CheckState.Unchecked)
        Dynamic.filter_favs = False
        Dynamic.filter_only_folder = False
        Dynamic.filters_enabled.clear()
        self.reload_thumbnails.emit()
        self.deleteLater()

    def mouseReleaseEvent(self, a0):
        return super().mouseReleaseEvent(a0)

    def closeEvent(self, a0):
        self.closed_.emit()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.closed_.emit()
        return super().deleteLater()
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    


class DatesTools:
    @classmethod
    def date_to_text(cls, date: datetime):
        return date.strftime("%d.%m.%Y")

    @classmethod
    def add_or_subtract_days(cls, date: datetime, days: int):
        return date + timedelta(days=days)
    
    @classmethod
    def text_to_datetime_date(cls, text: str):
        return datetime.strptime(text, "%d.%m.%Y").date()


class DatesTitle(QLabel):
    def __init__(self, default_text: str):
        super().__init__()
        self.default_text = default_text
        self.setText(default_text)

    def set_named_date_text(self, date: datetime):
        weekday = self.get_named_weekday(date)
        named_date = self.get_named_date(date)
        text = f"{named_date}, {weekday}"
        self.setText(text)

    def set_default_text(self):
        self.setText(self.default_text)

    def get_named_weekday(self, date: datetime) -> str:
        day_number = str(date.weekday())
        return Lng.weekdays_short[Cfg.lng_index][day_number]
    
    def get_named_date(self, date: datetime) -> str:
        month_number = str(date.month)
        month = Lng.months_gen[Cfg.lng_index][month_number]
        return f"{date.day} {month} {date.year}"
    
    def setText(self, a0):
        a0 = " " + a0
        return super().setText(a0)


class MyCalendar(QGroupBox):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, title: str):
        super().__init__()
        v_layout = UVBoxLayout(self)
        v_layout.setSpacing(10)
        margins = v_layout.contentsMargins()
        margins.setTop(5)
        v_layout.setContentsMargins(margins)

        self.title = DatesTitle(title)
        v_layout.addWidget(self.title)

        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        self.calendar.setMinimumDate(QDate(2000, 1, 1))
        self.calendar.setFixedSize(300, 300)

        v_layout.addWidget(self.calendar)
        if Cfg.lng_index == 0:
            self.calendar.setLocale(QLocale(QLocale.Language.Russian))
        else:
            self.calendar.setLocale(QLocale(QLocale.Language.English))
        self.calendar.clicked.connect(self.on_date_clicked)
        self.set_custom_ui()

    def on_date_clicked(self, date: QDate):
        self.dateSelected.emit(date)

    def set_date(self, py_date: datetime):
        qdate = QDate(py_date.year, py_date.month, py_date.day)
        self.calendar.setSelectedDate(qdate)

    def highlight_range(self, start_date: datetime, end_date: datetime):
        # Преобразуем datetime в QDate
        q_start = QDate(start_date.year, start_date.month, start_date.day)
        q_end = QDate(end_date.year, end_date.month, end_date.day)
        
        # Настраиваем стиль выделения
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(100, 150, 255, 100)) # Светло-синий цвет фона
        # fmt.setForeground(QColor("white")) # Можно также изменить цвет текста
        
        # Сначала очищаем предыдущие выделения (опционально)
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        
        # Проходим циклом по всем датам диапазона и применяем формат
        current = q_start
        while current <= q_end:
            self.calendar.setDateTextFormat(current, fmt)
            current = current.addDays(1)

        self.calendar.update()

    def set_custom_ui(self, icon_size: int = 10):
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

        widgets = self.findChildren(QToolButton)
        for wid in widgets:
            name = wid.objectName()
            if name == "qt_calendar_prevmonth":
                wid.setIcon(QIcon("./images/prev.svg"))
            elif name == "qt_calendar_nextmonth":
                wid.setIcon(QIcon("./images/next.svg"))

        for child in self.calendar.findChildren(QSpinBox):
            child.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        self.calendar.setStyleSheet("""
            #qt_calendar_monthbutton::menu-indicator {
                image: none;
                width: 0px;
            }

            #qt_calendar_prevmonth,
            #qt_calendar_nextmonth,
            #qt_calendar_monthbutton,
            #qt_calendar_yearbutton {
                height: 25px;
                background: transparent;                                 
            }

            #qt_calendar_prevmonth,
            #qt_calendar_nextmont {
                width: 25px;
            }

            #qt_calendar_prevmonth:hover,
            #qt_calendar_nextmonth:hover,
            #qt_calendar_monthbutton:hover,
            #qt_calendar_yearbutton:hover {                  
                background: transparent;  
                border: transparent;
                color: white;                                 
            }
        """)


class WinDates(QWidget):
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.central_layout = QVBoxLayout(self)
        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 10)

        dates_h_wid = QWidget()
        self.central_layout.addWidget(dates_h_wid)
        dates_h_lay = UHBoxLayout()
        dates_h_lay.setSpacing(10)
        dates_h_wid.setLayout(dates_h_lay)

        self.left_calendar = MyCalendar(Lng.start_date[Cfg.lng_index])
        self.left_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="start")
        )
        dates_h_lay.addWidget(self.left_calendar)

        self.right_calendar = MyCalendar(Lng.end_date[Cfg.lng_index])
        self.right_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="end")
        )
        dates_h_lay.addWidget(self.right_calendar)

        self.central_layout.addWidget(HSep())

        clear_btn = SmallBtn(text=Lng.reset[Cfg.lng_index])
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_btn_cmd)
        self.central_layout.addWidget(
            clear_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        m = self.central_layout.contentsMargins()
        m.setBottom(15)
        self.central_layout.setContentsMargins(m)
        if Dynamic.date_start:
            self.left_calendar.highlight_range(
                Dynamic.date_start, Dynamic.date_end
            )
            self.left_calendar.title.set_named_date_text(Dynamic.date_start)
        if Dynamic.date_end:
            self.right_calendar.highlight_range(
                Dynamic.date_start, Dynamic.date_end
            )
            self.right_calendar.title.set_named_date_text(Dynamic.date_end)

        self.adjustSize()

    def clear_btn_cmd(self, *args):
        reload = True
        if not Dynamic.date_start or not Dynamic.date_end:
            reload = False
        Dynamic.loaded_thumbs = 0
        Dynamic.date_start = None
        Dynamic.date_end = None
        Dynamic.f_date_start = None
        Dynamic.f_date_end = None
        if reload:
            self.reload_thumbnails.emit()
            self.dates_btn_normal.emit()
            self.deleteLater()

    def date_change(self, date: QDate, flag: Literal["start", "end"]):
        date = date.toPyDate()
        if flag == "start":
            Dynamic.date_start = date
            self.left_calendar.title.set_named_date_text(date)
        else:
            Dynamic.date_end = date
            self.right_calendar.title.set_named_date_text(date)
            self.left_calendar.calendar.setMaximumDate(
                QDate(date.year, date.month, date.day)
            )            

        if all((Dynamic.date_start, Dynamic.date_end)):
            Dynamic.f_date_start = self.named_date(Dynamic.date_start)
            Dynamic.f_date_end = self.named_date(Dynamic.date_end)
            self.reload_thumbnails.emit()
            self.dates_btn_solid.emit()

            for i in (self.left_calendar, self.right_calendar):
                i.highlight_range(Dynamic.date_start, Dynamic.date_end)
    
    def named_date(self, date: datetime) -> str:
        return date.strftime("%d.%m.%Y")
    
    def closeEvent(self, a0):
        if not all((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn_normal.emit()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        if not all((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn_normal.emit()
        return super().deleteLater()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class FiltersCalendar(UMainWindow):

    def __init__(self):
        super().__init__()

        self.tab_bar = QTabWidget()
        self.central_layout.addWidget(self.tab_bar)
        self.tab_bar.addTab(WinFilters(), "Фильтры")
        self.tab_bar.addTab(WinDates(), "Календарь")