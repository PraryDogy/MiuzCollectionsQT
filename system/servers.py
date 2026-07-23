import json
import os

from cfg import JsonData, Static
from system.lang import Lng


class Servers:
    items = []

    @classmethod
    def validate_json(cls):
        try:
            with open(Static.external_servers, "r", encoding="utf-8") as file:
                data: list[list[str]] = json.load(file)
        except Exception as e:
            print("Servers, error reading file", e)
            return False

        if not isinstance(data, list):
            print("Servers: json data не является списком")
            return False

        if len(data) == 0:
            print("Servers: json data список пуст")
            return False

        servers = []
        for server_data in data:
            if isinstance(server_data, list):
                if (x for x in server_data if isinstance(x, str)):
                    servers.append(server_data)
        if not servers:
            return False

        return servers

    @classmethod
    def json_to_app(cls, data: list[list[str]]):
        cls.items.clear()
        cls.items = data

    @classmethod
    def write_json_data(cls):
        with open(Static.external_servers, "w", encoding="utf-8") as file:
            json.dump(cls.items, file, indent=4, ensure_ascii=False)