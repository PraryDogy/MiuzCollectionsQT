class Test:
    __slots__ = ["a", "b"]
    def __init__(self):
        self.a = 1
        self.b = 2


c = Test()
print(c.__slots__)