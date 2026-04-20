import json
import os

from cfg import Cfg, Static
from system.lang import Lng


class Servers:
    items = []

    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.external_servers, "r", encoding="utf-8") as f:
                server_list: list[list] = json.load(f)
            for i in server_list:
                if len(i) == 3:
                    i.insert(0, Lng.set_server_alias[Cfg.lng_index])
                Servers.items.append(i)
        except Exception as e:
            print("Servers json to app error", e)
    
    @classmethod
    def write_json_data(cls):
        with open(Static.external_servers, "w", encoding="utf-8") as file:
            json.dump(cls.items, file, indent=4, ensure_ascii=False)