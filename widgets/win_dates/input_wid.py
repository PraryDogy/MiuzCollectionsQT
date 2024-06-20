import re
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent

from base_widgets import InputBase
from cfg import cnf

from .date_utils import DateUtils


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
        self.setPlaceholderText(cnf.lng.d_m_y)
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
