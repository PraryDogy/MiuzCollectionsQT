from dataclasses import dataclass

class Test:
    scaner = 0


@dataclass(slots=True)
class DataTest:
    scaner: int


data = DataTest(scaner=Test.scaner)
data.scaner = 111

print(Test.scaner)