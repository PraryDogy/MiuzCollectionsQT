from typing import Literal



class Test:
    KIND_VALUES = ["test", "some"]
    def __init__(self, kind: str):
        if kind not in self.KIND_VALUES:
            raise Exception


Test("hello")