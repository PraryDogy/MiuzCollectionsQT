import json

from .create_files import create_all_files


class LangAdmin:
    def __init__(self, file: str):
        with open(file, "r", encoding="utf-8") as f:
            data: dict = json.load(f)

        print("exist keys:")
        for i in data.keys():
            print(i)

        print()
        print("1 add new key")
        print("2 remove existing key")
        print("3 reload files")

        try:
            inp = int(input())
        except ValueError:
            inp = 4

        if inp == 1:
            print("write key name to ADD")
            key_name = input()

            print("write rus value")
            value_rus = input()

            print("write en value")
            value_eng = input()

            data[key_name] = [value_rus, value_eng]

            print("done add new")
            print(f"{key_name}: {value_rus, value_eng}")

        elif inp == 2:
            print("write key name to DELETE")
            key_name = input()

            try:
                data.pop(key_name)
            except KeyError:
                print("no key for delete")
                return

            print("done delete")

        elif inp == 3:
            data = dict(sorted(data.items()))

        else:
            print("ERROR: not 1 or 2")
            return
        
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        create_all_files(file)
