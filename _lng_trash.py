import json
import os

from lang import create_all_files


class TrashKeys:
    def __init__(self, json_file: str):

        exclude = ["_MACOSX", "env", "__pycache__", "lang"]
        parrent = os.path.dirname(os.path.dirname(__file__))

        pyfiles = []

        for root, dirs, files in os.walk(top=parrent, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if file.endswith(".py"):
                    pyfiles.append(os.path.join(root, file))

        with open(json_file, "r", encoding="utf-8") as f:
            json_data: dict = json.load(f)

        lng_keys = list(json_data.keys())
        lng_keys.remove("name")

        prefix = "Dynamic.lng."
        lng_keys = {prefix + i: 0 for i in lng_keys}

        for py_file in pyfiles:

            with open(file=py_file, mode="r") as py_f:
                py_text = py_f.read()

            for i in lng_keys.keys():

                if i in py_text:
                    lng_keys[i] += 1

        lng_keys: list[str] = [k for k, v in lng_keys.items() if v == 0]

        print()
        print("unused lang keys: ", *lng_keys, sep="\n")
        print("do you want to delete all this keys? 1 = yes")
        print()

        res = input()

        if res == "1":

            for i in lng_keys:
                i = i.replace(prefix, "")
                json_data.pop(i)    

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            create_all_files(json_file)

            print("DONE remove trash keys")

        elif res != 1:
            print("canceled")

TrashKeys("lang/lang.json")