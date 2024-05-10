import json


def create_py(filename: str, classname: str, data: dict):
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


def create_all_files(file: str):
    with open(file, "r", encoding="utf-8") as file:
        data: dict = json.load(file)

    ru_file = "lang/rus.py"
    en_file = "lang/eng.py"

    ru_class = "Rus"
    en_class = "Eng"

    ru_data = {k: v[0] for k, v in data.items()}
    ru_data = dict(sorted(ru_data.items()))

    en_data = {k: v[1] for k, v in data.items()}
    en_data = dict(sorted(en_data.items()))

    create_py(ru_file, ru_class, ru_data)
    create_py(en_file, en_class, en_data)
