import json
import os
import shutil

LANG_DIR = "lang"
LANG_JSON = os.path.join(LANG_DIR, "lang.json")
PY_RUS = os.path.join(LANG_DIR, "rus.py")
PY_ENG = os.path.join(LANG_DIR, "eng.py")
CLASS_RUS = "Rus"
CLASS_ENG = "Eng"

EXCLUDE = ["_MACOSX", "env", "__pycache__", "lang"]
PREFIX = "Dynamic.lng."
KEY_NAME = PREFIX + "name"

class LangAdmin:
    JSON_DATA: dict = None

    @classmethod
    def read_json_file(cls) -> dict[str, list[str, str]]:
        with open(LANG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    
    @classmethod
    def write_json_file(cls, data: dict[str, list[str, str]]):
        with open(LANG_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)

    @classmethod
    def start(cls):
        print("1 add lang key")
        print("2 remove lang key")
        print("3 update py lang files by json")
        print("4 remove unused lang items")
        print("5 remove empty folders and pyc files")

        user_input = input()

        if user_input == "1":
            cls.add_new_key()
        elif user_input == "2":
            cls.remove_key()
        elif user_input == "3":
            cls.update_py_files_with_json()
        elif user_input == "4":
            cls.remove_unused_keys()
        elif user_input == "5":
            cls.remove_empty_dirs()

    @classmethod
    def add_new_key(cls):
        data = cls.read_json_file()

        print("write key name to ADD")
        key_name = input()

        print("write rus value")
        value_rus = input()

        print("write en value")
        value_eng = input()

        data[key_name] = [value_rus, value_eng]

        print("done: ", f"{key_name}: {value_rus}, {value_eng}")

        cls.write_json_file(data)
        cls.create_py_files()

    @classmethod
    def remove_key(cls):

        print("write key name for delete")

        data = cls.read_json_file()
        key_name = input()

        if data.get(key_name):
            data.pop(key_name)
            print("done")
        else:
            print("no key for delete")

        cls.write_json_file(data)
        cls.create_py_files()

    @classmethod
    def update_py_files_with_json(cls):
        cls.create_py_files()
        print("done")

    @classmethod
    def create_py(cls, filename: str, classname: str, data: dict):
        file_text = ""

        classname = f"class {classname}:"
        init_row = "\tdef __init__(self):"
        super_row = f"\t\tsuper().__init__()"

        for i in (classname, init_row, super_row):
            file_text += i
            file_text += "\n"

        for k, v in data.items():
            file_text += f"\t\tself.{k} = {repr(v)}"
            file_text += "\n"

        with open(filename, "w") as new:
            new.write(file_text)

    @classmethod
    def create_py_files(cls):

        data = cls.read_json_file()

        ru_data = {k: v[0] for k, v in data.items()}
        ru_data = dict(sorted(ru_data.items()))

        en_data = {k: v[1] for k, v in data.items()}
        en_data = dict(sorted(en_data.items()))

        cls.create_py(PY_RUS, CLASS_RUS, ru_data)
        cls.create_py(PY_ENG, CLASS_ENG, en_data)

    @classmethod
    def remove_unused_keys(cls):

        parrent = os.path.dirname(os.path.dirname(__file__))
        pyfiles = []

        for root, dirs, files in os.walk(top=parrent, topdown=True):
            dirs[:] = [d for d in dirs if d not in EXCLUDE]
            for file in files:
                if file.endswith(".py"):
                    pyfiles.append(os.path.join(root, file))

        json_data = cls.read_json_file()

        lng_keys: dict = {
            PREFIX + i: 0
            for i in list(json_data.keys())
            }
        
        if KEY_NAME in lng_keys:
            lng_keys.pop(KEY_NAME)

        for py_file in pyfiles:

            with open(file=py_file, mode="r") as py_f:
                py_text = py_f.read()

            for i in lng_keys.keys():

                if i in py_text:
                    lng_keys[i] += 1

        unused: list[str] = [
            k
            for k, v
            in lng_keys.items()
            if v == 0
            ]

        print("unused lang items: ", *unused, sep="\n")
        print("do you want to delete this items? 1 = yes")

        res = input()

        if res == "1":

            for i in unused:
                i = i.replace(PREFIX, "")
                json_data.pop(i)    

            cls.write_json_file(json_data)
            cls.create_py_files()
            print("done")

        else:
            print("canceled")

    @classmethod
    def remove_empty_dirs(cls):
        exclude = ["env", ".git", "__pycache__"]
        base_path = os.path.dirname(__file__)

        for root, dirs, files in os.walk(base_path):

            dirs[:] = [d for d in dirs if d not in exclude]

            if (
                all(filename.endswith('.pyc') for filename in files)
                or
                not files
                ):

                try:
                    shutil.rmtree(root)
                    print(f"Удалена папка: {root.replace(base_path, '...')}")
                except Exception as e:
                    print(f"Ошибка при удалении папки {root}: {e}")

LangAdmin.start()