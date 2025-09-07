import os
import json
from cfg import Static, Dynamic

class Filters:
    filepath = os.path.join(Static.APP_SUPPORT_DIR, "filters.json")
    filters = []
    default = [
        "/1 IMG/",
        "/2 MODEL IMG/",
        ".tiff",
        ".psd",
        ".psb",
        ".jpg",
        ".jpeg",
        ".png"
    ]

    @classmethod
    def init(cls):
        cls.filters.extend(cls.default)
        if os.path.exists(cls.filepath):
            with open(cls.filepath, "r", encoding="utf-8") as f:
                for i in json.load(f):
                    if i not in cls.filters:
                        cls.filters.append(i)

    @classmethod
    def write_file(cls):
        with open(cls.filepath, "w", encoding="utf-8") as f:
            json.dump(cls.filters, f, indent=4, ensure_ascii=False)
