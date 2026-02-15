from dataclasses import dataclass, asdict

@dataclass(slots=True)
class Test:
    data: dict


a = Test({"a": 1})

a.data.update({"b": 2})


print(asdict(a))
