class Foo:
    __slots__ = ["test", "new_test", "new_item"]

    def __init__(self, test: str, new_test: str, new_item: str):
        self.test = test
        self.new_test = new_test
        self.new_item = new_item


data = [
    {"test": "te", "new_test": "be"}
]


for i in data:
    a = Foo(**i)
