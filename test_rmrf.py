from typing import Literal

class Test:

    def run(self, test: Literal["hello"]):
        ...


Test().run(test="hello")