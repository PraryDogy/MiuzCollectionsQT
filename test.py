import sqlalchemy

from database import THUMBS, Dbase
import os

class JsonData:

    some_var = "test"

    prod_ = {
        "en": "Product",
        "ru": "Предметка",
        "real": "1 IMG",
        "value": False
        }
    
    model_ = {
        "en": "Model",
        "ru": "Модели",
        "real": "2 MODEL IMG",
        "value": False
        }
    
    other_ = {
        "en": "Other",
        "ru": "Остальное",
        "real": "",
        "value": True
        }

    @classmethod
    def get_data(cls):
        return [
            i for i in dir(cls)
            if not i.startswith("__")
            and
            not callable(getattr(cls, i))
            ]


all_ = set(
    i.get("value")
    for i in (JsonData.prod_, JsonData.model_, JsonData.other_)
    )

print(len(all_))