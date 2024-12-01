from database import THUMBS, Dbase, CLMN_NAMES
import sqlalchemy
from cfg import JsonData

def get_values():
    return {
        "short_src": "",
        "short_hash": "",
        "size": "",
        "birth": "",
        "mod": "",
        "resol": "",
        "coll": "",
        "fav": "",
        "brand": ""
    }


assert CLMN_NAMES == list(get_values().keys())