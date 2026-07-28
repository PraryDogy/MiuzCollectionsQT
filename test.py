class JsonData:
    test = 1


class Foo:
    def __init__(self):
        super().__init__()
        self.foo_ = JsonData.test

    def test(self):
        self.foo_ = 2


foo = Foo()
foo.test()

print(JsonData.test)