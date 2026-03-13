import json

from cfg import Static


class Filters:
    filter_list = []

    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.external_filters, "r", encoding="utf-8") as f:
                data: list[str] = json.load(f)
            cls.filter_list = [
                i
                for i in data
                if i not in cls.filter_list
            ]
        except Exception as e:
            ...

    @classmethod
    def write_json_data(cls):
        with open(Static.external_filters, "w", encoding="utf-8") as f:
            json.dump(cls.filter_list, f, indent=4, ensure_ascii=False)
