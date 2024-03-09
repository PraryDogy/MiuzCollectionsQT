from datetime import datetime, timedelta


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