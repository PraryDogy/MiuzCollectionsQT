import json


def create_py(filename: str, classname: str, data: dict):

    with open(filename, "w", encoding="utf-8") as file:
        first_row = f"{classname}:\n"
        file.write(first_row)

        for k, v in data.items():

            if type(v) == str:
                if v.count("\n") == 0:
                    row = f"\t{k} = \"{v}\"\n"
                else:
                    v = v.replace("\n", "\\n")
                    row = f"\t{k} = \"{v}\"\n"

            elif type(v) == dict:
                row = f"\t{k} = {v}\n"

            file.write(row)


def create_all_files(file: str):
    with open(file, "r", encoding="utf-8") as file:
        data = json.load(file)

    ru_file = "lang/rus.py"
    en_file = "lang/eng.py"

    ru_class = "class Rus"
    en_class = "class Eng"

    ru_data = {k: v[0] for k, v in data.items()}
    en_data = {k: v[1] for k, v in data.items()}

    create_py(ru_file, ru_class, ru_data)
    create_py(en_file, en_class, en_data)
