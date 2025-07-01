class Foo:
    def __init__(self):
        super().__init__()
        self.test = [1, 2, 3]


abc = [Foo(), Foo()]

cba = abc.copy()
cba[0].test = [666]


for i in abc:
    print(i.test)