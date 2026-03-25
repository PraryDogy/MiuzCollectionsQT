import json
import os

from cfg import Static


class Servers:
    server_list = []

    @classmethod
    def json_to_app(cls):
        try:
            with open(Static.external_servers, "r", encoding="utf-8") as f:
                server_list: list = json.load(f)
            for i in server_list:
                Servers.server_list.append(i)
        except Exception as e:
            print("Servers json to app error", e)
    
    @classmethod
    def write_json_data(cls):
        with open(Static.external_servers, "w", encoding="utf-8") as file:
            json.dump(cls.server_list, file, indent=4, ensure_ascii=False)