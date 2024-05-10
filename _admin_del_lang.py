import json
import os

from lang import create_all_files


class TrashKeys:
    def __init__(self, json_file: str):
        exclude = ["_MACOSX", "cv2 backup", "env", "_pycache_"]
        parrent = os.path.dirname(os.path.dirname(__file__))
        pyfiles = []

        for root, dirs, files in os.walk(top=parrent, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if file.endswith(".py"):
                    pyfiles.append(os.path.join(root, file))

        json_data: dict = {}

        with open(json_file, "r", encoding="utf-8") as f:
            json_data: dict = json.load(f)

        self.trash_keys = {i: 0 for i in json_data}

        for py in pyfiles:
            with open(file=py, mode="r") as py_f:
                py_text = py_f.read()

                for lng_key in json_data:

                    # lng is cfg.Config.lng variable
                    if f"lng.{lng_key}" in py_text:
                        self.trash_keys[lng_key] = +1

        self.trash_keys = [k for k, v in self.trash_keys.items() if v == 0]
        self.trash_keys.remove("name")

        print()
        print("unused lang keys: ", self.trash_keys)
        print("do you want to delete all this keys? 1 = yes, 2 = no")
        print()

        res = int(input())

        if res == 1:

            for i in self.trash_keys:
                json_data.pop(i)    

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            create_all_files(json_file)

            print("DONE remove trash keys")

        else:
            print("canceled")

TrashKeys("lang/lang.json")