from cfg import JsonData



for k, v in JsonData.__dict__.items():
    if not k.startswith("__") and not isinstance(v, (classmethod)):
        print(k, v)