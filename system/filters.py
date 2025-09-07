import os
import json
from cfg import Static, Dynamic

class Filters:
    filepath = os.path.join(Static.APP_SUPPORT_DIR, "filters.json")
    filters = set()
    default = [
        "/1 IMG/",
        "/2 MODEL IMG/",
    ]

    @classmethod
    def init(cls):
        cls.filters.update(cls.default)
        if os.path.exists(cls.filepath):
            with open(cls.filepath, "r", encoding="utf-8") as f:
                cls.filters.update(json.load(f))

    @classmethod
    def write_file(cls):
        with open(cls.filepath, "w", encoding="utf-8") as f:
            json.dump(list(cls.filters), f, indent=4, ensure_ascii=False)
