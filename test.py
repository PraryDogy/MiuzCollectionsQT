from copy import deepcopy

class Mf:
    def __init__(self, value: int):
        super().__init__()
        self.value = value


class GlobalTest:
    lst = [
        Mf(1),
        Mf(2),
        Mf(3),
        Mf(4),
        Mf(5)
    ]


class Settings:

    def __init__(self, copy_lst: list[Mf]):
        super().__init__()
        self.copy_lst = copy_lst


copy_lst = deepcopy(GlobalTest.lst)
a = Settings(copy_lst)
a.copy_lst[-1].value = 555555
print(GlobalTest.lst[-1].value)



from dataclasses import dataclass

@dataclass
class Abc:
    test: deepcopy[list[str]]