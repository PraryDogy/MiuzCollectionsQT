import json

from cfg import Static


class Filters:
    items = []

    @classmethod
    def validate_json(cls):
        try:
            with open(Static.external_filters, "r", encoding="utf-8") as file:
                data: list[str] = json.load(file)
        except Exception as e:
            print("Filters, error reading file", e)
            return False

        if not isinstance(data, list):
            print("Filters: json data не является списком")
            return False

        if len(data) == 0:
            print("Filters: json data список пуст")
            return False

        filters = []
        for i in data:
            if isinstance(i, str):
                filters.append(i)
        if not filters:
            print("Filters, нет string фильтров")
            return False

        return filters

    @classmethod
    def json_to_app(cls, data: list[str]):
        cls.items.clear()
        cls.items.extend(data)

    @classmethod
    def write_json_data(cls):
        with open(Static.external_filters, "w", encoding="utf-8") as f:
            json.dump(cls.items, f, indent=4, ensure_ascii=False)
