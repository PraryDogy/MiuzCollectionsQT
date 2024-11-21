import json
from cfg import Filter, JsonData


JsonData.init()

print(JsonData.filters)

JsonData.filters = [
    i.get_data()
    for i in Filter.filters
]