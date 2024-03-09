from PyQt5.QtWidgets import QLabel

from cfg import cnf
from datetime import datetime

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
        return cnf.lng.weekdays[str(date.weekday())]
    
    def get_named_date(self, date: datetime) -> str:
        month = cnf.lng.months_genitive_case[str(date.month)]
        return f"{date.day} {month} {date.year}"