import os

import sqlalchemy

from cfg import JsonData
from database import THUMBS, Dbase

JsonData.init()
Dbase.init()
conn = Dbase.engine.connect()
