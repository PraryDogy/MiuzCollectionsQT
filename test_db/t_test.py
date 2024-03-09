import os
from random import randint

import sqlalchemy
from t_database import Dbase, Queries, TestMd

values = {"src": str, "size": int, "created": int}


def new_values():
    return [
        {
            "src": str(666),
            "size": randint(i, 1000000),
            "created": randint(i, 1000000)
            }
        for i in range(0, 15)
        ]
