images = {
    "insert": {},
    "update": {
        "upd1": "_val1",
        "upd2": "_val2",
        "upd3": "_upd3",
        "upd4": "_upd4",
        "upd5": "_upd5",
        "upd6": "_upd6"
        }
        }


data: dict = images["update"]
data_keys: list = list(data.keys())
limit = 4

chunks = [
    {
        key: data[key]
        for key in data_keys[i:i + limit]
        }
        for i in range(0, len(data), limit)
        ]


print(chunks)