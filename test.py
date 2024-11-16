import os
import traceback


class Utils:
    @classmethod
    def print_err(cls, error: Exception):
        tb = traceback.extract_tb(error.__traceback__)

        # Попробуем найти первую строчку стека, которая относится к вашему коду.
        for trace in tb:
            filepath = trace.filename
            filename = os.path.basename(filepath)
            
            # Если файл - не стандартный модуль, считаем его основным
            if not filepath.startswith("<") and filename != "site-packages":
                line_number = trace.lineno
                break
        else:
            # Если не нашли, то берем последний вызов
            trace = tb[-1]
            filepath = trace.filename
            filename = os.path.basename(filepath)
            line_number = trace.lineno

        print(f"{filepath}:{line_number}")
        print(error)


class Test:
    def test_two():
        raise ZeroDivisionError
    
import sqlalchemy

from database import THUMBS, Dbase


class More:
    def __init__(self):
        try:
            conn = Dbase.engine.connect()
            q = sqlalchemy.select(THUMBS)
            conn.execute(q)
        except Exception as e:
            Utils.print_err(parent=self, error=e)

a = More()