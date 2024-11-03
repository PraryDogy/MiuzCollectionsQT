import re
from datetime import datetime, timedelta
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QSpacerItem, QWidget

from base_widgets import Btn, InputBase, LayoutH, LayoutV, WinStandartBase
from cfg import Dynamic
from signals import signals_app


class DateUtils:
    @staticmethod
    def date_to_text(date: datetime):
        return date.strftime("%d.%m.%Y")

    @staticmethod
    def add_or_subtract_days(date: datetime, days: int):
        return date + timedelta(days=days)
    
    @staticmethod
    def text_to_datetime_date(text: str):
        return datetime.strptime(text, "%d.%m.%Y").date()


class ReDate:
    def __init__(self, text: str):
        self.converted_text = None
        t_reg = re.match(r"\d{,2}\W\d{,2}\W\d{4}", text)
        if t_reg:
            self.converted_text = re.sub("\W", ".", t_reg.group(0))


class ConvertDate:
    def __init__(self, text: str):
        try:
            self.date = DateUtils.text_to_datetime_date(text)
        except (ValueError, TypeError):
            self.date = None


class BaseDateInput(InputBase):
    inputChangedSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)
        self.setPlaceholderText(Dynamic.lng.d_m_y)
        self.textChanged.connect(self.onTextChanged)
        self.date = None

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Up:
            if self.date:
                self.date = DateUtils.add_or_subtract_days(self.date, 1)
                self.setText(DateUtils.date_to_text(self.date))
            else:
                self.date = datetime.today().date()
                self.setText(DateUtils.date_to_text(self.date))

        elif a0.key() == Qt.Key.Key_Down:
            if self.date:
                self.date = DateUtils.add_or_subtract_days(self.date, -1)
                self.setText(DateUtils.date_to_text(self.date))
            else:
                self.date = datetime.today().date()
                self.setText(DateUtils.date_to_text(self.date))

        return super().keyPressEvent(a0)

    def onTextChanged(self):
        date_check = ReDate(self.text()).converted_text
        new_date = ConvertDate(date_check).date

        if new_date:
            self.setText(date_check)
            self.date = ConvertDate(date_check).date
        else:
            self.date = None

        self.inputChangedSignal.emit()


class FiltersDateBtncolor:

    @staticmethod
    def date_based_color():
        if not Dynamic.date_start:
            signals_app.dates_btn_style.emit("normal")
        else:
            signals_app.dates_btn_style.emit("blue")

    @staticmethod
    def set_border():
        signals_app.dates_btn_style.emit("border")


class TitleLabel(QLabel):
    def __init__(self, default_text: str):
        self.default_text = "\n" + default_text

        super().__init__(self.default_text)
        self.setFixedWidth(150)

    def set_named_date_text(self, date: datetime):
        weekday = self.get_named_weekday(date).capitalize()
        named_date = self.get_named_date(date)

        self.setText(f"{weekday}:\n{named_date}")

    def set_default_text(self):
        self.setText(self.default_text)

    def get_named_weekday(self, date: datetime) -> str:
        return Dynamic.lng.weekdays[str(date.weekday())]
    
    def get_named_date(self, date: datetime) -> str:
        month = Dynamic.lng.months_genitive_case[str(date.month)]
        return f"{date.day} {month} {date.year}"


class BaseDateLayout(QWidget):
    dateChangedSignal = pyqtSignal()

    def __init__(self, title_label_text):
        super().__init__()

        layout_v = LayoutV()
        self.setLayout(layout_v)

        self.title_label = TitleLabel(title_label_text)
        layout_v.addWidget(self.title_label)

        spacer_item = QSpacerItem(1, 5)
        layout_v.addSpacerItem(spacer_item)

        self.input = BaseDateInput()
        self.input.inputChangedSignal.connect(self.input_changed)
        layout_v.addWidget(self.input)

    def input_changed(self):
        date = self.get_datetime_date()

        if date:
            self.title_label.set_named_date_text(date)
        else:
            self.title_label.set_default_text()

        self.dateChangedSignal.emit()

    def get_datetime_date(self):
        return self.input.date


class LeftDateWidget(BaseDateLayout):
    def __init__(self):
        super().__init__(Dynamic.lng.start)

        if Dynamic.date_start:
            self.input.setText(DateUtils.date_to_text(Dynamic.date_start))


class RightDateWidget(BaseDateLayout):
    def __init__(self):
        super().__init__(Dynamic.lng.end)

        if Dynamic.date_end:
            self.input.setText(DateUtils.date_to_text(Dynamic.date_end))


class WinDates(WinStandartBase):
    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.my_close)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        FiltersDateBtncolor.set_border()
        self.disable_min()
        self.disable_max()
        self.set_title(Dynamic.lng.dates)

        self.date_start = Dynamic.date_start
        self.date_end = Dynamic.date_end

        self.init_ui()
        self.fit_size()
        self.center_win(parent=parent)

    def init_ui(self):
        title_label = QLabel(Dynamic.lng.search_dates)
        title_label.setContentsMargins(0, 0, 0, 5)
        self.content_layout.addWidget(title_label)

        widget_wid = QWidget()
        widget_layout = LayoutH()
        widget_wid.setLayout(widget_layout)
        self.content_layout.addWidget(widget_wid)

        self.left_date = LeftDateWidget()
        self.left_date.dateChangedSignal.connect(partial(self.date_change, "start"))
        widget_layout.addWidget(self.left_date)

        spacer_item = QSpacerItem(10, 1)
        widget_layout.addItem(spacer_item)

        self.right_date = RightDateWidget()
        self.right_date.dateChangedSignal.connect(partial(self.date_change, "end"))
        widget_layout.addWidget(self.right_date)

        # ok cancel button

        buttons_wid = QWidget()
        buttons_layout = LayoutH()
        buttons_wid.setLayout(buttons_layout)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        self.content_layout.addWidget(buttons_wid)

        buttons_layout.addStretch(1)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ok_label = Btn(Dynamic.lng.ok)
        self.ok_label.mouseReleaseEvent = self.ok_cmd
        buttons_layout.addWidget(self.ok_label)

        spacer_item = QSpacerItem(10, 1)
        buttons_layout.addItem(spacer_item)

        cancel_label = Btn(Dynamic.lng.cancel)
        cancel_label.mouseReleaseEvent = self.cancel_cmd
        buttons_layout.addWidget(cancel_label)
        buttons_layout.addStretch(1)

    def date_change(self, flag: str):
        if flag == "start":
            new_date = self.left_date.get_datetime_date()
            self.date_start = new_date
        else:
            new_date = self.right_date.get_datetime_date()
            self.date_end = new_date

        if new_date:
            self.ok_label.setDisabled(False)
        else:
            self.ok_label.setDisabled(True)

    def named_date(self, date: datetime):
        month = Dynamic.lng.months_genitive_case[str(date.month)]
        return f"{date.day} {month} {date.year}"

    def ok_cmd(self, event):
        if not any((self.date_start, self.date_end)):
            return

        elif not self.date_start:
            return

        elif not self.date_end:
            self.date_end = self.date_start
            self.date_end = datetime.today().date()

        Dynamic.date_start = self.date_start
        Dynamic.date_end = self.date_end

        Dynamic.date_start_text = self.named_date(date=Dynamic.date_start)
        Dynamic.date_end_text = self.named_date(date=Dynamic.date_end)

        FiltersDateBtncolor.date_based_color()
        self.close()

        signals_app.reload_thumbnails.emit()

    def cancel_cmd(self, event):
        FiltersDateBtncolor.date_based_color()
        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            FiltersDateBtncolor.date_based_color()
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)

    def my_close(self, event):
        FiltersDateBtncolor.date_based_color()
        self.close()