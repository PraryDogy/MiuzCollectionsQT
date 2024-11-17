import json
import os
import sqlite3
import subprocess

import sqlalchemy

from cfg import APP_SUPPORT_DIR, DB_FILE, JsonData
from database import THUMBS, Dbase

RESERV_FILE = os.path.join(APP_SUPPORT_DIR, "RESERV.json")


class AdminDb:

    @classmethod
    def start(cls):
        print(
            "1 to db compare",
            "2 to reserv database",
            sep="\n"
            )
        
        user_input = input()

        if user_input == "1":
            cls.compare()

        elif user_input == "2":
            cls.reserv_db()

    @classmethod
    def compare(cls):
        JsonData.init()
        Dbase.create_engine()

        inspector = sqlalchemy.inspect(Dbase.engine)

        app_support_clmns = [
            i.get("name")
            for i in inspector.get_columns(THUMBS.name)
            ]

        inner_clmns = [
            i.name
            for i in THUMBS.columns
        ]

        remove_clmns = [
            i
            for i in app_support_clmns
            if i not in inner_clmns
            ]

        add_clmns = [
            i
            for i in inner_clmns
            if i not in app_support_clmns
            ]
        
        print(
            f"remove: {remove_clmns}",
            f"add: {add_clmns}",
            sep="\n"
            )

    @classmethod
    def reserv_db(cls):

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        q = f"SELECT * from {THUMBS.name}"

        res = cursor.execute(q).fetchall()
        names = list(map(lambda x: x[0], cursor.description))
        res_dict: list[dict] = []

        for i in res:

            item = {
                names[x]: value
                for x, value in enumerate(i)
                }
            
            res_dict.append(item)

        if res_dict:
            
            with open(RESERV_FILE, "w") as file:
                json.dump(res_dict, file, ensure_ascii=False, indent=4)

            subprocess.call(["open", "-R", RESERV_FILE])

            print("done")
        
        else:
            print("result empty")


AdminDb.start()