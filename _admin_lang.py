import json

class AdminLang:

    @classmethod
    def start(cls):

        with open("lang/lang.json", "r") as file:
            data: dict = json.load(file)

        rows = []
        for k, v in data.items():
            new_row = cls.create_row(k, v)
            rows.append(new_row)

        new_text = "\n".join(rows)

        with open("_lang.py", "w") as file:
            file.write(new_text)


    @classmethod
    def create_row(cls, k, v):
        new_k = f"{cls.quoted(k)} = "
        new_v = f"[{cls.quoted(v[0])}, {cls.quoted(v[1])}]"

        return new_k + new_v

    @classmethod
    def quoted(cls, text: str):
        return f"\"{text}\""

        
AdminLang.start()