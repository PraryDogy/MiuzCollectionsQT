from cfg import JsonData, Static
import json

with open(Static.JSON_FILE, "r") as f:
    data: dict = json.load(f)


for k, v in data.items():
    print(v, type(v))