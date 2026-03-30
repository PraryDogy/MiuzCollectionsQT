import json

from cfg import Static


class Filters:
    items = []

    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.external_filters, "r", encoding="utf-8") as f:
                data: list[str] = json.load(f)
            cls.items = [
                i
                for i in data
                if i not in cls.items
            ]
        except Exception as e:
            print("Filters json to app error", e)

    @classmethod
    def write_json_data(cls):
        with open(Static.external_filters, "w", encoding="utf-8") as f:
            json.dump(cls.items, f, indent=4, ensure_ascii=False)
