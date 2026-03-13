import json
import os

from cfg import Static


class Filters:
    filter_list = []
    default_filters = [
        "/1 IMG/",
        "/2 MODEL IMG/",
        ".tif",
        ".psd",
        ".psb",
        ".jpg",
        ".jpeg",
        ".png"
    ]

    @classmethod
    def init(cls):
        if os.path.exists(Static.external_filters):
            with open(Static.external_filters, "r", encoding="utf-8") as f:
                for i in json.load(f):
                    if i not in cls.filter_list:
                        cls.filter_list.append(i)
        else:
            cls.filter_list.extend(cls.default_filters)

    @classmethod
    def write_json_data(cls):
        with open(Static.external_filters, "w", encoding="utf-8") as f:
            json.dump(cls.filter_list, f, indent=4, ensure_ascii=False)
